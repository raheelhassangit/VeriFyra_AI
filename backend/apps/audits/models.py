import os
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .exceptions import InvalidTransition


class AuditStatus(models.TextChoices):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


ACTIVE_STATUSES = ["PENDING", "QUEUED", "RUNNING"]

S = AuditStatus
TRANSITIONS = {
    S.PENDING: {S.QUEUED, S.FAILED, S.CANCELLED},
    S.QUEUED: {S.RUNNING, S.FAILED, S.CANCELLED},
    S.RUNNING: {S.COMPLETED, S.PARTIALLY_COMPLETED, S.FAILED, S.CANCELLED},
    S.FAILED: {S.QUEUED},  # explicit retry only
}


class AgentType(models.TextChoices):
    WEBSITE = "WEBSITE"
    REPOSITORY = "REPOSITORY"
    DOCUMENTATION = "DOCUMENTATION"
    VERDICT = "VERDICT"


class AgentStatus(models.TextChoices):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


def audit_doc_path(instance, filename):
    # Random server-side name: the user's filename never touches the filesystem.
    return f"audit_docs/{instance.id}{os.path.splitext(filename)[1].lower()}"


class AuditRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="audits")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audit_runs")
    status = models.CharField(max_length=20, choices=AuditStatus.choices, default=AuditStatus.PENDING)
    current_stage = models.CharField(max_length=100, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    commit_sha = models.CharField(max_length=64, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    coverage_percentage = models.FloatField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)
    executive_summary = models.TextField(blank=True)
    documentation = models.FileField(upload_to=audit_doc_path, blank=True)
    cancel_requested = models.BooleanField(default=False)
    attempt = models.PositiveSmallIntegerField(default=1)
    celery_task_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["requested_by", "status"]), models.Index(fields=["project", "-created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(status__in=ACTIVE_STATUSES),
                name="uniq_active_audit_per_project",
            )
        ]

    def transition(self, new, **fields):
        if new not in TRANSITIONS.get(self.status, ()):
            raise InvalidTransition(f"Cannot move audit from {self.status} to {new}.")
        self.status = new
        for k, v in fields.items():
            setattr(self, k, v)
        self.save(update_fields=["status", *fields])


class AgentExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_run = models.ForeignKey(AuditRun, on_delete=models.CASCADE, related_name="agents")
    agent_type = models.CharField(max_length=20, choices=AgentType.choices)
    status = models.CharField(max_length=10, choices=AgentStatus.choices, default=AgentStatus.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["agent_type"]
        constraints = [models.UniqueConstraint(fields=["audit_run", "agent_type"], name="uniq_agent_per_audit")]