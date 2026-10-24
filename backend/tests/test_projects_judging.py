import pytest

from apps.accounts.models import Role
from apps.projects.models import JudgeAssignment, Project, Visibility

API = "/api/v1"
P = {"name": "Demo", "website_url": "https://example.com", "github_url": "https://github.com/o/r"}
FULL = {"innovation": 8, "technical_implementation": 7, "gemma_usage": 9, "reliability_evidence": 6, "ux_impact": 8}


@pytest.fixture
def users(make_user):
    return {
        "p1": make_user("p1@x.com"), "p2": make_user("p2@x.com"),
        "j1": make_user("j1@x.com", Role.JUDGE), "j2": make_user("j2@x.com", Role.JUDGE),
        "admin": make_user("a@x.com", Role.ADMIN),
    }


def mkproj(owner, **kw):
    return Project.objects.create(owner=owner, **{**P, **kw})


# ---- projects / ownership ----
@pytest.mark.django_db
def test_unauthenticated_blocked(client_for):
    assert client_for().get(f"{API}/projects/").status_code == 401
    assert client_for().get(f"{API}/judging/projects/").status_code == 401


@pytest.mark.django_db
def test_participant_crud_own_only(users, client_for):
    c = client_for(users["p1"])
    r = c.post(f"{API}/projects/", P, format="json")
    assert r.status_code == 201 and r.data["visibility"] == "PRIVATE"
    assert c.get(f"{API}/projects/").data["count"] == 1
    other = mkproj(users["p2"])
    assert c.get(f"{API}/projects/{other.id}/").status_code == 404
    assert c.patch(f"{API}/projects/{other.id}/", {"name": "x"}, format="json").status_code == 404
    assert c.delete(f"{API}/projects/{other.id}/").status_code == 404
    assert Project.objects.filter(pk=other.pk).exists()


@pytest.mark.django_db
def test_visibility_cannot_be_set_directly(users, client_for):
    r = client_for(users["p1"]).post(f"{API}/projects/", {**P, "visibility": "PUBLISHED"}, format="json")
    assert r.status_code == 201 and r.data["visibility"] == "PRIVATE"


@pytest.mark.django_db
@pytest.mark.parametrize("field,val", [("website_url", "ftp://x.com"), ("github_url", "https://evil.com/o/r"),
                                       ("github_url", "https://github.com/onlyowner")])
def test_url_validation(users, client_for, field, val):
    assert client_for(users["p1"]).post(f"{API}/projects/", {**P, field: val}, format="json").status_code == 400


@pytest.mark.django_db
def test_publish_only_by_owner(users, client_for):
    p = mkproj(users["p1"])
    assert client_for(users["p2"]).post(f"{API}/projects/{p.id}/publish/").status_code == 404
    r = client_for(users["p1"]).post(f"{API}/projects/{p.id}/publish/")
    assert r.status_code == 200 and r.data["visibility"] == "PUBLISHED"


@pytest.mark.django_db
def test_role_walls(users, client_for):
    assert client_for(users["j1"]).get(f"{API}/projects/").status_code == 403
    assert client_for(users["p1"]).get(f"{API}/judging/projects/").status_code == 403
    assert client_for(users["p1"]).get(f"{API}/judging/evaluations/").status_code == 403
    assert client_for(users["p1"]).get(f"{API}/judging/rubric/").status_code == 403


# ---- judge visibility ----
@pytest.mark.django_db
def test_judge_sees_published_or_assigned_only(users, client_for):
    pub = mkproj(users["p1"], visibility=Visibility.PUBLISHED)
    priv = mkproj(users["p1"], name="Priv")
    assigned = mkproj(users["p2"], name="Assigned")
    JudgeAssignment.objects.create(judge=users["j1"], project=assigned)
    c = client_for(users["j1"])
    ids = {x["id"] for x in c.get(f"{API}/judging/projects/").data["results"]}
    assert ids == {str(pub.id), str(assigned.id)}
    assert c.get(f"{API}/judging/projects/{priv.id}/").status_code == 404
    assert client_for(users["j2"]).get(f"{API}/judging/projects/{assigned.id}/").status_code == 404


