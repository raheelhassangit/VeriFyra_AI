from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.errors import AgentNotImplemented
from app.schemas.audit import AgentType, AuditRequest
from app.services.gemma import GemmaClient


@dataclass
class AgentContext:
    request: AuditRequest
    doc_path: Path | None
    prior: dict[str, dict]  # results of agents that already completed, keyed "website", "repository", ...
    gemma: GemmaClient
    settings: Settings


class BaseAgent:
    agent_type: AgentType
    needs_any: tuple[AgentType, ...] = ()  # skipped unless at least one of these completed

    async def run(self, ctx: AgentContext) -> dict:
        raise AgentNotImplemented(f"{self.agent_type.value} agent is not implemented yet.")