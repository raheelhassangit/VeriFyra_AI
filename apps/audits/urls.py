from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AuditCreateView, AuditViewSet

router = DefaultRouter()
router.register("audits", AuditViewSet, basename="audit")
urlpatterns = [path("projects/<uuid:project_id>/audits/", AuditCreateView.as_view(), name="audit-create")] + router.urls