@pytest.mark.django_db
def test_judge_cannot_modify_projects_and_no_owner_email_leak(users, client_for):
    pub = mkproj(users["p1"], visibility=Visibility.PUBLISHED)
    c = client_for(users["j1"])
    assert c.patch(f"{API}/judging/projects/{pub.id}/", {"name": "x"}, format="json").status_code == 405
    assert c.delete(f"{API}/judging/projects/{pub.id}/").status_code == 405
    assert "owner" not in c.get(f"{API}/judging/projects/{pub.id}/").data
    assert "p1@x.com" not in str(c.get(f"{API}/judging/projects/{pub.id}/").data)


@pytest.mark.django_db
def test_assignment_requires_judge_role(users):
    from django.core.exceptions import ValidationError
    a = JudgeAssignment(judge=users["p1"], project=mkproj(users["p2"]))
    with pytest.raises(ValidationError):
        a.full_clean()


# ---- evaluations ----
@pytest.fixture
def pub(users):
    return mkproj(users["p1"], visibility=Visibility.PUBLISHED)


@pytest.mark.django_db
def test_draft_then_submit_then_locked(users, client_for, pub):
    c = client_for(users["j1"])
    r = c.post(f"{API}/judging/evaluations/", {"project": str(pub.id), "scores": {"innovation": 5}}, format="json")
    assert r.status_code == 201 and r.data["status"] == "DRAFT"
    eid = r.data["id"]
    assert c.post(f"{API}/judging/evaluations/{eid}/submit/").status_code == 400  # incomplete
    c.patch(f"{API}/judging/evaluations/{eid}/", {"scores": FULL, "feedback": "Strong."}, format="json")
    assert c.post(f"{API}/judging/evaluations/{eid}/submit/").data["status"] == "SUBMITTED"
    assert c.patch(f"{API}/judging/evaluations/{eid}/", {"feedback": "changed"}, format="json").status_code == 409
    assert c.post(f"{API}/judging/evaluations/{eid}/submit/").status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize("scores", [{"innovation": 11}, {"innovation": -1}, {"bogus": 3}, {"innovation": "9"}, {"innovation": True}])
def test_score_validation(users, client_for, pub, scores):
    r = client_for(users["j1"]).post(f"{API}/judging/evaluations/", {"project": str(pub.id), "scores": scores}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_cannot_evaluate_invisible_project_or_duplicate(users, client_for, pub):
    priv = mkproj(users["p1"], name="Priv")
    c = client_for(users["j1"])
    assert c.post(f"{API}/judging/evaluations/", {"project": str(priv.id), "scores": {}}, format="json").status_code == 400
    assert c.post(f"{API}/judging/evaluations/", {"project": str(pub.id), "scores": {}}, format="json").status_code == 201
    assert c.post(f"{API}/judging/evaluations/", {"project": str(pub.id), "scores": {}}, format="json").status_code == 400


@pytest.mark.django_db
def test_judges_cannot_touch_each_others_evaluations(users, client_for, pub):
    r = client_for(users["j1"]).post(f"{API}/judging/evaluations/", {"project": str(pub.id), "scores": {}}, format="json")
    eid = r.data["id"]
    c2 = client_for(users["j2"])
    assert c2.get(f"{API}/judging/evaluations/{eid}/").status_code == 404
    assert c2.patch(f"{API}/judging/evaluations/{eid}/", {"feedback": "x"}, format="json").status_code == 404
    assert c2.post(f"{API}/judging/evaluations/{eid}/submit/").status_code == 404
    assert c2.get(f"{API}/judging/evaluations/").data["count"] == 0


# ---- role escalation ----
@pytest.mark.django_db
def test_no_self_promotion(users, client_for):
    c = client_for(users["p1"])
    c.patch(f"{API}/auth/me/", {"role": "ADMIN"}, format="json")
    users["p1"].refresh_from_db()
    assert users["p1"].role == Role.PARTICIPANT