from pydantic import BaseModel
from typing import List

class Publication(BaseModel):
    title: str
    year: int | None = None
    annotation: str | None = None
    journal: str | None = None
    link: str | None = None


class Grant(BaseModel):
    number: str
    years: str
    role: str
    title: str
    annotation: str | None = None
    link: str | None = None


class Profile(BaseModel):
    id: str
    full_name: str
    unit: str
    position: str | None = None
    degree: str | None = None
    publications: list[Publication]
    grants: list[Grant]
    links: dict[str, str]

class Subtask(BaseModel):
    id: str
    topic: str
    keywords: List[str]

class DecomposeResponse(BaseModel):
    subtasks: List[Subtask]

class Match(BaseModel):
    profile_id: str
    score: float
    reasons: List[str]

class RerankResponse(BaseModel):
    top: List[Match]

class Email(BaseModel):
    to: str
    subject: str
    body: str