import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from infrastructure.yandex_llm import LLM

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"

PROFILES_PATH = DATA_DIR / "profiles.json"
INDEX_PATH = DATA_DIR / "index.parquet"

EMBEDDING_DIM = 256

# У Yandex embeddings hard limit = 2048 токенов.
CHUNK_TOKEN_LIMIT = int(
    os.getenv("EMBED_CHUNK_TOKEN_LIMIT", "2000")
)

# Сколько embedding-запросов выполнять параллельно.
EMBED_BATCH_SIZE = int(
    os.getenv("EMBED_BATCH_SIZE", "8")
)


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    token_count: int


@dataclass(frozen=True, slots=True)
class ChunkTask:
    profile_index: int
    text: str
    token_count: int


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _format_items(
    items: Iterable[dict[str, Any]],
) -> str:
    blocks: list[str] = []

    for item in items:
        title = _clean(item.get("title"))
        annotation = _clean(item.get("annotation"))

        if title and annotation:
            blocks.append(f"{title}\n{annotation}")
        elif title:
            blocks.append(title)
        elif annotation:
            blocks.append(annotation)

    return "\n\n".join(blocks)


def build_raw_text(
    profile: dict[str, Any],
) -> str:
    publications = _format_items(
        profile.get("publications") or []
    )

    grants = _format_items(
        profile.get("grants") or []
    )

    return (
        f"{_clean(profile.get('full_name'))}\n"
        f"{_clean(profile.get('unit'))}\n"
        f"{_clean(profile.get('position'))}\n\n"
        f"Публикации:\n"
        f"{publications}\n\n"
        f"Гранты:\n"
        f"{grants}"
    ).strip()


def _load_profiles(
    path: Path,
) -> list[dict[str, Any]]:
    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(data, list):
        raise ValueError(
            f"{path} должен содержать json"
        )

    return data


def _make_token_counter(llm: LLM):
    """
    Yandex SDK даёт tokenize() у completion-модели.
    """
    tokenizer_model = llm.sdk.models.completions(
        llm.chat_model_name
    )

    def count_tokens(text: str) -> int:
        if not text:
            return 0

        tokens = tokenizer_model.tokenize(
            text,
            timeout=llm.timeout_embedding,
        )

        return len(tokens)

    return count_tokens


def _find_largest_prefix(
    text: str,
    max_tokens: int,
    count_tokens,
) -> int:
    """
    Бинарным поиском находит максимальный префикс строки,
    который помещается в max_tokens.

    Возвращает позицию символа для разрезания.
    """
    low = 1
    high = len(text)
    best = 1

    while low <= high:
        middle = (low + high) // 2

        candidate = text[:middle]
        token_count = count_tokens(candidate)

        if token_count <= max_tokens:
            best = middle
            low = middle + 1
        else:
            high = middle - 1

    # Желательно не резать слово посередине.
    # Ищем хороший разделитель недалеко от найденной границы.
    search_from = max(
        0,
        int(best * 0.8),
    )

    separators = [
        "\n\n",
        "\n",
        ". ",
        "; ",
        ", ",
        " ",
    ]

    best_separator = -1
    separator_length = 0

    for separator in separators:
        position = text.rfind(
            separator,
            search_from,
            best,
        )

        if position > best_separator:
            best_separator = position
            separator_length = len(separator)

    if best_separator > 0:
        return best_separator + separator_length

    return best


