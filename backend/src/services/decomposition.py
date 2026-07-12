"""Декомпозиция входящего R&D-запроса на отдельные подзадачи."""

from typing import Protocol

from pydantic import BaseModel, ValidationError

from domain.models import ResearchRequest, Subtask
from infrastructure.json_response import LLMResponseError, parse_json_object
from infrastructure.prompts import read_prompt


class ChatClient(Protocol):
    def chat(self, prompt: str, temperature: float | None = None) -> str:
        """Возвращает текстовый ответ LLM."""


class _DecompositionPayload(BaseModel):
    subtasks: list[Subtask]


class DecompositionError(RuntimeError):
    """LLM не смогла вернуть пригодную декомпозицию после повторной попытки."""


def decompose_request(llm: ChatClient, request: ResearchRequest, prompt_version: int = 2) -> list[Subtask]:
    """Подставляет запрос в prompt и валидирует структурированный результат LLM."""
    prompt = read_prompt(f"decompose_v{prompt_version}").replace("{grant_description}", request.text)
    for _ in range(2):
        try:
            payload = _DecompositionPayload.model_validate(parse_json_object(llm.chat(prompt)))
            if payload.subtasks:
                return payload.subtasks
        except (LLMResponseError, ValidationError):
            continue
    raise DecompositionError("Не удалось получить валидную декомпозицию запроса")
