import re
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.users.email_verification import (
    PASSWORD_RESET,
    SIGNUP,
    ResendBlocked,
    VerificationStatus,
    issue_code,
    resend_code,
    verify_code,
)
from apps.users.models import EmailVerificationCode


def wrong_code(code):
    return "000000" if code != "000000" else "111111"


def expire(record):
    EmailVerificationCode.objects.filter(pk=record.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )


@pytest.mark.django_db
class TestCodeIssuing:
    def test_issued_code_is_six_digits(self, make_user):
        issued = issue_code(make_user(), SIGNUP)

        assert re.fullmatch(r"\d{6}", issued.code)

    def test_code_is_not_stored_in_plain_text(self, make_user):
        issued = issue_code(make_user(), SIGNUP)

        assert issued.code not in issued.record.code_hash

    def test_new_code_invalidates_the_previous_one(self, make_user):
        user = make_user()
        first = issue_code(user, SIGNUP)

        issue_code(user, SIGNUP)

        first.record.refresh_from_db()
        assert first.record.consumed_at is not None
        assert not verify_code(user, SIGNUP, first.code).ok

    def test_issuing_one_purpose_leaves_the_other_alone(self, make_user):
        user = make_user()
        signup_code = issue_code(user, SIGNUP)

        issue_code(user, PASSWORD_RESET)

        assert verify_code(user, SIGNUP, signup_code.code).ok


@pytest.mark.django_db
class TestCodeVerification:
    def test_correct_code_is_accepted(self, make_user):
        user = make_user()
        issued = issue_code(user, SIGNUP)

        assert verify_code(user, SIGNUP, issued.code).ok

    def test_correct_code_is_consumed_and_cannot_be_reused(self, make_user):
        user = make_user()
        issued = issue_code(user, SIGNUP)

        verify_code(user, SIGNUP, issued.code)

        assert verify_code(user, SIGNUP, issued.code).status is VerificationStatus.MISSING

    def test_wrong_code_is_rejected_and_counts_the_attempt(self, make_user):
        user = make_user()
        issued = issue_code(user, SIGNUP)

        outcome = verify_code(user, SIGNUP, wrong_code(issued.code))

        assert outcome.status is VerificationStatus.INVALID
        assert outcome.attempts_remaining == 2
        issued.record.refresh_from_db()
        assert issued.record.attempt_count == 1

    def test_code_dies_after_three_failed_attempts(self, make_user):
        user = make_user()
        issued = issue_code(user, SIGNUP)
        for _ in range(3):
            verify_code(user, SIGNUP, wrong_code(issued.code))

        outcome = verify_code(user, SIGNUP, issued.code)

        assert outcome.status is VerificationStatus.LOCKED

    def test_expired_code_is_rejected(self, make_user):
        user = make_user()
        issued = issue_code(user, SIGNUP)
        expire(issued.record)

        outcome = verify_code(user, SIGNUP, issued.code)

        assert outcome.status is VerificationStatus.EXPIRED


@pytest.mark.django_db
class TestResendPolicy:
    def test_resend_within_cooldown_is_blocked(self, make_user):
        user = make_user()
        issue_code(user, SIGNUP)

        with pytest.raises(ResendBlocked):
            resend_code(user, SIGNUP)

        assert EmailVerificationCode.objects.filter(user=user).count() == 1

    @override_settings(EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=0)
    def test_resend_past_the_hourly_cap_is_blocked(self, make_user):
        user = make_user()
        issue_code(user, SIGNUP)
        for _ in range(4):
            resend_code(user, SIGNUP)

        with pytest.raises(ResendBlocked):
            resend_code(user, SIGNUP)

    @override_settings(EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=0)
    def test_resend_issues_a_working_code(self, make_user):
        user = make_user()
        issue_code(user, SIGNUP)

        issued = resend_code(user, SIGNUP)

        assert verify_code(user, SIGNUP, issued.code).ok


@pytest.mark.django_db
class TestBackfill:
    def test_existing_accounts_are_marked_verified(self, make_user):
        from importlib import import_module

        from django.apps import apps as django_apps

        from apps.users.email_verification import is_email_verified
        from apps.users.models import EmailVerification

        user = make_user()
        EmailVerification.objects.filter(user=user).delete()
        migration = import_module(
            "apps.users.migrations.0004_emailverification_emailverificationcode"
        )

        migration.mark_existing_accounts_verified(django_apps, None)

        assert is_email_verified(user)
