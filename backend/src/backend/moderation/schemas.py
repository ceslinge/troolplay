from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Reason = Literal[
    "off_topic",
    "disrespect",
    "hate",
    "explicit",
    "personal_info",
    "impersonation",
    "spam",
    "illegal",
    "other",
]
Target = Literal["character", "story"]
Decision = Literal["founded", "no_action", "abusive"]
Duration = Literal["day", "week", "month", "forever"]

# Une raison écrite, toujours : la charte le promet à la personne concernée.
Why = Annotated[str, Field(min_length=3, max_length=1000)]


class ReportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: Target
    target_id: int
    reason: Reason
    details: Annotated[str | None, Field(max_length=1000)] = None

    @model_validator(mode="after")
    def explain_other(self) -> "ReportIn":
        # « Autre » ne dit rien à l'équipe : il faut quelques mots.
        if self.reason == "other" and not (self.details or "").strip():
            raise ValueError("Dis en quelques mots ce qui pose problème")
        return self


# Ce que l'équipe envoie.


class WhyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Why


class DecideIn(WhyIn):
    decision: Decision


class SuspendIn(WhyIn):
    duration: Duration


class ReportingIn(WhyIn):
    allowed: bool


# Ce que l'équipe lit. Jamais d'adresse email : un compte s'y désigne par son numéro.


class ReporterOut(BaseModel):
    """Qui signale, et comment ses signalements ont été jugés jusqu'ici."""

    id: int | None
    reports_sent: int
    founded: int
    abusive: int
    reporting_revoked: bool


class ReportOut(BaseModel):
    id: int
    reason: str
    details: str | None
    created_at: datetime
    decision: str | None
    handled_at: datetime | None
    reporter: ReporterOut
    # Le contenu tel qu'on le lisait au moment du signalement, effacé une fois tranché.
    snapshot: dict | None


class CaseSummary(BaseModel):
    """Un dossier : tous les signalements d'un même contenu."""

    target: Target
    target_id: int
    label: str
    exists: bool
    hidden: bool
    open_reports: int
    total_reports: int
    reasons: dict[str, int]
    last_reported_at: datetime


class CaseList(BaseModel):
    items: list[CaseSummary]
    total: int


class TeamCharacter(BaseModel):
    id: int
    name: str
    server: str | None
    hidden: bool


class TeamAccount(BaseModel):
    """Un compte vu par l'équipe : le seul endroit où l'on voit qui joue quoi."""

    id: int
    role: str
    created_at: datetime
    verified: bool
    suspended: bool
    banned_until: datetime | None
    reporting_revoked: bool
    characters: list[TeamCharacter]
    reports_received: int
    reports_sent: int


class TeamContent(BaseModel):
    """Une fiche ou une histoire vue par l'équipe, depuis sa page : à qui elle est, où elle en est."""

    target: Target
    target_id: int
    hidden: bool
    owner: TeamAccount | None
    open_reports: int


class CaseDetail(CaseSummary):
    owner: TeamAccount | None
    reports: list[ReportOut]


class JournalEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    action: str
    target_user_id: int | None
    target_character_id: int | None
    target_story_id: int | None
    detail: str | None
    reason: str
    created_at: datetime


class Journal(BaseModel):
    items: list[JournalEntry]
    total: int
