import pytest
from fastapi.testclient import TestClient

from api.app import app, get_router_service
from domain.models import (
    CandidateMatch,
    EmailDraft,
    MatchResponse,
    Profile,
    ResearchRequest,
    Subtask,
    SubtaskMatches,
)


class StubMatchingService:
    """Предсказуемая замена Yandex и векторного индекса для API-тестов."""

    def match(self, request: ResearchRequest, top_n: int) -> MatchResponse:
        candidate = CandidateMatch(
            profile=Profile(id="p1", full_name="Иванов Иван", email="ivanov@example.test"),
            score=0.91,
            reasons=["Есть публикация по теме запроса"],
        )
        return MatchResponse(
            request=request,
            results=[
                SubtaskMatches(
                    subtask=Subtask(id=1, topic="Катализ", keywords=["катализ"]),
                    candidates=[candidate][:top_n],
                )
            ],
        )

    def create_email_draft(self, request: ResearchRequest, candidate: CandidateMatch) -> EmailDraft:
        return EmailDraft(to=candidate.profile.email, subject="Приглашение", body=request.description)


@pytest.fixture
def configured_client() -> TestClient:
    app.dependency_overrides[get_router_service] = StubMatchingService
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_match_endpoint_returns_frontend_contract(configured_client: TestClient) -> None:
    response = configured_client.post(
        "/api/v1/matches",
        json={
            "request": {
                "title": "Новый полимер",
                "description": "Нужен исследователь по катализу.",
            },
            "top_n": 5,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["candidates"][0]["profile"]["id"] == "p1"
    assert body["results"][0]["candidates"][0]["score"] == 0.91


def test_match_endpoint_validates_client_input(configured_client: TestClient) -> None:
    response = configured_client.post("/api/v1/matches", json={"request": {"title": "", "description": "x"}})

    assert response.status_code == 422


def test_match_endpoint_reports_unconfigured_service() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/matches",
        json={"request": {"title": "Тема", "description": "Описание"}},
    )

    assert response.status_code == 503


def test_email_draft_endpoint_returns_draft(configured_client: TestClient) -> None:
    response = configured_client.post(
        "/api/v1/email-drafts",
        json={
            "request": {"title": "Тема", "description": "Описание"},
            "candidate": {
                "profile": {"id": "p1", "full_name": "Иванов Иван", "email": "ivanov@example.test"},
                "score": 0.91,
                "reasons": ["Есть профильная публикация"],
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["to"] == "ivanov@example.test"
