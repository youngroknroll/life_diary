"""allauth 소셜 가입 폼.

allauth 가 설치되지 않은 데스크톱 설정에서 import 되지 않도록 별도 모듈로
두고, `SOCIALACCOUNT_FORMS` 에 문자열로만 참조한다.
"""

from allauth.socialaccount.forms import SignupForm as AllauthSocialSignupForm
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .email_verification import mark_email_verified


class SocialSignupForm(AllauthSocialSignupForm):
    """구글 가입에도 일반 가입과 같은 약관 동의를 요구한다."""

    consent = forms.BooleanField(
        required=True,
        label=_("이용약관과 개인정보처리방침에 동의합니다"),
        error_messages={
            "required": _("이용약관과 개인정보처리방침에 동의해야 가입할 수 있습니다.")
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conflicting_email = self._conflicting_email()

    def _conflicting_email(self):
        """이미 쓰는 주소면 아이디를 고르게 두지 않고 먼저 알린다."""
        email = self.initial.get("email") or ""
        if not email:
            return ""
        taken = get_user_model().objects.filter(email__iexact=email).exists()
        return email if taken else ""

    def save(self, request):
        user = super().save(request)
        # 구글이 이미 확인한 주소다. 코드를 한 번 더 받게 하지 않는다.
        mark_email_verified(user)
        return user
