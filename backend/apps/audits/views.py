from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.accounts.permissions import IsParticipant, IsPlatformAdmin
from apps.projects.models import Project

from . import services
from .exceptions import AuditConflict
from .models import AuditRun
from .serializers import AgentExecutionSerializer, AuditCreateSerializer, AuditRunSerializer

ROLES = IsParticipant | IsPlatformAdmin


def _conflict(e):
    return Response({"detail": str(e)}, status=409)


class AuditCreateView(APIView):
    permission_classes = [ROLES]
    throttle_classes = [UserRateThrottle, ScopedRateThrottle]
    throttle_scope = "audit_create"

    @extend_schema(request=AuditCreateSerializer, responses={202: AuditRunSerializer})
    def post(self, request, project_id):
        qs = Project.objects.all()
        if request.user.role != Role.ADMIN:
            qs = qs.filter(owner=request.user)
        project = get_object_or_404(qs, pk=project_id)
        s = AuditCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            audit = services.create_audit(project=project, user=request.user,
                                          documentation=s.validated_data.get("documentation"))
        except AuditConflict as e:
            return _conflict(e)
        return Response(AuditRunSerializer(audit).data, status=202)


class AuditViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditRunSerializer
    permission_classes = [ROLES]
    filterset_fields = ["status", "project"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AuditRun.objects.none()
        qs = AuditRun.objects.all()
        if self.request.user.role != Role.ADMIN:
            qs = qs.filter(project__owner=self.request.user)
        return qs

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        audit = self.get_object()
        try:
            audit = services.cancel_audit(audit.pk)
        except AuditConflict as e:
            return _conflict(e)
        return Response(self.get_serializer(audit).data)

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        audit = self.get_object()
        try:
            audit = services.retry_audit(audit.pk)
        except AuditConflict as e:
            return _conflict(e)
        return Response(self.get_serializer(audit).data, status=202)

    @extend_schema(responses=AgentExecutionSerializer(many=True))
    @action(detail=True, methods=["get"], pagination_class=None)
    def agents(self, request, pk=None):
        audit = self.get_object()
        return Response(AgentExecutionSerializer(audit.agents.all(), many=True).data)