from .base import AgentContext, BaseAgent
from .documentation_agent import DocumentationAgent
from .repository_agent import RepositoryAgent
from .verdict_agent import VerdictAgent
from .website_agent import WebsiteAgent

__all__ = ["AgentContext", "BaseAgent", "default_agents"]


def default_agents() -> list[BaseAgent]:
    """Execution order. Documentation runs after website and repository so it can use their evidence."""
    return [WebsiteAgent(), RepositoryAgent(), DocumentationAgent(), VerdictAgent()]