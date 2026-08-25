"""이메일 6자리 코드 인증 도메인 서비스.

가입 인증과 비밀번호 재설정이 같은 발급·발송·검증 경로를 쓴다.
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from . import verification_policy
from .models import EmailVerification, EmailVerificationCode

logger = logging.getLogger(__name__)

SIGNUP = EmailVerificationCode.PURPOSE_SIGNUP
PASSWORD_RESET = EmailVerificationCode.PURPOSE_PASSWORD_RESET

_SUBJECT_TEMPLATES = {
    SIGNUP: "users/verification/signup_code_subject.txt",
    PASSWORD_RESET: "users/verification/password_reset_code_subject.txt",
}
_BODY_TEMPLATES = {
    SIGNUP: "users/verification/signup_code_email.txt",
    PASSWORD_RESET: "users/verification/password_reset_code_email.txt",
}


class VerificationStatus(Enum):
    OK = "ok"
    INVALID = "invalid"
    EXPIRED = "expired"
    LOCKED = "locked"
    MISSING = "missing"


@dataclass(frozen=True)
class IssuedCode:
    code: str
    record: EmailVerificationCode


@dataclass(frozen=True)
class VerificationOutcome:
    status: VerificationStatus
    attempts_remaining: int = 0

    @property
    def ok(self) -> bool:
        return self.status is VerificationStatus.OK


class ResendBlocked(Exception):
    def __init__(self, retry_after_seconds: int):
        super().__init__(f"resend blocked for {retry_after_seconds}s")
        self.retry_after_seconds = retry_after_seconds


def _generate_code() -> str:
    length = verification_policy.CODE_LENGTH
    return f"{secrets.randbelow(10 ** length):0{length}d}"


def _active_codes(user, purpose):
    return EmailVerificationCode.objects.filter(
        user=user, purpose=purpose, consumed_at__isnull=True
    )


@transaction.atomic
def issue_code(user, purpose) -> IssuedCode:
    """새 코드를 발급하고 같은 목적의 미사용 코드를 모두 무효화한다."""
    _active_codes(user, purpose).update(consumed_at=timezone.now())
    code = _generate_code()
    record = EmailVerificationCode.objects.create(
        user=user,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=timezone.now()
        + timedelta(seconds=verification_policy.code_ttl_seconds()),
    )
    return IssuedCode(code=code, record=record)


def seconds_until_resend_allowed(user, purpose) -> int:
    latest = (
        EmailVerificationCode.objects.filter(user=user, purpose=purpose)
        .order_by("-created_at")
        .first()
    )
    if latest is None:
        return 0
    elapsed = (timezone.now() - latest.created_at).total_seconds()
    return max(int(verification_policy.resend_cooldown_seconds() - elapsed), 0)


def _sends_in_window(user, purpose) -> int:
    window_start = timezone.now() - timedelta(
        seconds=verification_policy.send_window_seconds()
    )
    return EmailVerificationCode.objects.filter(
        user=user, purpose=purpose, created_at__gte=window_start
    ).count()


def resend_code(user, purpose) -> IssuedCode:
    retry_after = seconds_until_resend_allowed(user, purpose)
    if retry_after:
        raise ResendBlocked(retry_after)
    if _sends_in_window(user, purpose) >= verification_policy.max_sends_per_window():
        raise ResendBlocked(verification_policy.send_window_seconds())
    return issue_code(user, purpose)


def verify_code(user, purpose, raw_code) -> VerificationOutcome:
    record = _active_codes(user, purpose).order_by("-created_at").first()
    if record is None:
        return VerificationOutcome(VerificationStatus.MISSING)
    if record.is_locked():
        return VerificationOutcome(VerificationStatus.LOCKED)
    if record.is_expired():
        return VerificationOutcome(VerificationStatus.EXPIRED)

    if not check_password((raw_code or "").strip(), record.code_hash):
        record.register_failure()
        status = (
            VerificationStatus.LOCKED
            if record.is_locked()
            else VerificationStatus.INVALID
        )
        return VerificationOutcome(status, record.attempts_remaining())

    record.consume()
    return VerificationOutcome(VerificationStatus.OK)


def seconds_until_expiry(user, purpose) -> int:
    record = _active_codes(user, purpose).order_by("-created_at").first()
    if record is None:
        return 0
    return max(int((record.expires_at - timezone.now()).total_seconds()), 0)


def ensure_active_code(user, purpose) -> bool:
    """쓸 수 있는 코드가 없을 때만 새로 발급해 보낸다."""
    record = _active_codes(user, purpose).order_by("-created_at").first()
    if record is not None and record.is_usable():
        return True
    return issue_and_send(user, purpose)


def start_verification(user) -> None:
    """가입 직후 미인증 상태를 명시적으로 남긴다."""
    EmailVerification.objects.get_or_create(user=user)


def mark_email_verified(user) -> None:
    EmailVerification.objects.update_or_create(
        user=user, defaults={"verified_at": timezone.now()}
    )


def is_email_verified(user) -> bool:
    return EmailVerification.objects.filter(
        user=user, verified_at__isnull=False
    ).exists()


def mask_email(email) -> str:
    local, separator, domain = (email or "").partition("@")
    if not separator:
        return ""
    head = local[:2] if len(local) > 2 else local[:1]
    return f"{head}***@{domain}"


def send_verification_email(user, purpose, code) -> bool:
    context = {
        "code": code,
        "username": user.get_username(),
        "expires_in_minutes": verification_policy.code_ttl_seconds() // 60,
    }
    subject = render_to_string(_SUBJECT_TEMPLATES[purpose]).strip()
    body = render_to_string(_BODY_TEMPLATES[purpose], context)
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except (SMTPException, OSError):
        logger.exception("Failed to send verification code email")
        return False
    return True


def issue_and_send(user, purpose) -> bool:
    return send_verification_email(user, purpose, issue_code(user, purpose).code)


def resend_and_send(user, purpose) -> bool:
    return send_verification_email(user, purpose, resend_code(user, purpose).code)
