class AuditConflict(Exception):
    """Request conflicts with the audit's current state or limits (maps to HTTP 409)."""


class InvalidTransition(AuditConflict):
    pass