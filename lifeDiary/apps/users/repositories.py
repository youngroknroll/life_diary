from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import UserGoal, UserNote


class UserAccountRepository:
    """User 계정 조회 ORM 쿼리 전담."""

    def find_inactive_with_pending_deletion(self, username):
        """탈퇴 유예 중(비활성 + 미취소 + 미영구삭제)인 계정을 찾는다."""
        return (
            get_user_model()
            .objects.filter(
                username__iexact=username,
                is_active=False,
                deletion_request__cancelled_at__isnull=True,
                deletion_request__purged_at__isnull=True,
            )
            .select_related("deletion_request")
            .first()
        )

    def find_active_by_email(self, email):
        return list(
            get_user_model().objects.filter(email__iexact=email, is_active=True)
        )

    def username_exists(self, username):
        return get_user_model().objects.filter(username__iexact=username).exists()

    def email_exists(self, email):
        return get_user_model().objects.filter(email__iexact=email).exists()


class GoalRepository:
    """UserGoal ORM 쿼리 전담."""

    def find_by_user(self, user):
        return UserGoal.objects.filter(user=user).select_related("tag")

    def find_by_period(self, user, period):
        return UserGoal.objects.filter(user=user, period=period).select_related("tag")

    def find_grouped_by_period(self, user):
        """사용자의 모든 UserGoal을 1쿼리로 fetch 후 period별 분리."""
        grouped = {"daily": [], "weekly": [], "monthly": []}
        for goal in UserGoal.objects.filter(user=user).select_related("tag", "tag__category"):
            if goal.period in grouped:
                grouped[goal.period].append(goal)
        return grouped

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
