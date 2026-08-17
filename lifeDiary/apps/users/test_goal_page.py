"""목표 관리 페이지 — 껍데기, 진행률, CRUD 리다이렉트, 중복 거절."""

import pytest
from django.urls import reverse

from apps.tags.models import Category, Tag
from apps.users.models import UserGoal


@pytest.fixture
def owner(make_user):
    return make_user(username="goalowner")


@pytest.fixture
def study(owner):
    return Tag.objects.create(
        user=owner,
        name="공부",
        color="#7CD9A0",
        category=Category.objects.get(slug="investment"),
    )


@pytest.mark.django_db
class TestGoalPageShell:
    def test_the_goal_page_renders_a_full_document(self, client, owner):
        client.force_login(owner)

        response = client.get(reverse("users:usergoal_list"))

        assert response.status_code == 200
        assert b"<html" in response.content

    def test_the_page_carries_progress_rows_for_each_goal(self, client, owner, study):
        UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.get(reverse("users:usergoal_list"))

        rows = response.context["goal_progress_rows"]
        assert [row["tag_name"] for row in rows] == ["공부"]
        assert rows[0]["target_hours"] == 4.0

    def test_the_page_carries_no_progress_rows_without_goals(self, client, owner):
        client.force_login(owner)

        response = client.get(reverse("users:usergoal_list"))

        assert response.context["goal_progress_rows"] == []


@pytest.mark.django_db
class TestGoalMutationsOverAjax:
    """페이지 이동 없이 고치는 화면이라, XHR 은 리다이렉트 대신 본문을 되받는다."""

    def test_ajax_create_returns_the_refreshed_body(self, client, owner, study):
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={"tag": study.id, "period": "daily", "target_hours": 4.0},
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        assert response.status_code == 200
        body = response.content.decode()
        assert "goal-manager" in body
        assert "<html" not in body

    def test_ajax_create_reports_invalid_input_as_unprocessable(
        self, client, owner, study
    ):
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={"tag": study.id, "period": "daily", "target_hours": 99.0},
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        assert response.status_code == 422
        assert not UserGoal.objects.filter(user=owner).exists()

    def test_ajax_delete_returns_the_refreshed_body(self, client, owner, study):
        goal = UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_delete", args=[goal.pk]),
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        assert response.status_code == 200
        assert "goal-manager" in response.content.decode()
        assert not UserGoal.objects.filter(pk=goal.pk).exists()


@pytest.mark.django_db
class TestDuplicateGoals:
    def test_a_second_goal_for_the_same_tag_and_period_is_rejected(
        self, client, owner, study
    ):
        UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={"tag": study.id, "period": "daily", "target_hours": 9.0},
        )

        assert response.status_code == 200
        assert UserGoal.objects.filter(user=owner).count() == 1

    def test_a_rejected_add_keeps_what_the_user_typed(self, client, owner, study):
        UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={"tag": study.id, "period": "daily", "target_hours": 9.5},
        )

        assert response.context["add_values"] == {
            "tag": str(study.id),
            "period": "daily",
            "target_hours": "9.5",
        }

    def test_keeping_a_goals_own_tag_and_period_is_not_a_duplicate(
        self, client, owner, study
    ):
        goal = UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_update", args=[goal.pk]),
            data={"tag": study.id, "period": "daily", "target_hours": 6.0},
        )

        assert response["Location"] == reverse("users:usergoal_list")
        goal.refresh_from_db()
        assert goal.target_hours == 6.0

    def test_another_users_identical_goal_is_not_a_duplicate(
        self, client, owner, study, make_user
    ):
        stranger = make_user(username="stranger")
        stranger_tag = Tag.objects.create(
            user=stranger,
            name="공부",
            color="#7CD9A0",
            category=Category.objects.get(slug="investment"),
        )
        UserGoal.objects.create(
            user=stranger, tag=stranger_tag, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={"tag": study.id, "period": "daily", "target_hours": 4.0},
        )

        assert response["Location"] == reverse("users:usergoal_list")
        assert UserGoal.objects.filter(user=owner).count() == 1


@pytest.mark.django_db
class TestGoalFormPagesAreGone:
    def test_create_get_redirects_to_the_goal_page(self, client, owner):
        client.force_login(owner)

        response = client.get(reverse("users:usergoal_create"))

        assert response.status_code == 302
        assert response["Location"] == reverse("users:usergoal_list")

    def test_update_get_redirects_to_the_goal_page(self, client, owner, study):
        goal = UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.get(reverse("users:usergoal_update", args=[goal.pk]))

        assert response.status_code == 302
        assert response["Location"] == reverse("users:usergoal_list")


@pytest.mark.django_db
class TestGoalMutationsReturnToTheGoalPage:
    def test_creating_a_goal_returns_to_the_goal_page(self, client, owner, study):
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={"tag": study.id, "period": "daily", "target_hours": 4.0},
        )

        assert response["Location"] == reverse("users:usergoal_list")
        assert UserGoal.objects.filter(user=owner).count() == 1

    def test_updating_a_goal_returns_to_the_goal_page(self, client, owner, study):
        goal = UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_update", args=[goal.pk]),
            data={"tag": study.id, "period": "weekly", "target_hours": 9.0},
        )

        assert response["Location"] == reverse("users:usergoal_list")
        goal.refresh_from_db()
        assert goal.period == "weekly"
        assert goal.target_hours == 9.0

    def test_deleting_a_goal_returns_to_the_goal_page(self, client, owner, study):
        goal = UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0
        )
        client.force_login(owner)

        response = client.post(reverse("users:usergoal_delete", args=[goal.pk]))

        assert response["Location"] == reverse("users:usergoal_list")
        assert not UserGoal.objects.filter(pk=goal.pk).exists()
