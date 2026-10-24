class AgentError(Exception):
    """Expected failure. The message is safe to show to users."""


class AgentNotImplemented(AgentError):
    pass