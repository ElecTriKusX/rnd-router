"""Точка входа FastAPI: бизнес-зависимости передаются явно, а не создаются глобально."""

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from domain.models import CandidateMatch, EmailDraft, MatchResponse, ResearchRequest
from services.router import RNDService
from services.ports import RouterService


class MatchCommand(BaseModel):
    request: ResearchRequest
    top_n: int = Field(default=5, ge=1, le=20)


class EmailDraftCommand(BaseModel):
    request: ResearchRequest
    candidate: CandidateMatch


def get_router_service() -> RouterService:
    """Возвращает сервис без раннего обращения к данным, ключам или Yandex."""
    return RNDService()


def create_app() -> FastAPI:
    app = FastAPI(
        title="R&D Router API",
        version="0.1.0",
        description="API contract for researcher matching and invitation drafting.",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/api/v1/matches",
        response_model=MatchResponse,
        status_code=status.HTTP_200_OK,
    )
    def match_researchers(
        command: MatchCommand,
        service: RouterService = Depends(get_router_service),
    ) -> MatchResponse:
        try:
            return service.match(command.request, command.top_n)
        except (RuntimeError, EnvironmentError, FileNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error

    @app.post("/api/v1/email-drafts", response_model=EmailDraft, status_code=status.HTTP_200_OK)
    def create_email_draft(
        command: EmailDraftCommand,
        service: RouterService = Depends(get_router_service),
    ) -> EmailDraft:
        try:
            return service.create_email_draft(command.request, command.candidate)
        except (RuntimeError, EnvironmentError, FileNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error

    return app


app = create_app()
