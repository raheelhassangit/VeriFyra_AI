from django.db.models import Q

from .models import Project, Visibility


def judge_visible_projects(user):
    return Project.objects.filter(Q(visibility=Visibility.PUBLISHED) | Q(assignments__judge=user)).distinct()