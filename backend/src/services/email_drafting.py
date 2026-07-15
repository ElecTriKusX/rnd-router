"""Генерация персонализированного письма только по запросу пользователя."""

from typing import Protocol

from pydantic import ValidationError

from domain.models import CandidateMatch, EmailDraft, ResearchRequest
from infrastructure.json_response import LLMResponseError, parse_json_object
from infrastructure.prompts import read_prompt


class ChatClient(Protocol):
    def chat(self, prompt: str, temperature: float | None = None) -> str:
        """Возвращает текстовый ответ LLM."""


class EmailDraftingError(RuntimeError):
    """Письмо нельзя сформировать из-за неполных данных или ответа LLM."""


def draft_email(
    llm: ChatClient,
    request: ResearchRequest,
    candidate: CandidateMatch,
    prompt_version: int = 2,
) -> EmailDraft:
    """Генерирует письмо для одного выбранного кандидата, а не для всего списка."""
    profile = candidate.profile
    candidate_info = (
        f"ФИО: {profile.full_name}\n"
        f"Подразделение: {profile.unit}\n"
        f"Должность: {profile.position or 'не указана'}\n"
        f"Учёная степень: {profile.degree or 'нет'}"
    )
    prompt = read_prompt(f"draft_email_v{prompt_version}")
    prompt = prompt.replace("{grant_description}", request.text)
    prompt = prompt.replace("{candidate_info}", candidate_info)
    prompt = prompt.replace("{candidate_email}", profile.email or "не указан")
    prompt = prompt.replace("{reasons}", "\n".join(f"- {reason}" for reason in candidate.reasons))
    if not profile.email:
        prompt += (
            "\n\nВажное уточнение: email кандидата отсутствует. Всё равно подготовь текст письма, "
            "а в поле \"to\" верни null."
        )

    for _ in range(2):
        try:
            draft = EmailDraft.model_validate(parse_json_object(llm.chat(prompt)))
            if profile.email and draft.to != profile.email:
                raise EmailDraftingError("LLM вернула email, не совпадающий с профилем")
            return draft if profile.email else draft.model_copy(update={"to": None})
        except (LLMResponseError, ValidationError):
            continue
    raise EmailDraftingError("Не удалось получить валидный черновик письма")
