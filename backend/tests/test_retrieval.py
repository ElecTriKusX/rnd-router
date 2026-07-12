import json

import pyarrow as pa
import pyarrow.parquet as pq

from infrastructure.retrieval import VectorRetriever


class FakeEmbeddingClient:
    """Возвращает заданный вектор вместо обращения к Yandex Embeddings."""

    def embed(self, text: str, kind: str = "doc") -> list[float]:
        assert text == "катализ"
        assert kind == "query"
        return [1.0] + [0.0] * 255


def test_vector_retriever_returns_nearest_profile(tmp_path) -> None:
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(
        json.dumps(
            [
                {"id": "p1", "full_name": "Иванов Иван"},
                {"id": "p2", "full_name": "Петров Пётр"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    index_path = tmp_path / "index.parquet"
    pq.write_table(
        pa.table(
            {
                "id": ["p1", "p2"],
                "vector": [[1.0] + [0.0] * 255, [0.0, 1.0] + [0.0] * 254],
            }
        ),
        index_path,
    )

    retriever = VectorRetriever(FakeEmbeddingClient(), profiles_path=profiles_path, index_path=index_path)

    result = retriever.retrieve("катализ", k=1)

    assert [profile.id for profile in result] == ["p1"]
