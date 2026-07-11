from pathlib import Path
import json
import re
from typing import List, Dict, Optional
from models import Publication, Grant, Profile

"""
ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ГЕНЕРАЦИЯ id ПО full_name ДЛЯ ПРОФИЛЯ НПР
"""

_TMAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "",  "ы": "y", "ь": "",  "э": "e", "ю": "yu", "я": "ya",
}

_generate_id_map = dict()

def _translit(s: str) -> str:
    return "".join(_TMAP.get(ch, ch) for ch in s.lower())

def generate_id(full_name: str) -> str:
    parts = full_name.split()
    last = _translit(parts[0])
    initials = "".join(_translit(p[0].lower()) for p in parts[1:])
    full_id = f"{last}_{initials}" if initials else last

    if full_id in _generate_id_map:
        _generate_id_map[full_id] += 1
        return full_id

    _generate_id_map[full_id] = 1
    return full_id

"""
ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
"""

def section(lines: List[str], title: str) -> List[str]:
    """возвращает индексы сексии между двумя ## в md файле"""
    try:
        start = lines.index(f"## {title}") + 1
    except ValueError:
        return []
    end = next((i for i, ln in enumerate(lines[start:], start) if ln.startswith("## ")), len(lines))
    return lines[start:end]


def kv_value(line: str) -> str:
    """разделяет строку на <НАЗВАНИЕ СТРОКИ>:<СОДЕРЖИМОЕ>"""
    return line.split(":", 1)[1].strip() if ":" in line else ""

"""
ПАРСИНГ ПУБЛИКАЦИЙ
"""

def parse_publications(lines: List[str]) -> List[Publication]:
    """
    принимает список строк md файла из секции публикаций
    возвращает список публикаций
    """
    pubs: List[Publication] = []
    year: Optional[int] = None
    block: List[str] = []
    # проходимся по всем стррокам секции публикаций
    for ln in lines + [""]:
        # если строка начинается с года
        if ln.startswith("### "):
            pubs += _flush_pub_blocks(block, year)
            block = []
            year = int(ln.split()[1])
        else:
            block.append(ln)
    pubs += _flush_pub_blocks(block, year)
    return pubs


def _flush_pub_blocks(lines: List[str], year: Optional[int]) -> List[Publication]:
    if year is None:
        return []
    res: List[Publication] = []
    paragraph: List[str] = []
    for ln in lines + [""]:
        if ln.strip():
            paragraph.append(ln.rstrip())
        elif paragraph:
            res.append(_build_pub(paragraph, year))
            paragraph = []
    return res


def _build_pub(par: List[str], year: int) -> Publication:
    title = par[0].strip()
    journal = annotation = None
    for ln in par[1:]:
        low = ln.lower()
        if low.startswith("журнал"):
            journal = kv_value(ln)
        elif low.startswith("аннотация"):
            annotation = kv_value(ln)
    return Publication(title=title, year=year, annotation=annotation, journal=journal)

"""
ПАРСИНГ ГРАНТОВ
"""

grant_hdr = re.compile(r"^([^\(]+)\s*\(([^,]+),\s*([^\)]+)\)")

def parse_grants(lines: List[str]) -> List[Grant]:
    """
    принимает список строк md файла из секции грантов
    возвращает список грантов
    """
    grants: List[Grant] = []
    cur: List[str] = []
    # проходимся по всем строкам секции грантов
    for ln in lines + [""]:
        # если строка начинается с "-" то нашли грант
        if ln.startswith("-") or not ln.strip():
            if cur:
                grants.append(_build_grant(cur))
                cur = []
            if ln.startswith("-"):
                cur.append(ln.lstrip("- ").strip())
        else:
            cur.append(ln.strip())
    return grants


def _build_grant(lines: List[str]) -> Grant:
    m = grant_hdr.match(lines[0])
    if m:
        number, years, role = (m.group(1).strip(), m.group(2).strip(), m.group(3).strip())
    else:
        number, years, role = lines[0], "", ""
    title = annotation = ""
    for ln in lines[1:]:
        low = ln.lower()
        if low.startswith("название"):
            title = kv_value(ln)
        elif low.startswith("аннотация"):
            annotation = kv_value(ln)
    return Grant(number=number, years=years, role=role, title=title, annotation=annotation or None)

"""
ПАРСИНГ ССЫЛОК
"""

def parse_links(lines: List[str]) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for ln in lines:
        ln = ln.lstrip("- ").strip()
        if ":" in ln:
            k, v = ln.split(":", 1)
            if v.strip():
                d[k.strip()] = v.strip()
    return d


"""
ПАРСИНГ ПРОФИЛЯ
"""

def parse_profile_md(text: str) -> Profile:
    # текст md файла превращаем в список строк
    lines = [ln.rstrip() for ln in text.splitlines()]

    # парсинг ФИО
    full_name = re.search(r"^#\s+(.+)", text, re.M).group(1).strip()  # type: ignore

    # парсинг прочих данных о профиле между # и ##
    try:
        first_sec = next(i for i, ln in enumerate(lines) if ln.startswith("## "))
    except StopIteration:
        first_sec = len(lines)
    header_lines = lines[1:first_sec]

    unit = position = degree = None
    for ln in header_lines:
        low = ln.lower()
        if low.startswith("подраздел"):
            unit = kv_value(ln)
        elif low.startswith("должн"):
            position = kv_value(ln)
        elif "уч" in low and "степен" in low:
            degree = kv_value(ln)

    #парсинг разделов с ##
    pubs = parse_publications(section(lines, "Публикации"))
    grants = parse_grants(section(lines, "Гранты и проекты"))
    links = parse_links(section(lines, "Ссылки"))

    return Profile(
        id=generate_id(full_name),
        full_name=full_name,
        unit=unit or "",
        position=position,
        degree=degree,
        publications=pubs,
        grants=grants,
        links=links,
    )


"""ГЛАВНАЯ ФУНКЦИЯ"""

def main():
    """читает md файлы, парсит в profiles.json и выводит статистику"""
    root = Path(__file__).resolve().parents[0]
    src_dir = root / "data" / "profiles_raw"
    out_path = root / "data" / "profiles.json"

    profiles: List[Profile] = []
    for md_file in src_dir.glob("*.md"):
        profiles.append(parse_profile_md(md_file.read_text(encoding="utf-8")))

    out_path.write_text(
        json.dumps([p.model_dump() for p in profiles], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Количество профилей: {len(profiles)}")
    print(f"Количество профилей с грантами: {sum(bool(p.grants) for p in profiles)}")
    print(f"Количество профилей с непустыми аннотациями: {sum(any(pub.annotation for pub in p.publications) or any(gr.annotation for gr in p.grants) for p in profiles)}")

if __name__ == "__main__":
    main()
