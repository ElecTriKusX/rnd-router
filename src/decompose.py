from llm import LLM
from prompt import read_prompt, validate_json
from dotenv import load_dotenv
import logging
from typing import Any
from pydantic import BaseModel, ValidationError
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Subtask(BaseModel):
    id: int
    topic: str
    keywords: List[str]

class DecomposeResponse(BaseModel):
    subtasks: List[Subtask]

class DecomposeError(Exception):
    pass

def decompose(llm: LLM, grant_description: str, prompt_version: int) -> DecomposeResponse:
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
    
    test_data = [
        """Биокатализ в химии акриловых полимеров, применяемых 
в горнодобывающей промышленности и для интенсификации нефтедобычи""",
        """Система противоэпилептической электростимуляции блуждающего нерва""",
        """Разработка технологии термической обработки для повышения усталостных свойств 
полой рабочей лопатки вентилятора из титанового сплава 
и создание установки термической обработки полой лопатки для
реализации технологии в серийном технологическом процессе""",
    ]

    result = decompose(llm, test_data[0], 2)
    print(result)
    print(type(result))