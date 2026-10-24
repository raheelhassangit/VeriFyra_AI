import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .exceptions import AuditConflict
from .models import ACTIVE_STATUSES, AgentExecution, AgentStatus, AgentType, AuditRun, AuditStatus

logger = logging.getLogger(__name__)
AGENT_DONE = [AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.SKIPPED]


def _lock(audit_id):
    return AuditRun.objects.select_for_update().get(pk=audit_id)


def _check_capacity(user, project):
    if AuditRun.objects.filter(project=project, status__in=ACTIVE_STATUSES).exists():
        raise AuditConflict("An audit is already active for this project.")
    n = AuditRun.objects.filter(requested_by=user, status__in=ACTIVE_STATUSES).count()
    if n >= settings.AUDIT_MAX_ACTIVE_PER_USER:
        raise AuditConflict(f"You already have {n} active audits. Wait for one to finish.")


def create_audit(*, project, user, documentation=None):
    _check_capacity(user, project)
    try:
        with transaction.atomic():
            audit = AuditRun.objects.create(project=project, requested_by=user, documentation=documentation or "")
            audit.transition(AuditStatus.QUEUED, current_stage="QUEUED")
            transaction.on_commit(lambda: dispatch(audit.pk))
    except IntegrityError:  # race: another request won
        raise AuditConflict("An audit is already active for this project.") from None
    return audit


def dispatch(audit_id):
    from .tasks import run_audit
    try:
        res = run_audit.delay(str(audit_id))
    except Exception:
        logger.exception("Could not enqueue audit %s", audit_id)
        fail_audit(audit_id, "Task queue unavailable. Retry the audit later.")
        return
    AuditRun.objects.filter(pk=audit_id).update(celery_task_id=res.id or "")


def claim_audit(audit_id, resumable):
    """Atomically move QUEUED -> RUNNING. A duplicate delivery returns None and does nothing."""
    with transaction.atomic():
        a = AuditRun.objects.select_for_update().filter(pk=audit_id).first()
        if a is None:
            return None
        if a.status == AuditStatus.QUEUED:
            a.transition(AuditStatus.RUNNING, started_at=timezone.now(), current_stage="STARTING",
                         progress_percentage=0, error_message="")
        elif not (a.status == AuditStatus.RUNNING and resumable):  # resumable = redelivery or Celery retry
            return None
        return a


def _upsert_agents(audit, agents):
    now = timezone.now()
    for ag in agents:
        ex, _ = AgentExecution.objects.get_or_create(audit_run=audit, agent_type=ag["agent_type"])
        ex.status = ag["status"]
        ex.result = ag.get("result") or {}
        ex.error_message = ag.get("error_message", "")
        ex.duration_ms = ag.get("duration_ms")
        if ex.status != AgentStatus.PENDING and not ex.started_at:
            ex.started_at = now
        if ex.status in AGENT_DONE and not ex.completed_at:
            ex.completed_at = now
        ex.save()


def apply_progress(audit_id, data):
    with transaction.atomic():
        a = _lock(audit_id)
        if a.status != AuditStatus.RUNNING:
            return
        _upsert_agents(a, data.get("agents", []))
        done = a.agents.filter(status__in=AGENT_DONE).count()
        a.current_stage = (data.get("stage") or a.current_stage)[:100]
        a.progress_percentage = min(99, round(100 * done / len(AgentType.values)))  # 100 only at finalize
        a.save(update_fields=["current_stage", "progress_percentage"])


def finalize_audit(audit_id, data):
    with transaction.atomic():
        a = _lock(audit_id)
        if a.status != AuditStatus.RUNNING:
            return a
        _upsert_agents(a, data.get("agents", []))
        completed = a.agents.filter(status=AgentStatus.COMPLETED).count()
        now = timezone.now()
        if data["state"] == "CANCELLED":
            a.transition(AuditStatus.CANCELLED, completed_at=now, current_stage="CANCELLED")
        elif completed == 0:
            a.transition(AuditStatus.FAILED, completed_at=now, current_stage="FAILED",
                         error_message=(data.get("error") or "No agent completed successfully.")[:2000])
        else:
            final = AuditStatus.COMPLETED if completed == len(AgentType.values) else AuditStatus.PARTIALLY_COMPLETED
            a.transition(final, completed_at=now, current_stage="DONE", progress_percentage=100,
                         commit_sha=data.get("commit_sha", ""), executive_summary=data.get("executive_summary", ""),
                         coverage_percentage=data.get("coverage_percentage"), overall_score=data.get("overall_score"),
                         error_message=(data.get("error") or "")[:2000])
        # Notification creation hooks in here once the notifications app exists.
    return a


def fail_audit(audit_id, message):
    with transaction.atomic():
        a = _lock(audit_id)
        if a.status not in ACTIVE_STATUSES:
            return a
        a.transition(AuditStatus.FAILED, completed_at=timezone.now(), current_stage="FAILED",
                     error_message=message[:2000])
    return a


def cancel_audit(audit_id):
    with transaction.atomic():
        a = _lock(audit_id)
        if a.status in (AuditStatus.PENDING, AuditStatus.QUEUED):
            a.transition(AuditStatus.CANCELLED, completed_at=timezone.now(), current_stage="CANCELLED")
        elif a.status == AuditStatus.RUNNING:
            a.cancel_requested = True  # the worker forwards it to the agent service
            a.save(update_fields=["cancel_requested"])
        else:
            raise AuditConflict(f"A {a.status} audit cannot be cancelled.")
    return a


def retry_audit(audit_id):
    with transaction.atomic():
        a = _lock(audit_id)
        _check_capacity(a.requested_by, a.project)
        try:
            with transaction.atomic():
                a.transition(AuditStatus.QUEUED, current_stage="QUEUED", progress_percentage=0, error_message="",
                             completed_at=None, started_at=None, cancel_requested=False)
        except IntegrityError:
            raise AuditConflict("An audit is already active for this project.") from None
        a.agents.update(status=AgentStatus.PENDING, result={}, error_message="", started_at=None,
                        completed_at=None, duration_ms=None, retry_count=F("retry_count") + 1)
        transaction.on_commit(lambda: dispatch(a.pk))
        a.transition(AuditStatus.QUEUED, current_stage="QUEUED", progress_percentage=0, error_message="",
                        completed_at=None, started_at=None, cancel_requested=False, attempt=a.attempt + 1)
    return a