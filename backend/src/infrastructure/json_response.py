"""Проверка JSON-ответов LLM перед передачей их в доменные модели."""

import json
from typing import Any


class LLMResponseError(ValueError):
    """LLM вернула текст, из которого нельзя получить JSON-объект."""


def parse_json_object(text: str) -> dict[str, Any]:
    """Извлекает JSON-объект даже если модель случайно добавила обрамляющий текст."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start > end:
        raise LLMResponseError("В ответе LLM не найден JSON-объект")

    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise LLMResponseError("LLM вернула невалидный JSON") from error

    if not isinstance(value, dict):
        raise LLMResponseError("LLM должна вернуть JSON-объект")
    return value
