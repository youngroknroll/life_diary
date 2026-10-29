"""아이디 찾기 뷰."""

import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext

from .. import login_protection
from ..forms import (
    UsernameRecoveryForm,
)
from ..repositories import UserAccountRepository

logger = logging.getLogger(__name__)
_user_repo = UserAccountRepository()


def _send_username_recovery_email(request, email):
    """이메일과 일치하는 모든 계정의 username을 메일로 발송한다.

    Why: 한 이메일에 여러 계정이 있을 수 있으므로 모두 안내.
    """
    users = _user_repo.find_active_by_email(email)
    if not users:
        return
    context = {
        "usernames": [u.get_username() for u in users],
        "domain": request.get_host(),
        "protocol": "https" if request.is_secure() else "http",
    }
    subject = render_to_string("users/recovery/username_recovery_subject.txt").strip()
    body = render_to_string("users/recovery/username_recovery_email.txt", context)
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except (SMTPException, OSError):
        logger.exception("Failed to send username recovery email")


def username_recovery_view(request):
    """아이디(username) 찾기.

    Why: 등록 여부 노출 방지를 위해 결과 페이지는 항상 동일.
    """
    if request.method == "POST":
        form = UsernameRecoveryForm(request.POST)
        if form.is_valid():
            if login_protection.is_rate_limited(
                request,
                "username-recovery",
                "RECOVERY_RATE_LIMIT_MAX_ATTEMPTS",
                "RECOVERY_RATE_LIMIT_WINDOW_SECONDS",
            ):
                return redirect("users:username_recovery_done")
            _send_username_recovery_email(request, form.cleaned_data["email"])
            return redirect("users:username_recovery_done")
    else:
        form = UsernameRecoveryForm()
    return render(
        request,
        "users/recovery/username_recovery_form.html",
        {"form": form, "page_title": gettext("아이디 찾기")},
    )


def username_recovery_done_view(request):
    """아이디 찾기 요청을 접수했다는 안내 화면을 보여준다."""
    return render(
        request,
        "users/recovery/username_recovery_done.html",
        {"page_title": gettext("아이디 찾기")},
    )
