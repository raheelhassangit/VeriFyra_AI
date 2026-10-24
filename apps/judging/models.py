import uuid

from django.conf import settings
from django.db import models


class EvalStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"


class ProjectEvaluation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="evaluations")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="evaluations")
    scores = models.JSONField(default=dict, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=EvalStatus.choices, default=EvalStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["judge", "project"], name="uniq_eval_judge_project")]