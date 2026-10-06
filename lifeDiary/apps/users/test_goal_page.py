"""목표 관리 페이지 — 껍데기, 진행률, CRUD 리다이렉트, 중복 거절."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.tags.models import Category, Tag
from apps.users.goal_deadline import DeadlineState
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
            "due_date": "",
            "no_due_date": False,
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


def days_from_today(days):
    return timezone.localdate() + timedelta(days=days)


@pytest.mark.django_db
class TestGoalDueDate:
    def test_a_goal_added_with_a_due_date_keeps_it(self, client, owner, study):
        client.force_login(owner)
        due = days_from_today(10)

        client.post(
            reverse("users:usergoal_create"),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 4.0,
                "due_date": due.isoformat(),
            },
        )

        assert UserGoal.objects.get(user=owner).due_date == due

    def test_checking_no_due_date_wins_over_a_typed_date(self, client, owner, study):
        client.force_login(owner)

        client.post(
            reverse("users:usergoal_create"),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 4.0,
                "due_date": days_from_today(10).isoformat(),
                "no_due_date": "on",
            },
        )

        assert UserGoal.objects.get(user=owner).due_date is None

    def test_an_empty_date_without_no_due_date_is_rejected(self, client, owner, study):
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 4.0,
                "due_date": "",
            },
        )

        assert not UserGoal.objects.filter(user=owner).exists()
        assert response.context["add_error"]

    def test_a_new_goal_cannot_start_with_a_past_due_date(self, client, owner, study):
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_create"),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 4.0,
                "due_date": days_from_today(-1).isoformat(),
            },
        )

        assert not UserGoal.objects.filter(user=owner).exists()
        assert response.context["add_error"]

    def test_moving_a_due_date_into_the_past_is_rejected(self, client, owner, study):
        tomorrow = days_from_today(1)
        goal = UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0, due_date=tomorrow
        )
        client.force_login(owner)

        response = client.post(
            reverse("users:usergoal_update", args=[goal.pk]),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 4.0,
                "due_date": days_from_today(-1).isoformat(),
            },
        )

        goal.refresh_from_db()
        assert goal.due_date == tomorrow
        assert response.context["row_error"]

    def test_a_goal_already_past_its_due_date_can_still_be_edited(
        self, client, owner, study
    ):
        yesterday = days_from_today(-1)
        goal = UserGoal.objects.create(
            user=owner, tag=study, period="daily", target_hours=4.0, due_date=yesterday
        )
        client.force_login(owner)

        client.post(
            reverse("users:usergoal_update", args=[goal.pk]),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 6.0,
                "due_date": yesterday.isoformat(),
            },
        )

        goal.refresh_from_db()
        assert goal.target_hours == 6.0
        assert goal.due_date == yesterday

    def test_a_rejected_add_keeps_the_typed_due_date(self, client, owner, study):
        client.force_login(owner)
        past = days_from_today(-1).isoformat()

        response = client.post(
            reverse("users:usergoal_create"),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 4.0,
                "due_date": past,
            },
        )

        assert response.context["add_values"]["due_date"] == past
        assert response.context["add_values"]["no_due_date"] is False

    def test_a_form_without_a_deadline_field_adds_a_goal_without_one(
        self, client, owner, study
    ):
        client.force_login(owner)

        client.post(
            reverse("users:usergoal_create"),
            data={"tag": study.id, "period": "daily", "target_hours": 4.0},
        )

        assert UserGoal.objects.get(user=owner).due_date is None

    def test_undoing_a_delete_restores_a_past_due_date(self, client, owner, study):
        client.force_login(owner)
        yesterday = days_from_today(-1)

        client.post(
            reverse("users:usergoal_create"),
            data={
                "tag": study.id,
                "period": "daily",
                "target_hours": 4.0,
                "due_date": yesterday.isoformat(),
                "restore": "1",
            },
        )

        assert UserGoal.objects.get(user=owner).due_date == yesterday

    def test_the_progress_card_shows_each_goals_deadline(self, client, owner, study):
        UserGoal.objects.create(
            user=owner,
            tag=study,
            period="daily",
            target_hours=4.0,
            due_date=days_from_today(2),
        )
        client.force_login(owner)

        response = client.get(reverse("users:usergoal_list"))

        rows = response.context["goal_progress_rows"]
        assert rows[0]["deadline"] == DeadlineState("upcoming", 2)

    def test_the_goal_table_pairs_each_goal_with_its_deadline(
        self, client, owner, study
    ):
        goal = UserGoal.objects.create(
            user=owner,
            tag=study,
            period="daily",
            target_hours=4.0,
            due_date=days_from_today(-1),
        )
        client.force_login(owner)

        response = client.get(reverse("users:usergoal_list"))

        assert response.context["goal_items"] == [(goal, DeadlineState("overdue", 1))]
