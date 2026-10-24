from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import IsParticipant, IsPlatformAdmin

from .models import Project, Visibility
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsParticipant | IsPlatformAdmin]
    filterset_fields = ["visibility"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        qs = Project.objects.all()
        if self.request.user.role != Role.ADMIN:
            qs = qs.filter(owner=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        p = self.get_object()
        p.visibility = Visibility.PUBLISHED
        p.published_at = p.published_at or timezone.now()
        p.save(update_fields=["visibility", "published_at", "updated_at"])
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        p = self.get_object()
        p.visibility = Visibility.PRIVATE
        p.save(update_fields=["visibility", "updated_at"])
        return Response(self.get_serializer(p).data)