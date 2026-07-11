from llm import LLM
from prompt import read_prompt, validate_json
import logging
from typing import List
from pydantic import ValidationError
from models import Subtask, Profile, RerankResponse, Match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RerankError(Exception):
    pass

def format_candidate(profile: Profile) -> str:
    lines = [
        f"ID: {profile.id}",
        f"ФИО: {profile.full_name}",
        f"Подразделение: {profile.unit}",
        f"Должность: {profile.position or 'не указана'}",
        f"Учёная степень: {profile.degree or 'нет'}",
    ]
    # Публикации (берём только названия, 5 штук)
    if profile.publications:
        pubs = [p.title for p in profile.publications[:5]]
        lines.append(f"Публикации: {', '.join(pubs)}")
    else:
        lines.append("Публикации: нет")
    # Гранты (берём названия)
    if profile.grants:
        grs = [g.title for g in profile.grants[:5]]
        lines.append(f"Гранты: {', '.join(grs)}")
    else:
        lines.append("Гранты: нет")
    return "\n".join(lines)

def rerank(
    llm: LLM,
    subtask: Subtask,
    candidates: List[Profile],
    prompt_version: int,
    top_n: int,
    
) -> RerankResponse:

    subtask_description = f"Тема: {subtask.topic}\nКлючевые слова: {', '.join(subtask.keywords)}"

    candidates_text = []
    for i, p in enumerate(candidates, 1):
        candidates_text.append(f"Кандидат {i}:\n{format_candidate(p)}")
    candidates_block = "\n\n".join(candidates_text)

    raw_prompt = read_prompt(f"rerank_v{prompt_version}")
    prompt = raw_prompt.replace("{subtask_description}", subtask_description)
    prompt = prompt.replace("{candidates}", candidates_block)
    prompt = prompt.replace("{top_n}", str(top_n))

    retry_attempts = 2
    for retry in range(retry_attempts):
        response = llm.chat(prompt)
        success, data = validate_json(response)
        if not success:
            logger.warning(f"Invalid JSON received, retry {retry}: {response[:200]}...")
            continue

        try:
            return RerankResponse(**data)
        except ValidationError as e:
            logger.warning(f"Rerank validation failed, retry {retry}: {e}")
            continue

    logger.error(f"Rerank failed after {retry_attempts} retries")
    raise RerankError(f"Unable to get valid rerank response for subtask id {subtask.id}")

if __name__ == '__main__':

    from models import Publication, Grant  # для создания тестовых данных
    llm = LLM()

    subtask = Subtask(
        id="sub1",
        topic="Биокатализ в химии акриловых полимеров",
        keywords=["биокатализ", "акриловые полимеры", "промышленность"]
    )

    candidate1 = Profile(
        id="p1",
        full_name="Костомаров Владимир Михайлович",
        unit="Институт социально-гуманитарных наук",
        position="Директор института",
        degree="к.и.н.",
        publications=[
            Publication(title="ПРОСТРАНСТВЕННАЯ ХАРАКТЕРИСТИКА СИСТЕМЫ РАССЕЛЕНИЯ РУССКИХ ПЕРВОПОСЕЛЕНЦЕВ СИБИРИ XVII-XVIII ВВ. БАССЕЙНА Р. ТОБОЛ В КОНТЕКСТЕ ЛАНДШАФТА (ОПТИКА ГИС)", year=2022, annotation=None, journal="Вестник ТюмГУ", link=None),
            Publication(title="Исламский ландшафт Тюменского края с начала XX до начала XXI века", year=2023, annotation=None, journal="Вестник ТюмГУ", link=None)
        ],
        grants=[
            Grant(number="24-28-00936", years="2022-2024", role="Руководитель", title="Грант РНФ «Историко-географическое измерение расселения в Зауралье (XVII-XVIII вв.)»", annotation=None, link=None)
        ],
        links={"ORCID": "https://orcid.org/..."}
    )

    candidate2 = Profile(
        id="p2",
        full_name="Крыжанков Максим Дмитриевич",
        unit="Передовая инженерная школа",
        position="Ведущий специалист",
        degree="к.т.н.",
        publications=[
            Publication(title="Анализ возможных потерь углеводородного сырья в процессе эксплуатации промысловых нефтепроводов", year=2019, annotation=None, journal=" Нефтегазовый терминал : сборник научных трудов", link=None)
        ],
        grants=[
        ],
        links={}
    )

    candidate3 = Profile(
        id="p3",
        full_name="Кузина Ольга Александровна",
        unit="Кафедра прикладной и технической физики",
        position="Доцент (к.н.)",
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

    candidates = [candidate1, candidate2, candidate3]

    try:
        result = rerank(llm, subtask, candidates, 2, 2)
        print(result)
        print(result.top[0].profile_id, result.top[0].score, result.top[0].reasons)
    except RerankError as e:
        print(f"Ошибка: {e}")