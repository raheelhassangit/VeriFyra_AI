from app.schemas.audit import AgentType

from .base import BaseAgent


class WebsiteAgent(BaseAgent):
    """In: website_url. Out: pages, features, browser errors, evidence, untested checks."""
    agent_type = AgentType.WEBSITE