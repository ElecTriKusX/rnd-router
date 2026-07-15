import pytest
from fastapi.testclient import TestClient

from api.app import app, get_router_service
from domain.models import (
    CandidateMatch,
    EmailDraft,
    Profile,
    ResearchRequest,
)


class StubMatchingService:
    """Предсказуемая замена Yandex и векторного индекса для API-тестов."""

    def create_email_draft(self, request: ResearchRequest, candidate: CandidateMatch) -> EmailDraft:
        return EmailDraft(to=candidate.profile.email, subject="Приглашение", body=request.description)


@pytest.fixture
def configured_client() -> TestClient:
    app.dependency_overrides[get_router_service] = StubMatchingService
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_match_endpoint_validates_client_input(configured_client: TestClient) -> None:
    response = configured_client.post("/api/v1/matches", json={"request": {"title": "", "description": "x"}})

    assert response.status_code == 422


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
