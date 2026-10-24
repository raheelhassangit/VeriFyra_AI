from rest_framework.permissions import BasePermission

from .models import Role


def role_required(*roles):
    class _HasRole(BasePermission):
        def has_permission(self, request, view):
            u = request.user
            return bool(u and u.is_authenticated and u.is_active and u.role in roles)

    return _HasRole


IsParticipant = role_required(Role.PARTICIPANT)
IsJudge = role_required(Role.JUDGE)
IsPlatformAdmin = role_required(Role.ADMIN)