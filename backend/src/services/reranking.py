"""LLM-переранжирование кандидатов, найденных векторным поиском."""

from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from domain.models import CandidateMatch, Profile, Subtask
from infrastructure.json_response import LLMResponseError, parse_json_object
from infrastructure.prompts import read_prompt


class ChatClient(Protocol):
    def chat(self, prompt: str, temperature: float | None = None) -> str:
        """Возвращает текстовый ответ LLM."""


class _RankedProfile(BaseModel):
    profile_id: str
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=1)


class _RerankingPayload(BaseModel):
    top: list[_RankedProfile]


class RerankingError(RuntimeError):
    """LLM вернула непригодный рейтинг кандидатов."""


def _format_candidate(profile: Profile) -> str:
    """Передаёт модели только данные, на которые можно опирать объяснение выбора."""
    publications = "; ".join(item.title for item in profile.publications[:5]) or "нет"
    grants = "; ".join(item.title for item in profile.grants[:5]) or "нет"
    return (
        f"ID: {profile.id}\n"
        f"ФИО: {profile.full_name}\n"
        f"Подразделение: {profile.unit}\n"
        f"Должность: {profile.position or 'не указана'}\n"
        f"Учёная степень: {profile.degree or 'нет'}\n"
        f"Публикации: {publications}\n"
        f"Гранты: {grants}"
    )


def rerank_candidates(
    llm: ChatClient,
    subtask: Subtask,
    candidates: list[Profile],
    top_n: int,
    prompt_version: int = 2,
) -> list[CandidateMatch]:
    """Выбирает top_n и связывает ответ LLM с исходными профилями по id."""
    if not candidates:
        return []

    profiles_by_id = {profile.id: profile for profile in candidates}
    candidates_text = "\n\n".join(
        f"Кандидат {number}:\n{_format_candidate(profile)}"
        for number, profile in enumerate(candidates, start=1)
    )
    prompt = read_prompt(f"rerank_v{prompt_version}")
    prompt = prompt.replace("{subtask_description}", f"Тема: {subtask.topic}\nКлючевые слова: {', '.join(subtask.keywords)}")
    prompt = prompt.replace("{candidates}", candidates_text).replace("{top_n}", str(top_n))

    for _ in range(2):
        try:
            payload = _RerankingPayload.model_validate(parse_json_object(llm.chat(prompt)))
            result = [
                CandidateMatch(profile=profiles_by_id[item.profile_id], score=item.score, reasons=item.reasons)
                for item in payload.top[:top_n]
            ]
            if len({item.profile.id for item in result}) != len(result):
                raise RerankingError("LLM вернула одного кандидата несколько раз")
            return result
        except (KeyError, LLMResponseError, ValidationError):
            continue
    raise RerankingError("Не удалось получить валидный рейтинг кандидатов")
