from django.shortcuts import get_object_or_404

from .models import UserGoal, UserNote


class GoalRepository:
    """UserGoal ORM 쿼리 전담."""

    def find_by_user(self, user):
        return UserGoal.objects.filter(user=user).select_related("tag")

    def find_by_period(self, user, period):
        return UserGoal.objects.filter(user=user, period=period).select_related("tag")

    def get_or_404(self, pk, user):
        return get_object_or_404(UserGoal, pk=pk, user=user)


class NoteRepository:
    """UserNote ORM 쿼리 전담."""

    def find_by_user(self, user):
        return UserNote.objects.filter(user=user).order_by("-created_at")

    def find_latest(self, user):
        return UserNote.objects.filter(user=user).order_by("-created_at").first()

    def get_or_404(self, pk, user):
        return get_object_or_404(UserNote, pk=pk, user=user)
