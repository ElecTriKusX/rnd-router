"""Единые контракты данных для парсинга, ML, API и интерфейса."""

from pydantic import BaseModel, Field


class Publication(BaseModel):
    title: str
    year: int | None = None
    annotation: str | None = None
    journal: str | None = None
    link: str | None = None


class Grant(BaseModel):
    number: str
    years: str | None = None
    role: str | None = None
    title: str
    annotation: str | None = None
    link: str | None = None


class Profile(BaseModel):
    """Карточка исследователя независимо от источника: парсера, поиска или API."""

    id: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    unit: str = ""
    position: str | None = None
    degree: str | None = None
    email: str | None = None
    publications: list[Publication] = Field(default_factory=list)
    grants: list[Grant] = Field(default_factory=list)
    links: dict[str, str] = Field(default_factory=dict)


class ResearchRequest(BaseModel):
    """Входящий запрос клиента, не смешиваемый с историческим грантом."""

    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=20_000)

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.description}".strip()


class Subtask(BaseModel):
    id: int = Field(ge=1)
    topic: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)


class DecomposeResponce(BaseModel):
    subtasks: list[Subtask]


class CandidateMatch(BaseModel):
    """Профиль и объяснение того, почему он подходит для конкретной подзадачи."""

    profile: Profile
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=0)


class SubtaskMatches(BaseModel):
    subtask: Subtask
    candidates: list[CandidateMatch] = Field(default_factory=list)


class MatchResponse(BaseModel):
    request: ResearchRequest
    results: list[SubtaskMatches]


class EmailDraft(BaseModel):
    to: str | None = None
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
