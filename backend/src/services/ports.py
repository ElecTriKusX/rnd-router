"""Интерфейсы для замены внешних сервисов в тестах без сетевых вызовов."""

from typing import Protocol

from domain.models import MatchResponse, ResearchRequest


class MatchingService(Protocol):
    def match(self, request: ResearchRequest, top_n: int) -> MatchResponse:
        """Возвращает ранжированных исследователей для всех выделенных подзадач."""
