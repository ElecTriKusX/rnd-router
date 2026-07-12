from llm import LLM
from prompt import read_prompt, validate_json
from dotenv import load_dotenv
import logging
from typing import Any
from pydantic import ValidationError
from typing import List
from models import Grant, DecomposeResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecomposeError(Exception):
    pass

def decompose(llm: LLM, grant: Grant, prompt_version: int) -> DecomposeResponse:
    
    grant_description = grant.title
    if grant.annotation is not None:
        grant_description = f"{grant.title}. {grant.annotation}"
    
    raw_prompt = read_prompt(f"decompose_v{prompt_version}")
    prompt = raw_prompt.replace("{grant_description}", grant_description)

    retry_attempts = 2
    for retry in range(retry_attempts):
        response = llm.chat(prompt)
        success, data = validate_json(response)
        if not success:
            logger.warning(f"Invalid JSON received, retry {retry}: {response}")
            continue

        try:
            return DecomposeResponse(**data)
        except ValidationError as e:
            logger.warning(f"Decompose failed (validation), retry {retry}: {response}")

    logger.error(f"НDecompose failed after {retry_attempts} retries")
    raise DecomposeError(f"Unable to get a valid JSON response for description: {grant_description}")

if __name__ == '__main__':
    llm = LLM()
    
    test_data = Grant(
        number="23-12-00123",
        years="2023-2025",
        role="Исполнитель",
        title="Биокатализ в химии акриловых полимеров, применяемых в горнодобывающей промышленности и для интенсификации нефтедобычи",
        annotation=None,
        link=None,
    )

    result = decompose(llm, test_data, 2)
    print(result)
    print(type(result))