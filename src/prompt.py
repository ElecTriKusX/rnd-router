import json

def validate_json(text: str) -> tuple[bool, dict | None]:
    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1 or start > end:
        return False, None

    json_str = text[start:end + 1]

    try:
        data = json.loads(json_str)
        return True, data
    except json.JSONDecodeError:
        return False, None

def read_prompt(name: str) -> str:
    with open(f'./prompts/{name}.md', 'r', encoding='utf-8') as file:
        return file.read()
