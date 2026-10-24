from django.contrib import admin

from .models import ProjectEvaluation


@admin.register(ProjectEvaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("project", "judge", "status", "submitted_at")
    list_filter = ("status",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False