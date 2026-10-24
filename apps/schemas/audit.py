import re
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

BRANCH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/\-]*")


class AgentType(StrEnum):
    WEBSITE = "WEBSITE"
    REPOSITORY = "REPOSITORY"
    DOCUMENTATION = "DOCUMENTATION"
    VERDICT = "VERDICT"


class AgentStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class AuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: UUID
    attempt: int = Field(default=1, ge=1, le=100)
    website_url: HttpUrl
    github_url: HttpUrl
    github_branch: str = Field(default="", max_length=200)

    @field_validator("github_url")
    @classmethod
    def github_only(cls, v):
        parts = [p for p in (v.path or "").split("/") if p]
        if (v.scheme != "https" or v.host not in {"github.com", "www.github.com"}
                or v.username or v.password or len(parts) < 2):
            raise ValueError("Must be an https://github.com/<owner>/<repo> URL.")
        return v

    @field_validator("github_branch")
    @classmethod
    def safe_branch(cls, v):
        if v and (not BRANCH_RE.fullmatch(v) or ".." in v):
            raise ValueError("Invalid branch or commit name.")
        return v


class AgentOut(BaseModel):
    agent_type: AgentType
    status: AgentStatus
    result: dict = Field(default_factory=dict)
    error_message: str = ""
    duration_ms: int | None = None


class StatusOut(BaseModel):
    state: Literal["RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
    stage: str = ""
    agents: list[AgentOut] = Field(default_factory=list)
    commit_sha: str = ""
    executive_summary: str = ""
    coverage_percentage: float | None = None
    overall_score: float | None = None
    error: str = ""


class AcceptedOut(BaseModel):
    audit_id: str
    state: str