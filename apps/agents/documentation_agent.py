from app.schemas.audit import AgentType

from .base import BaseAgent


class DocumentationAgent(BaseAgent):
    """In: doc_path. Out: requirements, requirement-to-evidence mappings, limitations."""
    agent_type = AgentType.DOCUMENTATION