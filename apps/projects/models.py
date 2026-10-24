import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Visibility(models.TextChoices):
    PRIVATE = "PRIVATE", "Private"
    PUBLISHED = "PUBLISHED", "Published"


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=150)
    website_url = models.URLField(max_length=500)
    github_url = models.URLField(max_length=500)
    github_branch = models.CharField(max_length=200, blank=True)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["owner", "-created_at"]), models.Index(fields=["visibility"])]

    def __str__(self):
        return self.name


class JudgeAssignment(models.Model):
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="judge_assignments", limit_choices_to={"role": "JUDGE"},
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["judge", "project"], name="uniq_judge_project")]

    def clean(self):
        if self.judge_id and self.judge.role != "JUDGE":
            raise ValidationError({"judge": "Assigned user must have the JUDGE role."})