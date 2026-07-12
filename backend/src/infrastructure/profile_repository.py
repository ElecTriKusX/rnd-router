"""Чтение валидированных профилей из локального файла данных."""

import json
from pathlib import Path

from domain.models import Profile


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILES_PATH = PROJECT_ROOT / "data" / "profiles.json"


def load_profiles(path: Path = DEFAULT_PROFILES_PATH) -> dict[str, Profile]:
    """Загружает profiles.json и запрещает дублирующиеся идентификаторы."""
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл профилей: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("profiles.json должен содержать JSON-массив профилей")

    profiles = [Profile.model_validate(item) for item in data]
    result = {profile.id: profile for profile in profiles}
    if len(result) != len(profiles):
        raise ValueError("В profiles.json есть повторяющиеся id профилей")
    return result
