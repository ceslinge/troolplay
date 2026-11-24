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


class ReportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: Literal["character", "story"]
    target_id: int
    reason: Reason
    details: Annotated[str | None, Field(max_length=1000)] = None

    @model_validator(mode="after")
    def explain_other(self) -> "ReportIn":
        # « Autre » ne dit rien à l'équipe : il faut quelques mots.
        if self.reason == "other" and not (self.details or "").strip():
            raise ValueError("Dis en quelques mots ce qui pose problème")
        return self
