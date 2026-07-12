"""Точка входа FastAPI: бизнес-зависимости передаются явно, а не создаются глобально."""

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from domain.models import MatchResponse, ResearchRequest
from services.ports import MatchingService


class MatchCommand(BaseModel):
    request: ResearchRequest
    top_n: int = Field(default=5, ge=1, le=20)


class UnconfiguredMatchingService:
    """Безопасная заглушка до подключения реального индекса и LLM."""

    def match(self, request: ResearchRequest, top_n: int) -> MatchResponse:
        del request, top_n
        raise RuntimeError("Сервис подбора пока не подключён")


def get_matching_service() -> MatchingService:
    """Точка, где появится подключение production-сервиса после поставки индекса."""
    return UnconfiguredMatchingService()


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
        service: MatchingService = Depends(get_matching_service),
    ) -> MatchResponse:
        try:
            return service.match(command.request, command.top_n)
        except RuntimeError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error

    return app


app = create_app()
