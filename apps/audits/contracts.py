from rest_framework import serializers

from .models import AgentStatus, AgentType


class AgentOutcomeSerializer(serializers.Serializer):
    agent_type = serializers.ChoiceField(choices=AgentType.choices)
    status = serializers.ChoiceField(choices=AgentStatus.choices)
    result = serializers.JSONField(required=False, default=dict)
    error_message = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)
    duration_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0)


class ServiceStatusSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=["RUNNING", "COMPLETED", "FAILED", "CANCELLED"])
    stage = serializers.CharField(required=False, allow_blank=True, default="", max_length=100)
    agents = AgentOutcomeSerializer(many=True, required=False, default=list)
    commit_sha = serializers.CharField(required=False, allow_blank=True, default="", max_length=64)
    executive_summary = serializers.CharField(required=False, allow_blank=True, default="")
    coverage_percentage = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    overall_score = serializers.FloatField(required=False, allow_null=True, min_value=0, max_value=100)
    error = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)