from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EvaluationViewSet, JudgeProjectViewSet, RubricView

router = DefaultRouter()
router.register("projects", JudgeProjectViewSet, basename="judging-project")
router.register("evaluations", EvaluationViewSet, basename="judging-evaluation")
urlpatterns = [path("rubric/", RubricView.as_view(), name="rubric")] + router.urls