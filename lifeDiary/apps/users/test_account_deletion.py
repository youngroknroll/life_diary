from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.dashboard.models import TimeBlock
from apps.tags.models import Category, Tag
from apps.users.account_deletion import (
    cancel_account_deletion,
    mask_email,
    purge_due_deleted_accounts,
    request_account_deletion,
)
from apps.users.models import AccountDeletionRequest, DeletedAccountRecord, UserGoal, UserNote


pytestmark = pytest.mark.django_db


class TestEmailMasking:
    @pytest.mark.parametrize(
        ("email", "expected"),
        [
            ("logbetter.info@gmail.com", "lo************@gmail.com"),
            ("a@example.com", "a@example.com"),
            ("ab@example.com", "a*@example.com"),
            ("", ""),
        ],
    )
    def test_masks_email_without_retaining_plain_address(self, email, expected):
        assert mask_email(email) == expected


class TestAccountDeletionService:
    def test_request_disables_user_and_schedules_purge(self, make_user):
        user = make_user(email="person@example.com")
        now = timezone.now()

        deletion_request = request_account_deletion(user, now=now)

        user.refresh_from_db()
        assert user.is_active is False
        assert deletion_request.user == user
        assert deletion_request.requested_at == now
        assert deletion_request.scheduled_delete_at == now + timedelta(days=15)
        assert deletion_request.cancelled_at is None
        assert deletion_request.purged_at is None

    def test_request_is_idempotent_for_active_request(self, make_user):
        user = make_user(email="person@example.com")
        first_now = timezone.now()
        second_now = first_now + timedelta(hours=2)

        first = request_account_deletion(user, now=first_now)
        second = request_account_deletion(user, now=second_now)

        assert second.id == first.id
        assert AccountDeletionRequest.objects.count() == 1
        assert second.requested_at == first_now

    def test_cancel_before_deadline_reactivates_user(self, make_user):
        user = make_user(email="person@example.com")
        requested_at = timezone.now()
        request_account_deletion(user, now=requested_at)

        cancelled = cancel_account_deletion(user, now=requested_at + timedelta(days=3))

        user.refresh_from_db()
        deletion_request = AccountDeletionRequest.objects.get(user=user)
        assert cancelled is True
        assert user.is_active is True
        assert deletion_request.cancelled_at == requested_at + timedelta(days=3)

    def test_cancel_after_deadline_is_rejected(self, make_user):
        user = make_user(email="person@example.com")
        requested_at = timezone.now()
        request_account_deletion(user, now=requested_at)

        cancelled = cancel_account_deletion(user, now=requested_at + timedelta(days=16))

        user.refresh_from_db()
        deletion_request = AccountDeletionRequest.objects.get(user=user)
        assert cancelled is False
        assert user.is_active is False
        assert deletion_request.cancelled_at is None

    def test_purge_due_account_deletes_user_data_and_keeps_masked_audit_record(self, make_user):
        user = make_user(username="delete-me", email="delete-me@example.com")
        category = Category.objects.create(
            name="테스트", slug="test-category", color="#123456", display_order=1
        )
        tag = Tag.objects.create(user=user, category=category, name="private", color="#123456")
        TimeBlock.objects.create(user=user, tag=tag, date=timezone.localdate(), slot_index=1)
        UserGoal.objects.create(user=user, tag=tag, period="daily", target_hours=1)
        UserNote.objects.create(user=user, note="private note")
        requested_at = timezone.now() - timedelta(days=16)
        request_account_deletion(user, now=requested_at)
        original_user_id = user.id
        date_joined = user.date_joined

        purged_count = purge_due_deleted_accounts(now=timezone.now())

        assert purged_count == 1
        assert get_user_model().objects.filter(id=original_user_id).exists() is False
        assert TimeBlock.objects.filter(user_id=original_user_id).exists() is False
        assert Tag.objects.filter(user_id=original_user_id).exists() is False
        record = DeletedAccountRecord.objects.get(original_user_id=original_user_id)
        assert record.username == "delete-me"
        assert record.masked_email == "de*******@example.com"
        assert record.date_joined == date_joined
        assert record.deletion_requested_at == requested_at
        assert record.purged_at is not None


class TestAccountDeletionViews:
    def test_mypage_links_to_account_delete_confirmation(self, auth_client):
        response = auth_client.get(reverse("users:mypage"))

        assert response.status_code == 200
        assert reverse("users:account_delete") in response.content.decode()

    def test_post_account_delete_requests_deletion_and_logs_out(self, auth_client):
        user = auth_client.user

        response = auth_client.post(reverse("users:account_delete"), follow=True)

        user.refresh_from_db()
        assert response.redirect_chain[-1][0] == reverse("home")
        assert user.is_active is False
        assert AccountDeletionRequest.objects.filter(user=user).exists()
        assert "_auth_user_id" not in auth_client.session

    def test_login_before_deadline_cancels_pending_deletion(self, client, make_user):
        password = "pass-Long-9!"
        user = make_user(username="pending-user", password=password)
        request_account_deletion(user)

        response = client.post(
            reverse("users:login"),
            {"username": "pending-user", "password": password},
            follow=True,
        )

        user.refresh_from_db()
        deletion_request = AccountDeletionRequest.objects.get(user=user)
        assert response.redirect_chain[-1][0] == reverse("home")
        assert user.is_active is True
        assert deletion_request.cancelled_at is not None
        assert str(user.id) == client.session["_auth_user_id"]

    def test_login_after_deadline_does_not_cancel_pending_deletion(self, client, make_user):
        password = "pass-Long-9!"
        user = make_user(username="expired-user", password=password)
        request_account_deletion(user, now=timezone.now() - timedelta(days=16))

        response = client.post(
            reverse("users:login"),
            {"username": "expired-user", "password": password},
        )

        user.refresh_from_db()
        deletion_request = AccountDeletionRequest.objects.get(user=user)
        assert response.status_code == 200
        assert user.is_active is False
        assert deletion_request.cancelled_at is None
        assert "_auth_user_id" not in client.session


class TestPurgeDeletedAccountsCommand:
    def test_command_purges_due_accounts(self, make_user):
        user = make_user(username="command-delete", email="command@example.com")
        original_user_id = user.id
        request_account_deletion(user, now=timezone.now() - timedelta(days=16))

        call_command("purge_deleted_accounts", verbosity=0)

        assert get_user_model().objects.filter(id=original_user_id).exists() is False
        assert DeletedAccountRecord.objects.filter(original_user_id=original_user_id).exists()
