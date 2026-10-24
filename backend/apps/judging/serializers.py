from django.conf import settings
from rest_framework import serializers

from apps.projects.selectors import judge_visible_projects

from .models import ProjectEvaluation


def check_scores(scores, require_all=False):
    rubric = settings.JUDGING_RUBRIC
    if not isinstance(scores, dict):
        raise serializers.ValidationError("Scores must be an object.")
    unknown = set(scores) - set(rubric)
    if unknown:
        raise serializers.ValidationError(f"Unknown criteria: {sorted(unknown)}")
    for k, v in scores.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= rubric[k]:
            raise serializers.ValidationError(f"{k} must be a number between 0 and {rubric[k]}.")
    if require_all and set(scores) != set(rubric):
        raise serializers.ValidationError(f"All criteria must be scored: {sorted(set(rubric) - set(scores))} missing.")
    return scores


class EvaluationSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=ProjectEvaluation._meta.get_field("project").related_model.objects.all())

    class Meta:
        model = ProjectEvaluation
        fields = ("id", "project", "scores", "feedback", "status", "created_at", "updated_at", "submitted_at")
        read_only_fields = ("id", "status", "created_at", "updated_at", "submitted_at")

    def validate_scores(self, v):
        return check_scores(v)

    def validate(self, attrs):
        user = self.context["request"].user
        project = attrs.get("project")
        if self.instance:
            if project and project != self.instance.project:
                raise serializers.ValidationError({"project": "Cannot be changed."})
        else:
            if not judge_visible_projects(user).filter(pk=project.pk).exists():
                raise serializers.ValidationError({"project": "Invalid project."})  # same message as nonexistent
            if ProjectEvaluation.objects.filter(judge=user, project=project).exists():
                raise serializers.ValidationError({"project": "You already have an evaluation for this project."})
        return attrs