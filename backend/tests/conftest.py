import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import Role, User

PW = "Str0ng-Pass-123"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


@pytest.fixture
def make_user(db):
    def _mk(email, role=Role.PARTICIPANT):
        return User.objects.create_user(email, PW, role=role)
    return _mk


@pytest.fixture
def client_for():
    def _c(user=None):
        c = APIClient()
        if user:
            c.force_authenticate(user)  # skips login only; permission classes still run for real
        return c
    return _c