import copy
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from llm import LLM

SRC_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = SRC_DIR / "data"

PROFILES_PATH = DATA_DIR / "profiles.json"
INDEX_PATH = DATA_DIR / "index.parquet"

EMBEDDING_DIM = 256


@dataclass(frozen=True, slots=True)
class Match:
    id: str
    full_name: str
    unit: str
    score: float
    profile: dict[str, Any]


@dataclass(frozen=True, slots=True)
class _Index:
    ids: tuple[str, ...]
    full_names: tuple[str, ...]
    units: tuple[str, ...]
    normalized_vectors: np.ndarray


@lru_cache(maxsize=1)
def _get_llm() -> LLM:
    """
    Не создаём LLM во время импорта:
    импорт retrieve.py не должен сразу требовать переменные окружения.
    """
    return LLM()


@lru_cache(maxsize=4)
def _load_index_cached(
    path_str: str,
    mtime_ns: int,
) -> _Index:
    # mtime_ns нужен для автоматической инвалидизации кеша
    # после пересборки index.parquet.
    del mtime_ns

    table = pq.read_table(
        path_str,
        columns=["id", "full_name", "unit", "vector"],
    )

    ids = tuple(
        str(value)
        for value in table["id"].to_pylist()
    )
    full_names = tuple(
        str(value)
        for value in table["full_name"].to_pylist()
    )
    units = tuple(
        str(value)
        for value in table["unit"].to_pylist()
    )

    vectors = np.asarray(
        table["vector"].to_pylist(),
        dtype=np.float32,
    )

    if vectors.ndim != 2 or vectors.shape[1] != EMBEDDING_DIM:
        raise ValueError(
            f"Ожидался массив векторов индекса размерности "
            f"(N, {EMBEDDING_DIM}), получена размерность {vectors.shape}"
        )

    if len(ids) != vectors.shape[0]:
        raise ValueError(
            "Количество записей метаданных и векторов индекса не совпадает"
        )

    if len(set(ids)) != len(ids):
        raise ValueError(
            "В индексе обнаружены повторяющиеся идентификаторы профилей"
        )

    # Нормализуем один раз при загрузке индекса.
    # После этого косинусное сходство вычисляется скалярным произведением.
    norms = np.linalg.norm(
        vectors,
        axis=1,
        keepdims=True,
    )

    if np.any(norms == 0):
        bad_rows = np.flatnonzero(
            norms[:, 0] == 0
        ).tolist()

        raise ValueError(
            f"В индексе обнаружены векторы с нулевой нормой "
            f"в строках: {bad_rows}"
        )

    normalized_vectors = vectors / norms

    return _Index(
        ids=ids,
        full_names=full_names,
        units=units,
        normalized_vectors=normalized_vectors,
    )


def _load_index(
    path: Path = INDEX_PATH,
) -> _Index:
    stat = path.stat()

    return _load_index_cached(
        str(path),
        stat.st_mtime_ns,
    )


@lru_cache(maxsize=4)
def _load_profiles_cached(
    path_str: str,
    mtime_ns: int,
) -> dict[str, dict[str, Any]]:
    # mtime_ns используется как часть ключа кеша.
    del mtime_ns

    data = json.loads(
        Path(path_str).read_text(encoding="utf-8")
    )

    if not isinstance(data, list):
        raise ValueError(
            f"Файл {path_str} должен содержать JSON-массив профилей"
        )

    by_id: dict[str, dict[str, Any]] = {}

    for profile in data:
        profile_id = str(
            profile.get("id", "")
        ).strip()

        if not profile_id:
            raise ValueError(
                "В profiles.json обнаружен профиль без идентификатора"
            )

        if profile_id in by_id:
            raise ValueError(
                f"В profiles.json обнаружен повторяющийся "
                f"идентификатор профиля: {profile_id}"
            )

        by_id[profile_id] = profile

    return by_id


def _load_profiles(
    path: Path = PROFILES_PATH,
) -> dict[str, dict[str, Any]]:
    stat = path.stat()

    return _load_profiles_cached(
        str(path),
        stat.st_mtime_ns,
    )


def retrieve(
    query: str,
    k: int = 20,
) -> list[Match]:
    query = query.strip()

    if not query:
        raise ValueError("Поисковый запрос не должен быть пустым")

    if k <= 0:
        return []

    index = _load_index()
    profiles = _load_profiles()

    # Критически важно:
    # поисковый запрос кодируем через kind="query".
    query_vector = np.asarray(
        _get_llm().embed(
            query,
            kind="query",
        ),
        dtype=np.float32,
    )

    if query_vector.shape != (EMBEDDING_DIM,):
        raise ValueError(
            f"Ожидался вектор запроса размерности {EMBEDDING_DIM}, "
            f"получена размерность {query_vector.shape}"
        )

    if not np.isfinite(query_vector).all():
        raise ValueError(
            "Вектор запроса содержит NaN или бесконечные значения"
        )

    query_norm = np.linalg.norm(query_vector)

    if query_norm == 0:
        raise ValueError(
            "Вектор запроса имеет нулевую норму"
        )

    normalized_query = (
        query_vector / query_norm
    )

    # Вычисляем косинусное сходство.
    # Векторы индекса уже нормализованы.
    scores = (
        index.normalized_vectors
        @ normalized_query
    )

    top_k = min(k, len(index.ids))

    order = np.argsort(
        -scores,
        kind="stable",
    )[:top_k]

    matches: list[Match] = []

    for row in order:
        profile_id = index.ids[row]

        try:
            profile = profiles[profile_id]
        except KeyError as exc:
            raise KeyError(
                f"Профиль {profile_id!r} присутствует в "
                f"index.parquet, но отсутствует в profiles.json"
            ) from exc

        matches.append(
            Match(
                id=profile_id,
                full_name=index.full_names[row],
                unit=index.units[row],
                score=float(scores[row]),
                profile=copy.deepcopy(profile),
            )
        )

    return matches


if __name__ == "__main__":
    query = (
        "Найти исследователя с именем Чаюн Данил Викторович"
    )

    matches = retrieve(query, k=5)

    for match in matches:
        print(
            f"{match.score:.4f} | "
            f"{match.full_name} | "
            f"{match.unit}"
        )