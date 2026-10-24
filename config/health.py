import logging

from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    db_ok = True
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:
        logger.exception("Health check: database unavailable")
        db_ok = False
    return Response(
        {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "unavailable"},
        status=200 if db_ok else 503,
    )