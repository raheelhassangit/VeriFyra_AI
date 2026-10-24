from rest_framework import serializers

from .models import AgentExecution, AuditRun
from .validators import validate_documentation


class AuditCreateSerializer(serializers.Serializer):
    documentation = serializers.FileField(required=False, validators=[validate_documentation])


class AuditRunSerializer(serializers.ModelSerializer):
    has_documentation = serializers.SerializerMethodField()

    class Meta:
        model = AuditRun
        fields = ("id", "project", "status", "current_stage", "progress_percentage", "commit_sha",
                  "started_at", "completed_at", "error_message", "coverage_percentage", "overall_score",
                  "executive_summary", "has_documentation", "created_at")
        read_only_fields = fields

    def get_has_documentation(self, obj) -> bool:
        return bool(obj.documentation)


class AgentExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentExecution
        fields = ("id", "agent_type", "status", "started_at", "completed_at", "duration_ms",
                  "result", "error_message", "retry_count")
        read_only_fields = fields