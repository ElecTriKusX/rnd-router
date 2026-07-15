"""Сквозной сценарий: декомпозиция, поиск, rerank и генерация письма."""

from collections.abc import Callable

from domain.models import CandidateMatch, EmailDraft, MatchResponse, ResearchRequest, SubtaskMatches, DecomposeResponce
from infrastructure.retrieval import VectorRetriever
from infrastructure.yandex_llm import LLM
from services.decomposition import decompose_request
from services.email_drafting import draft_email
from services.describe import describe_candidate


class RNDService:
    """Соединяет domain-сценарии с адаптерами Yandex и локального индекса."""

    def __init__(
        self,
        llm_factory: Callable[[], LLM] = LLM,
        retriever_factory: Callable[[LLM], VectorRetriever] = VectorRetriever,
    ) -> None:
        self._llm_factory = llm_factory
        self._retriever_factory = retriever_factory

    def decompose(self, request: ResearchRequest) -> DecomposeResponce:
        """Разбивает входящий запрос на подзадачи."""
        llm = self._llm_factory()
        return DecomposeResponce(subtasks=decompose_request(llm, request))

    def match(self, request: ResearchRequest, decompose: DecomposeResponce) -> MatchResponse:
        """Находит и объясняет кандидатов для каждой подзадачи входящего запроса."""
        llm = self._llm_factory()
        retriever = self._retriever_factory(llm)
        results: list[SubtaskMatches] = []

        subtask_profiles = {}
        all_profiles = {}
        scores = {}

        for subtask in decompose.subtasks:
            profiles_and_scores = retriever.retrieve(f"{request.text} {subtask.topic}", k=5)
            subtask_profiles[subtask.id] = []
            for profile, score in profiles_and_scores:
                subtask_profiles[subtask.id].append(profile)
                if profile.id not in all_profiles:
                    all_profiles[profile.id] = profile
                    scores[profile.id] = score
                if score > scores[profile.id]:
                    scores[profile.id] = score

        candidates = {}
        for profile_id in all_profiles.keys():
            profile = all_profiles[profile_id]
            reasons = describe_candidate(llm, request, profile)
            score = scores[profile.id]
            candidates[profile.id] = CandidateMatch(profile=profile, score=score, reasons=reasons)
        
        for subtask in decompose.subtasks:
            subtask_candidates = [candidates[profile.id] for profile in subtask_profiles[subtask.id]]
            results.append(SubtaskMatches(subtask=subtask, candidates=subtask_candidates))

        return MatchResponse(request=request, results=results)

    def create_email_draft(self, request: ResearchRequest, candidate: CandidateMatch) -> EmailDraft:
        """Создаёт одно письмо после явного действия менеджера в интерфейсе."""
        return draft_email(self._llm_factory(), request, candidate)
