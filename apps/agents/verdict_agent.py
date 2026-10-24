from app.schemas.audit import AgentType

from .base import BaseAgent


class VerdictAgent(BaseAgent):
    """In: prior results. Out: executive_summary, coverage_percentage, overall_score, report."""
    agent_type = AgentType.VERDICT
    needs_any = (AgentType.WEBSITE, AgentType.REPOSITORY, AgentType.DOCUMENTATION)