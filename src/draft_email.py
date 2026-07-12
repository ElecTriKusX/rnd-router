# draft_email.py
from llm import LLM
from prompt import read_prompt, validate_json
import logging
from typing import List
from pydantic import ValidationError
from models import Grant, Profile, Email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DraftEmailError(Exception):
    pass

def draft_email(
    llm: LLM,
    grant: Grant,
    reasons: List[str],
    profile: Profile,
    prompt_version: int,
) -> Email:

    # Краткое описание гранта
    grant_description = grant.title
    if grant.annotation:
        grant_description += f". {grant.annotation}"

    # Информация о кандидате
    candidate_info = (
        f"ФИО: {profile.full_name}\n"
        f"Подразделение: {profile.unit}\n"
        f"Должность: {profile.position or 'не указана'}\n"
        f"Учёная степень: {profile.degree or 'нет'}"
    )

    # Формируем список причин в виде маркированного списка (для вставки в письмо)
    reasons_bullet = "\n".join(f"- {r}" for r in reasons)

    # Читаем промпт
    raw_prompt = read_prompt(f"draft_email_v{prompt_version}")
    prompt = raw_prompt.replace("{grant_description}", grant_description)
    prompt = prompt.replace("{candidate_info}", candidate_info)
    prompt = prompt.replace("{candidate_email}", profile.email)
    prompt = prompt.replace("{reasons}", reasons_bullet)

    retry_attempts = 2
    for retry in range(retry_attempts):
        response = llm.chat(prompt)
        success, data = validate_json(response)
        if not success:
            logger.warning(f"Invalid JSON received, retry {retry}: {response[:200]}...")
            continue

        try:
            return Email(**data)
        except ValidationError as e:
            logger.warning(f"Email validation failed, retry {retry}: {e}")
            continue

    logger.error(f"Failed to generate email after {retry_attempts} retries")
    raise DraftEmailError(f"Unable to generate email for profile {profile.id}")

if __name__ == '__main__':
    from models import Publication, Grant
    llm = LLM()

    # Тестовый грант
    grant = Grant(
        number="23-12-00123",
        years="2023-2025",
        role="Исполнитель",
        title="Биокатализ в химии акриловых полимеров, применяемых в горнодобывающей промышленности и для интенсификации нефтедобычи",
        annotation="Проект направлен на разработку экологически чистых каталитических систем",
        link=None
    )

    # Тестовый профиль кандидата
    candidate = Profile(
        id="p3",
        full_name="Кузина Ольга Александровна",
        unit="Кафедра прикладной и технической физики",
        position="Доцент (к.н.)",
        email="o.a.kuzina@utmn.ru",
        degree="к.т.н.",
        publications=[
            Publication(title="Влияние концентрации ПАВ водных растворов и температуры на коэффициент поверхностного натяжения", year=2016, annotation=None, journal="Вестник ТюмГУ", link=None),
            Publication(title="Особенности модернизации петрофизического исследовательского комплекса для осуществления возможности фильтрации газа совместно с водонефтяными флюидами", year=2022, annotation=None, journal="Вестник ТюмГУ", link=None),
            Publication(title="Исследование реологических свойств и вытеснение высокопарафинистой нефти", year=2020, annotation=None, journal="Вестник ТюмГУ", link=None),
            Publication(title="Расчетно-экспериментальный метод определения параметров фильтрации смеси «нефть — водный раствор поверхностно-активных веществ»", year=2020, annotation=None, journal="Вестник ТюмГУ", link=None),
        ],
        grants=[
        ],
        links={}
    )

    reasons = [
        'Имеет публикации по исследованию реологических свойств и вытеснению высокопарафинистой нефти', 
        'Публикации касаются физико-химических свойств, что частично пересекается с темой биокатализа в химии акриловых полимеров'
    ]

    try:
        email = draft_email(llm, grant, reasons, candidate, 2)
        print(f"To: {email.to}")
        print(f"Subject: {email.subject}")
        print(f"Body:\n{email.body}")
    except DraftEmailError as e:
        print(f"Ошибка: {e}")