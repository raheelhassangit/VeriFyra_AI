import logging
import time

from celery import shared_task
from django.conf import settings

from . import services
from .agent_client import AgentServiceClient, AgentServiceError, AgentServiceUnavailable
from .models import AuditRun

logger = logging.getLogger(__name__)
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}


def get_client():
    return AgentServiceClient()


def _poll(client, audit_id):
    deadline = time.monotonic() + settings.AUDIT_MAX_SECONDS
    cancel_sent = False
    while True:
        data = client.status(audit_id)
        services.apply_progress(audit_id, data)
        if data["state"] in TERMINAL:
            return data
        if not cancel_sent and AuditRun.objects.filter(pk=audit_id, cancel_requested=True).exists():
            client.cancel(audit_id)
            cancel_sent = True
        if time.monotonic() > deadline:
            client.cancel(audit_id)
            raise AgentServiceError("Audit exceeded the maximum allowed duration.")
        time.sleep(settings.AUDIT_POLL_INTERVAL)


@shared_task(bind=True, acks_late=True, reject_on_worker_lost=True, max_retries=3)
def run_audit(self, audit_id):
    info = self.request.delivery_info or {}
    resumable = bool(info.get("redelivered")) or self.request.retries > 0
    audit = services.claim_audit(audit_id, resumable)
    if audit is None:
        logger.info("Audit %s not claimable (duplicate or finished); skipping.", audit_id)
        return
    try:
        client = get_client()
        client.execute(audit)  # idempotent on the service side
        data = _poll(client, audit_id)
    except AgentServiceUnavailable as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15 * 2 ** self.request.retries)
        services.fail_audit(audit_id, str(exc))
        return
    except AgentServiceError as exc:
        services.fail_audit(audit_id, str(exc))
        return
    except Exception:
        logger.exception("Unexpected error in audit %s", audit_id)
        services.fail_audit(audit_id, "Unexpected internal error.")
        return
    services.finalize_audit(audit_id, data)