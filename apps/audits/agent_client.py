import json
import logging
import os

import requests
from django.conf import settings

from .contracts import ServiceStatusSerializer

logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Permanent failure: do not retry."""


class AgentServiceNotConfigured(AgentServiceError):
    pass


class AgentServiceUnavailable(Exception):
    """Transient failure: safe to retry."""


class AgentServiceClient:
    def __init__(self):
        if not settings.AGENT_SERVICE_TOKEN:
            raise AgentServiceNotConfigured("AGENT_SERVICE_TOKEN is not configured.")
        self.base = settings.AGENT_SERVICE_URL.rstrip("/")
        self.headers = {"Authorization": f"Bearer {settings.AGENT_SERVICE_TOKEN}"}

    def _request(self, method, path, **kw):
        try:
            r = requests.request(method, self.base + path, headers=self.headers,
                                 timeout=settings.AGENT_SERVICE_REQUEST_TIMEOUT, **kw)
        except (requests.ConnectionError, requests.Timeout) as e:
            raise AgentServiceUnavailable("Agent service unreachable.") from e
        if r.status_code >= 500:
            raise AgentServiceUnavailable(f"Agent service error ({r.status_code}).")
        if r.status_code in (401, 403):
            raise AgentServiceError("Agent service rejected the internal credentials.")
        return r

    def execute(self, audit):
        payload = {
            "audit_id": str(audit.id),
            "website_url": audit.project.website_url,
            "github_url": audit.project.github_url,
            "github_branch": audit.project.github_branch,
            "attempt": audit.attempt,
        }
        doc = files = None
        try:
            if audit.documentation:
                doc = audit.documentation.open("rb")
                files = {"documentation": (os.path.basename(audit.documentation.name), doc)}
            r = self._request("POST", "/internal/audits/execute/", data={"payload": json.dumps(payload)}, files=files)
        finally:
            if doc:
                doc.close()
        if r.status_code not in (200, 202):
            raise AgentServiceError(f"Agent service rejected the audit request ({r.status_code}).")

    def status(self, audit_id):
        r = self._request("GET", f"/internal/audits/{audit_id}/status/")
        if r.status_code == 404:
            raise AgentServiceError("Agent service has no record of this audit.")
        if r.status_code != 200:
            raise AgentServiceError(f"Unexpected status response ({r.status_code}).")
        try:
            body = r.json()
        except ValueError:
            raise AgentServiceError("Agent service returned a non-JSON response.") from None
        s = ServiceStatusSerializer(data=body)
        if not s.is_valid():
            logger.warning("Invalid status payload for audit %s: %s", audit_id, s.errors)
            raise AgentServiceError("Agent service returned an invalid status payload.")
        return s.validated_data

    def cancel(self, audit_id):
        try:
            self._request("POST", f"/internal/audits/{audit_id}/cancel/")
        except (AgentServiceError, AgentServiceUnavailable):
            logger.warning("Cancel request to agent service failed for audit %s", audit_id)