"""Сквозной сценарий: декомпозиция, поиск, rerank и генерация письма."""

from collections.abc import Callable

from domain.models import CandidateMatch, EmailDraft, MatchResponse, ResearchRequest, SubtaskMatches
from infrastructure.retrieval import VectorRetriever
from infrastructure.yandex_llm import LLM
from services.decomposition import decompose_request
from services.email_drafting import draft_email
from services.reranking import rerank_candidates


class RNDService:
    """Соединяет domain-сценарии с адаптерами Yandex и локального индекса."""

    def __init__(
        self,
        llm_factory: Callable[[], LLM] = LLM,
        retriever_factory: Callable[[LLM], VectorRetriever] = VectorRetriever,
    ) -> None:
        self._llm_factory = llm_factory
        self._retriever_factory = retriever_factory

    def match(self, request: ResearchRequest, top_n: int) -> MatchResponse:
        """Находит и объясняет кандидатов для каждой подзадачи входящего запроса."""
        llm = self._llm_factory()
        retriever = self._retriever_factory(llm)
        results: list[SubtaskMatches] = []
        for subtask in decompose_request(llm, request):
            profiles = retriever.retrieve(subtask.topic, k=20)
            candidates = rerank_candidates(llm, subtask, profiles, top_n=top_n)
            results.append(SubtaskMatches(subtask=subtask, candidates=candidates))
        return MatchResponse(request=request, results=results)

    def create_email_draft(self, request: ResearchRequest, candidate: CandidateMatch) -> EmailDraft:
        """Создаёт одно письмо после явного действия менеджера в интерфейсе."""
        return draft_email(self._llm_factory(), request, candidate)