def split_text_by_tokens(
    text: str,
    count_tokens,
    max_tokens: int = CHUNK_TOKEN_LIMIT,
) -> list[Chunk]:
    """
    Разбивает текст на чанки не длиннее max_tokens.

    Сначала пытаемся сохранить крупные куски текста,
    а если кусок слишком большой — находим максимальный
    допустимый префикс.
    """
    text = text.strip()

    if not text:
        return []

    total_tokens = count_tokens(text)

    if total_tokens <= max_tokens:
        return [
            Chunk(
                text=text,
                token_count=total_tokens,
            )
        ]

    chunks: list[Chunk] = []
    remaining = text

    while remaining:
        remaining = remaining.strip()

        if not remaining:
            break

        token_count = count_tokens(remaining)

        if token_count <= max_tokens:
            chunks.append(
                Chunk(
                    text=remaining,
                    token_count=token_count,
                )
            )
            break

        cut_position = _find_largest_prefix(
            text=remaining,
            max_tokens=max_tokens,
            count_tokens=count_tokens,
        )

        chunk_text = remaining[
            :cut_position
        ].strip()

        if not chunk_text:
            raise RuntimeError(
                "Ошибка разделения текста на чанки"
            )

        chunk_token_count = count_tokens(
            chunk_text
        )

        if chunk_token_count > max_tokens:
            raise RuntimeError(
                f"Чанк слишком большой: "
                f"{chunk_token_count} токенов"
            )

        chunks.append(
            Chunk(
                text=chunk_text,
                token_count=chunk_token_count,
            )
        )

        remaining = remaining[
            cut_position:
        ]

    return chunks


def _prepare_chunk_tasks(
    raw_texts: list[str],
    count_tokens,
) -> list[ChunkTask]:
    """
    Разбивает все профили на чанки.

    Затем все чанки всех профилей можно отправить
    на embedding одним общим потоком батчей.
    """
    tasks: list[ChunkTask] = []

    for profile_index, raw_text in enumerate(
        raw_texts
    ):
        chunks = split_text_by_tokens(
            text=raw_text,
            count_tokens=count_tokens,
        )

        logger.info(
            "Профиль %d: %d чанков, токенов=%s",
            profile_index,
            len(chunks),
            [
                chunk.token_count
                for chunk in chunks
            ],
        )

        for chunk in chunks:
            tasks.append(
                ChunkTask(
                    profile_index=profile_index,
                    text=chunk.text,
                    token_count=chunk.token_count,
                )
            )

    return tasks


def _embed_chunks(
    llm: LLM,
    tasks: list[ChunkTask],
    batch_size: int,
) -> list[np.ndarray]:
    """
    Считает embeddings чанков ограниченными
    параллельными батчами.

    Порядок результатов соответствует порядку tasks.
    """
    if batch_size <= 0:
        raise ValueError(
            "размер батча должен быть > 0"
        )

    embed_doc = partial(
        llm.embed,
        kind="doc",
    )

    vectors: list[np.ndarray] = []

    with ThreadPoolExecutor(
        max_workers=batch_size
    ) as pool:
        for start in range(
            0,
            len(tasks),
            batch_size,
        ):
            batch = tasks[
                start:start + batch_size
            ]

            logger.info(
                "Эмбединг чанков %d..%d из %d",
                start + 1,
                start + len(batch),
                len(tasks),
            )

            batch_texts = [
                task.text
                for task in batch
            ]

            batch_embeddings = pool.map(
                embed_doc,
                batch_texts,
            )

            for raw_vector in batch_embeddings:
                vector = np.asarray(
                    raw_vector,
                    dtype=np.float32,
                )

                if vector.shape != (
                    EMBEDDING_DIM,
                ):
                    raise ValueError(
                        f"Ожидалось "
                        f"{EMBEDDING_DIM}-dim "
                        f"embedding, найдено "
                        f"{vector.shape}"
                    )

                if not np.isfinite(
                    vector
                ).all():
                    raise ValueError(
                        "Эмбединг содержит "
                        "NaN or inf"
                    )

                vectors.append(vector)

    return vectors


