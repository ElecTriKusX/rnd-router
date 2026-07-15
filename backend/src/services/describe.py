"""LLM-описание кандидатов, найденных векторным поиском."""

from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from domain.models import CandidateMatch, Profile, Subtask, ResearchRequest
from infrastructure.json_response import LLMResponseError, parse_json_object
from infrastructure.prompts import read_prompt
import json

class ChatClient(Protocol):
    def chat(self, prompt: str, temperature: float | None = None) -> str:
        """Возвращает текстовый ответ LLM."""


class DescribeError(RuntimeError):
    """LLM вернула непригодный рейтинг кандидатов."""


class _Reasons(BaseModel):
    reasons: list[str]


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


def describe_candidate(
    llm: ChatClient,
    request: ResearchRequest,
    profile: Profile,
    prompt_version: int = 1,
    max_attempts: int = 2,
) -> list[str]:
    """Описывает обоснование выбора кандидата."""

    candidate_text = f"\nКандидат :\n{_format_candidate(profile)}"
    current_prompt = read_prompt(f"describe_v{prompt_version}")
    current_prompt= current_prompt.replace("{grant_description}", request.text)
    current_prompt = current_prompt.replace("{candidate}", candidate_text)

    last_response = None

    for attempt in range(max_attempts):
        try:
            res = llm.chat(current_prompt, temperature=0.3)
            last_response = res
            js = parse_json_object(res)
            payload = _Reasons.model_validate(js)

            return payload.reasons

        except (json.JSONDecodeError, ValueError) as e:
            error_msg = (
                f"Не удалось распарсить JSON из ответа модели.\n"
                f"Ошибка: {e}\n"
                f"Ответ модели:\n{res}"
            )
            current_prompt = _build_correction_prompt(base_prompt, res, error_msg)
            continue

        except ValidationError as e:
            error_msg = (
                f"Ошибка валидации JSON-структуры.\n"
                f"Детали: {e}\n"
                f"Ответ модели:\n{res}"
            )
            current_prompt = _build_correction_prompt(base_prompt, res, error_msg)
            continue

        except (KeyError, LLMResponseError):
            raise

    raise DescribeError(
        f"Не удалось получить объяснение выбора кандидата за {max_attempts} попыток. "
        f"Последний ответ: {last_response}"
    )


def _build_correction_prompt(original_prompt: str, bad_response: str, error_message: str) -> str:
    """Формирует промпт с просьбой исправить ошибки в предыдущем ответе."""
    return f"""
{original_prompt}

ВНИМАНИЕ: Твой предыдущий ответ был неверным и не прошёл проверку.

Твой предыдущий ответ:
{bad_response}

Ошибка, обнаруженная при проверке:
{error_message}

Пожалуйста, исправь свой ответ так, чтобы он строго соответствовал требованиям формата (только JSON с ключом "top", правильные поля и типы). 
Верни только исправленный JSON, без пояснений и дополнительного текста.
"""