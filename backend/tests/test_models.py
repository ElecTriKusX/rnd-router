import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from domain.models import CandidateMatch, Profile


def test_profile_has_one_canonical_email_field() -> None:
    profile = Profile(id="p1", full_name="Иванов Иван", email="ivanov@example.test")

    assert profile.email == "ivanov@example.test"
    assert profile.publications == []


def test_match_score_must_be_probability() -> None:
    profile = Profile(id="p1", full_name="Иванов Иван")

    with pytest.raises(ValidationError):
        CandidateMatch(profile=profile, score=1.1, reasons=["Совпадает тематика"])


def test_profile_fixture_conforms_to_the_canonical_model() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "profiles.json"
    profile_data = json.loads(fixture_path.read_text(encoding="utf-8"))[0]

    profile = Profile.model_validate(profile_data)

    assert profile.id == "ivanov_ii"
