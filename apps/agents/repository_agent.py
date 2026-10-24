from app.schemas.audit import AgentType

from .base import BaseAgent


class RepositoryAgent(BaseAgent):
    """In: github_url, branch. Out: commit_sha, tool findings, dependency info, evidence."""
    agent_type = AgentType.REPOSITORY