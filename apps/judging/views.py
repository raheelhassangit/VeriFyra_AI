from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsJudge
from apps.projects.selectors import judge_visible_projects
from apps.projects.serializers import JudgeProjectSerializer

from .models import EvalStatus, ProjectEvaluation
from .serializers import EvaluationSerializer, check_scores


class JudgeProjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JudgeProjectSerializer
    permission_classes = [IsJudge]
    search_fields = ["name"]

    def get_queryset(self):
        from apps.projects.models import Project
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        return judge_visible_projects(self.request.user).select_related("owner")


class EvaluationViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationSerializer
    permission_classes = [IsJudge]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["status", "project"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ProjectEvaluation.objects.none()
        return ProjectEvaluation.objects.filter(judge=self.request.user)

    def perform_create(self, serializer):
        serializer.save(judge=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        if self.get_object().status == EvalStatus.SUBMITTED:
            return Response({"detail": "Submitted evaluations cannot be edited."}, status=409)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        with transaction.atomic():
            ev = ProjectEvaluation.objects.select_for_update().get(pk=self.get_object().pk)
            if ev.status == EvalStatus.SUBMITTED:
                return Response({"detail": "Already submitted."}, status=409)
            try:
                check_scores(ev.scores, require_all=True)
            except serializers.ValidationError as e:
                return Response({"scores": e.detail}, status=400)
            if not ev.feedback.strip():
                return Response({"feedback": ["Written feedback is required to submit."]}, status=400)
            ev.status = EvalStatus.SUBMITTED
            ev.submitted_at = timezone.now()
            ev.save(update_fields=["status", "submitted_at", "updated_at"])
        return Response(self.get_serializer(ev).data)


class RubricView(APIView):
    permission_classes = [IsJudge]

    def get(self, request):
        return Response(settings.JUDGING_RUBRIC)