import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from yandex_ai_studio_sdk import AIStudio
from yandex_ai_studio_sdk.auth import APIKeyAuth
from httpx import HTTPError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_retry_decorator(max_attempts: int):
    def _is_5xx(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            return False
        return 500 <= status_code < 600

    return retry(
        retry=retry_if_exception_type(HTTPError),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry_error_callback=lambda rs: logger.error(
            f"All retries exhausted after {rs.attempt_number} attempts: {rs.outcome.exception()}"
        ),
        before_sleep=lambda rs: logger.warning(
            f"Retry {rs.attempt_number}/{max_attempts} after error: {rs.outcome.exception()}"
        ),
    )


class LLM:
    def __init__(self):
        folder_id = os.getenv("LLM_FOLDER_ID")
        api_key = os.getenv("LLM_API_KEY")

        if not folder_id:
            raise EnvironmentError("LLM_FOLDER_ID not set")
        if not api_key:
            raise EnvironmentError("LLM_API_KEY not set")

        self.chat_model_name = os.getenv("LLM_CHAT_MODEL", "yandexgpt")
        self.embed_model_name = os.getenv("LLM_EMBEDDING_MODEL", "yandexgpt-embeddings")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.timeout_completion = int(os.getenv("LLM_TIMEOUT_COMPLETION", "60"))
        self.timeout_embedding = int(os.getenv("LLM_TIMEOUT_EMBEDDING", "30"))
        self.retry_attempts = int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))

        self.sdk = AIStudio(
            folder_id=folder_id,
            auth=APIKeyAuth(api_key),
        )

    @make_retry_decorator(3)
    def chat(self, prompt: str, temperature: Optional[float] = None) -> str:
        temp = temperature if temperature is not None else self.temperature

        try:
            model = self.sdk.models.completions(self.chat_model_name)
            model = model.configure(temperature=temp)
            alternatives = model.run(prompt, timeout=self.timeout_completion)

            if not alternatives or len(alternatives) == 0:
                raise RuntimeError("Empty response from LLM chat")

            first = alternatives[0]
            logger.debug(f"Chat response status={first.status.name}")
            return first.text

        except HTTPError as e:
            logger.error(f"Chat request failed (HTTP): {e}")
            raise
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    @make_retry_decorator(3)
    def embed(self, text: str, kind: str = "doc") -> List[float]:
        if kind not in ("doc", "query"):
            raise ValueError("kind must be 'doc' or 'query'")

        try:
            model = self.sdk.models.text_embeddings(f"{self.embed_model_name}-{kind}")
            result = model.run(text, timeout=self.timeout_embedding)
            return result.embedding

        except HTTPError as e:
            logger.error(f"Embedding request failed (HTTP): {e}")
            raise
        except AttributeError as e:
            logger.error(
                f"Embedding call failed: likely the model name '{self.embed_model_name}' "
                f"is not a valid embedding model for this SDK version. "
                f"Use something like 'yandexgpt-embeddings'. Error details: {e}"
            )
            raise
        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            raise

if __name__ == "__main__":
    try:
        llm = LLM()
        logger.info(
            f"Config loaded: folder_id={os.getenv('LLM_FOLDER_ID')}, "
            f"chat_model={llm.chat_model_name}, embed_model={llm.embed_model_name}"
        )

        print("Chat:")
        req = "Привет, как дела?"
        print(f"Вопрос: {req}")
        resp = llm.chat("Привет, как дела?", temperature=0.3)
        print(f"Ответ: {resp}")

        print("Embeddings:")
        emb = llm.embed("Тестовый текст для эмбеддинга", kind="doc")
        print(f"Размерность эмбеддинга: {len(emb)}")
        print(f"{emb[:5]} ...")

    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)
