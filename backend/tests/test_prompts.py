from infrastructure.prompts import read_prompt


def test_prompt_is_loaded_independently_from_working_directory() -> None:
    prompt = read_prompt("decompose_v1")

    assert "{grant_description}" in prompt
