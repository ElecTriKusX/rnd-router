"""Векторный поиск профилей по локальному parquet-индексу."""

from pathlib import Path
from typing import Protocol

import numpy as np
import pyarrow.parquet as pq

from domain.models import Profile
from infrastructure.profile_repository import DEFAULT_PROFILES_PATH, load_profiles


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INDEX_PATH = PROJECT_ROOT / "data" / "index.parquet"
EMBEDDING_DIMENSION = 256


class EmbeddingClient(Protocol):
    def embed(self, text: str, kind: str = "doc") -> list[float]:
        """Создаёт embedding текста."""


class VectorRetriever:
    """Получает кандидатов через косинусное сходство, без отдельной векторной БД."""

    def __init__(
        self,
        llm: EmbeddingClient,
        profiles_path: Path = DEFAULT_PROFILES_PATH,
        index_path: Path = DEFAULT_INDEX_PATH,
    ) -> None:
        self._llm = llm
        self._profiles_path = profiles_path
        self._index_path = index_path

    def retrieve(self, query: str, k: int = 10) -> list[tuple[Profile, float]]:
        """Возвращает не более k профилей, наиболее близких к запросу."""
        if not query.strip():
            raise ValueError("Поисковый запрос не может быть пустым")
        if k <= 0:
            return []
        if not self._index_path.exists():
            raise FileNotFoundError(f"Не найден индекс: {self._index_path}")

        table = pq.read_table(self._index_path, columns=["id", "vector"])
        ids = [str(value) for value in table["id"].to_pylist()]
        vectors = np.asarray(table["vector"].to_pylist(), dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[1] != EMBEDDING_DIMENSION:
            raise ValueError("Индекс должен содержать векторы размерности 256")

        query_vector = np.asarray(self._llm.embed(query, kind="query"), dtype=np.float32)
        if query_vector.shape != (EMBEDDING_DIMENSION,):
            raise ValueError("Embedding поискового запроса должен иметь размерность 256")
        if not np.isfinite(query_vector).all():
            raise ValueError("Embedding поискового запроса содержит некорректные значения")

        vector_norms = np.linalg.norm(vectors, axis=1)
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0 or np.any(vector_norms == 0):
            raise ValueError("В индексе или запросе найден вектор нулевой длины")

        scores = (vectors / vector_norms[:, None]) @ (query_vector / query_norm)
        order = np.argsort(-scores, kind="stable")[: min(k, len(ids))]

        MAX_SCORE = max(0.4, max(scores))
        MIN_SCORE = min(0.0, min(scores))
        THRESHOLD = 0.005

        norm = lambda x: (x-MIN_SCORE)/(MAX_SCORE-MIN_SCORE)
        
        profiles = load_profiles(self._profiles_path)

        candidates = [(profiles[ids[idx]], norm(scores[idx])) for idx in order]
        results = []
        for i in range(len(candidates)-1):
            p1, s1 = candidates[i]
            p2, s2 = candidates[i+1]
            if abs(s1-s2) >= THRESHOLD:
                results.append((p1, s1))

        return results
