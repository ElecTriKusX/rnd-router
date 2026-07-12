"""Интерфейсы для замены внешних сервисов в тестах без сетевых вызовов."""

from typing import Protocol

from domain.models import CandidateMatch, EmailDraft, MatchResponse, ResearchRequest


class MatchingService(Protocol):
    def match(self, request: ResearchRequest, top_n: int) -> MatchResponse:
        """Возвращает ранжированных исследователей для всех выделенных подзадач."""


class RouterService(MatchingService, Protocol):
    def create_email_draft(self, request: ResearchRequest, candidate: CandidateMatch) -> EmailDraft:
        """Создаёт черновик письма для выбранного кандидата."""