def _aggregate_profile_vectors(
    profile_count: int,
    tasks: list[ChunkTask],
    chunk_vectors: list[np.ndarray],
) -> list[np.ndarray]:
    """
    Собирает один embedding на профиль.

    Используем weighted mean:
        sum(vector_i * token_count_i)
        --------------------------------
        sum(token_count_i)

    После этого L2-нормализация.
    """
    if len(tasks) != len(chunk_vectors):
        raise ValueError(
            "задачи и векторы фрагментов "
            "имеют разную длину"
        )

    vectors_by_profile: list[
        list[np.ndarray]
    ] = [
        []
        for _ in range(profile_count)
    ]

    weights_by_profile: list[
        list[int]
    ] = [
        []
        for _ in range(profile_count)
    ]

    for task, vector in zip(
        tasks,
        chunk_vectors,
        strict=True,
    ):
        vectors_by_profile[
            task.profile_index
        ].append(vector)

        weights_by_profile[
            task.profile_index
        ].append(task.token_count)

    result: list[np.ndarray] = []

    for profile_index in range(
        profile_count
    ):
        vectors = vectors_by_profile[
            profile_index
        ]

        weights = weights_by_profile[
            profile_index
        ]

        if not vectors:
            raise ValueError(
                f"Профиль {profile_index} "
                f"не имеет эмбединг чанков"
            )

        matrix = np.stack(
            vectors,
            axis=0,
        )

        # Маленький последний чанк не должен иметь
        # такой же вес, как полный чанк на 2000 токенов.
        pooled = np.average(
            matrix,
            axis=0,
            weights=np.asarray(
                weights,
                dtype=np.float32,
            ),
        ).astype(
            np.float32
        )

        # Для cosine similarity удобно сохранить
        # уже нормализованный вектор.
        norm = np.linalg.norm(
            pooled
        )

        if norm == 0:
            raise ValueError(
                f"Профиль {profile_index} "
                f"получился с zero-norm embedding"
            )

        pooled /= norm

        result.append(pooled)

    return result


def build_index(
    profiles_path: Path = PROFILES_PATH,
    index_path: Path = INDEX_PATH,
    batch_size: int = EMBED_BATCH_SIZE,
) -> Path:
    profiles = _load_profiles(
        profiles_path
    )

    if not profiles:
        raise ValueError(
            f"Нет профилей в "
            f"{profiles_path}"
        )

    raw_texts = [
        build_raw_text(profile)
        for profile in profiles
    ]

    llm = LLM()

    # Tokenizer создаётся один раз.
    count_tokens = _make_token_counter(
        llm
    )

    # 1. Разбиваем все профили на чанки.
    tasks = _prepare_chunk_tasks(
        raw_texts=raw_texts,
        count_tokens=count_tokens,
    )

    logger.info(
        "Подготовлено %d embedding chunks "
        "для %d профилей",
        len(tasks),
        len(profiles),
    )

    # 2. Считаем embeddings для всех чанков.
    chunk_vectors = _embed_chunks(
        llm=llm,
        tasks=tasks,
        batch_size=batch_size,
    )

    # 3. Усредняем чанки обратно
    #    в один 256-dim вектор на профиль.
    profile_vectors = (
        _aggregate_profile_vectors(
            profile_count=len(profiles),
            tasks=tasks,
            chunk_vectors=chunk_vectors,
        )
    )

    index_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    table = pa.table(
        {
            "id": [
                _clean(
                    profile.get("id")
                )
                for profile in profiles
            ],
            "full_name": [
                _clean(
                    profile.get(
                        "full_name"
                    )
                )
                for profile in profiles
            ],
            "unit": [
                _clean(
                    profile.get("unit")
                )
                for profile in profiles
            ],
            "vector": pa.array(
                [
                    vector.tolist()
                    for vector
                    in profile_vectors
                ],
                type=pa.list_(
                    pa.float32(),
                    EMBEDDING_DIM,
                ),
            ),
        }
    )

    pq.write_table(
        table,
        index_path,
    )

    logger.info(
        "Сохранено %d профилей в %s",
        len(profiles),
        index_path,
    )

    return index_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO
    )

    build_index()
