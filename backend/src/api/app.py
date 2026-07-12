"""FastAPI entry point. Business dependencies are injected, never global."""

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from domain.models import MatchResponse, ResearchRequest
from services.ports import MatchingService


class MatchCommand(BaseModel):
    request: ResearchRequest
    top_n: int = Field(default=5, ge=1, le=20)


class UnconfiguredMatchingService:
    """Safe default until the real vector index and LLM are wired."""

    def match(self, request: ResearchRequest, top_n: int) -> MatchResponse:
        del request, top_n
        raise RuntimeError("Matching service is not configured")


def get_matching_service() -> MatchingService:
    """Production wiring is added only after the real index is delivered."""
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
