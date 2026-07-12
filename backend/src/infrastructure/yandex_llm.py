"""Адаптер Yandex AI Studio к минимальному интерфейсу LLM приложения."""

import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from yandex_ai_studio_sdk import AIStudio
from yandex_ai_studio_sdk.auth import APIKeyAuth

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class LLM:
    """Клиент YandexGPT; создаётся только при реальном запросе пользователя."""

    def __init__(self) -> None:
        # Ключи лежат в корневом .env, чтобы их не дублировать между backend и frontend.
        load_dotenv(PROJECT_ROOT / ".env")
        folder_id = os.getenv("LLM_FOLDER_ID")
        api_key = os.getenv("LLM_API_KEY")
        if not folder_id or not api_key:
            raise EnvironmentError("Не заданы LLM_FOLDER_ID и LLM_API_KEY")

        self.chat_model_name = os.getenv("LLM_CHAT_MODEL", "yandexgpt")
        self.embed_model_name = os.getenv("LLM_EMBEDDING_MODEL", "yandexgpt-embeddings")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.timeout_completion = int(os.getenv("LLM_TIMEOUT_COMPLETION", os.getenv("LLM_COMPLETION_TIMEOUT", "60")))
        self.timeout_embedding = int(os.getenv("LLM_TIMEOUT_EMBEDDING", os.getenv("LLM_EMBEDDING_TIMEOUT", "30")))
        self.sdk = AIStudio(folder_id=folder_id, auth=APIKeyAuth(api_key))

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def chat(self, prompt: str, temperature: float | None = None) -> str:
        """Запрашивает completion и повторяет временно неуспешный вызов до трёх раз."""
        model = self.sdk.models.completions(self.chat_model_name).configure(
            temperature=self.temperature if temperature is None else temperature
        )
        alternatives = model.run(prompt, timeout=self.timeout_completion)
        if not alternatives:
            raise RuntimeError("YandexGPT вернул пустой ответ")
        return alternatives[0].text

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def embed(self, text: str, kind: Literal["doc", "query"] = "doc") -> list[float]:
        """Возвращает embedding документа или поискового запроса."""
        model = self.sdk.models.text_embeddings(f"{self.embed_model_name}-{kind}")
        return list(model.run(text, timeout=self.timeout_embedding).embedding)
