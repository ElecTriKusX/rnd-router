"""Interfaces that let tests replace external services without network calls."""

from typing import Protocol

from domain.models import MatchResponse, ResearchRequest


class MatchingService(Protocol):
    def match(self, request: ResearchRequest, top_n: int) -> MatchResponse:
        """Return ranked researchers for every derived subtask."""
