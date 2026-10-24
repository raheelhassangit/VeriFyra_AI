from urllib.parse import urlparse

from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "website_url", "github_url", "github_branch",
                  "visibility", "published_at", "created_at", "updated_at")
        read_only_fields = ("id", "visibility", "published_at", "created_at", "updated_at")

    def validate_website_url(self, v):
        if urlparse(v).scheme not in ("http", "https"):
            raise serializers.ValidationError("Only http and https URLs are allowed.")
        return v

    def validate_github_url(self, v):
        p = urlparse(v)
        parts = [x for x in p.path.split("/") if x]
        if p.scheme != "https" or p.hostname not in ("github.com", "www.github.com") or len(parts) < 2:
            raise serializers.ValidationError("Must be an https://github.com/<owner>/<repo> URL.")
        return v


class JudgeProjectSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)

    class Meta:
        model = Project
        fields = ("id", "name", "website_url", "github_url", "github_branch", "owner_name", "published_at")
        read_only_fields = fields