import pytest

from apps.users.models import UserGoal


@pytest.fixture
def goal_factory(db):
    def _make(user, tag, period="daily", target_hours=2.0, **kwargs):
        return UserGoal.objects.create(
            user=user,
            tag=tag,
            period=period,
            target_hours=target_hours,
            **kwargs,
        )

    return _make
