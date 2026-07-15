"""Точка входа FastAPI: бизнес-зависимости передаются явно, а не создаются глобально."""

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from domain.models import CandidateMatch, EmailDraft, MatchResponse, ResearchRequest, DecomposeResponce
from services.router import RNDService
from services.ports import RouterService


class MatchCommand(BaseModel):
    request: ResearchRequest
    decompose: DecomposeResponce


class DecomposeCommand(BaseModel):
    request: ResearchRequest

class EmailDraftCommand(BaseModel):
    request: ResearchRequest
    candidate: CandidateMatch
    facts: list[str] = Field(default_factory=list)
    instruction: str = ""


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
        "/api/v1/decompose",
        response_model=DecomposeResponce,
        status_code=status.HTTP_200_OK,
    )
    def decompose_grant(
        command: DecomposeCommand,
        service: RouterService = Depends(get_router_service),
    ) -> DecomposeResponce:
        try:
            return service.decompose(command.request)
        except (RuntimeError, EnvironmentError, FileNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error

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
            return service.match(command.request, command.decompose)
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
            context = []
            if command.facts:
                context.append("Факты, которые нужно использовать в письме:\n" + "\n".join(f"- {fact}" for fact in command.facts))
            if command.instruction.strip():
                context.append("Дополнительная инструкция для письма:\n" + command.instruction.strip())
            request = command.request
            if context:
                request = ResearchRequest(
                    title=request.title,
                    description=f"{request.description}\n\n" + "\n\n".join(context),
                )
            return service.create_email_draft(request, command.candidate)
        except (RuntimeError, EnvironmentError, FileNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error

    return app


app = create_app()
