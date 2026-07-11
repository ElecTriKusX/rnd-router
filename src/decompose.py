from llm import LLM
from prompt import read_prompt, validate_json
from dotenv import load_dotenv
import logging
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecomposeError(Exception):
    pass

def decompose(llm: LLM, grant_description: str, prompt_version:int) -> dict:
    raw_prompt = read_prompt(f"decompose_v{prompt_version}")
    prompt = raw_prompt.replace("{grant_description}", grant_description)

    response = ""
    retry_attempts = 2
    for retry in range(retry_attempts):
        response = llm.chat(prompt)
        success, data = validate_json(response)
        if success and validate_subtasks_structure(data):
            return data
        logger.warning(f"Decompose failed (validation), retry {retry}: {response}")
    
    logger.error(f"Decompose failed after all retries ({retry_attempts})")
    raise DecomposeError(f"Unable to get a valid JSON response for the description: {grant_description}")

def validate_subtasks_structure(data: dict) -> bool:
    # Проверяем наличие корневого ключа
    if "subtasks" not in data:
        return False

    subtasks = data["subtasks"]
    if not isinstance(subtasks, list):
        return False

    if not subtasks:
        return False

    # Проверяем подзадачи
    for idx, task in enumerate(subtasks):
        if not isinstance(task, dict):
            return False

        # Проверяем id
        if "id" not in task:
            return False
        if not isinstance(task["id"], int):
            return False

        # Проверяем topic
        if "topic" not in task:
            return False
        if not isinstance(task["topic"], str):
            return False

        # Проверяем keywords
        if "keywords" not in task:
            return False
        if not isinstance(task["keywords"], list):
            return False
        for kw_idx, kw in enumerate(task["keywords"]):
            if not isinstance(kw, str):
                return False

    return True

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