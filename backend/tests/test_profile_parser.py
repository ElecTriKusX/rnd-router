from infrastructure.profile_parser import parse_profile_md


def test_profile_parser_creates_canonical_profile() -> None:
    text = """# Иванов Иван Иванович
- Подразделение: Институт химии
- Должность: Доцент

## Публикации
### 2024
- Название: "Катализ полимеризации"
- Источник: "Вестник"

## Гранты и проекты

## Ссылки
- ORCID: https://orcid.org/example
- Email: ivanov@example.test
"""

    profile = parse_profile_md(text)

    assert profile.id == "ivanov_ii"
    assert profile.publications[0].title == "Катализ полимеризации"
    assert profile.links["ORCID"] == "https://orcid.org/example"
    assert profile.email == "ivanov@example.test"
