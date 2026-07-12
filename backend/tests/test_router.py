from domain.models import CandidateMatch, Profile, ResearchRequest
from services.router import RNDService


class FakeLLM:
    """Имитирует последовательные ответы LLM, не обращаясь к Yandex."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = iter(responses)

    def chat(self, prompt: str, temperature: float | None = None) -> str:
        del prompt, temperature
        return next(self._responses)


class FakeRetriever:
    """Возвращает известный профиль вместо чтения parquet-индекса."""

    def __init__(self, profiles: list[Profile]) -> None:
        self._profiles = profiles

    def retrieve(self, query: str, k: int = 20) -> list[Profile]:
        del query
        return self._profiles[:k]


def test_router_connects_decomposition_retrieval_and_reranking() -> None:
    llm = FakeLLM(
        [
            '{"subtasks": [{"id": 1, "topic": "Катализ", "keywords": ["полимер"]}]}',
            '{"top": [{"profile_id": "p1", "score": 0.92, "reasons": ["Есть публикация по катализу"]}]}',
        ]
    )
    profile = Profile(id="p1", full_name="Иванов Иван", email="ivanov@example.test")
    service = RNDService(
        llm_factory=lambda: llm,
        retriever_factory=lambda _: FakeRetriever([profile]),
    )

    response = service.match(ResearchRequest(title="Полимер", description="Нужен катализ"), top_n=5)

    assert response.results[0].subtask.topic == "Катализ"
    assert response.results[0].candidates[0].profile.id == "p1"
    assert response.results[0].candidates[0].reasons == ["Есть публикация по катализу"]


def test_router_generates_email_only_for_selected_candidate() -> None:
    llm = FakeLLM(['{"to": "ivanov@example.test", "subject": "Приглашение", "body": "Здравствуйте"}'])
    profile = Profile(id="p1", full_name="Иванов Иван", email="ivanov@example.test")
    service = RNDService(llm_factory=lambda: llm)
    request = ResearchRequest(title="Полимер", description="Нужен катализ")

    draft = service.create_email_draft(
        request,
        CandidateMatch(profile=profile, score=0.92, reasons=["Есть публикация"]),
    )

    assert draft.subject == "Приглашение"
