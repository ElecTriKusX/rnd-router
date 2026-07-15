from domain.models import CandidateMatch, Profile, ResearchRequest
from services.router import RNDService


class FakeLLM:
    """Имитирует последовательные ответы LLM, не обращаясь к Yandex."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = iter(responses)

    def chat(self, prompt: str, temperature: float | None = None) -> str:
        del prompt, temperature
        return next(self._responses)


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
