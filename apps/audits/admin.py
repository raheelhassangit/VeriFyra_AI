from django.contrib import admin

from .models import AgentExecution, AuditRun


class ReadOnly(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditRun)
class AuditRunAdmin(ReadOnly):
    list_display = ("id", "project", "status", "current_stage", "progress_percentage", "created_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("project__name", "requested_by__email")


@admin.register(AgentExecution)
class AgentExecutionAdmin(ReadOnly):
    list_display = ("audit_run", "agent_type", "status", "duration_ms", "retry_count")
    list_filter = ("agent_type", "status")