from django.contrib import admin

from .models import JudgeAssignment, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "visibility", "published_at")
    list_filter = ("visibility",)
    search_fields = ("name", "owner__email")


@admin.register(JudgeAssignment)
class JudgeAssignmentAdmin(admin.ModelAdmin):
    list_display = ("judge", "project", "assigned_at")
    autocomplete_fields = ("project",)