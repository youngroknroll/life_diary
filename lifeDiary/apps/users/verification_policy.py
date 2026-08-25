"""이메일 코드 인증 정책값.

값은 설정으로 덮을 수 있고, 설정이 없으면 여기 기본값을 쓴다. 모델과 도메인
서비스가 같은 값을 봐야 해서 별도 모듈로 분리했다.
"""

from django.conf import settings

CODE_LENGTH = 6

_DEFAULTS = {
    "EMAIL_VERIFICATION_ENABLED": True,
    "EMAIL_VERIFICATION_CODE_TTL_SECONDS": 600,
    "EMAIL_VERIFICATION_MAX_ATTEMPTS": 3,
    "EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS": 60,
    "EMAIL_VERIFICATION_MAX_SENDS_PER_WINDOW": 5,
    "EMAIL_VERIFICATION_SEND_WINDOW_SECONDS": 60 * 60,
    "PASSWORD_RESET_SESSION_TTL_SECONDS": 600,
}


def _value(name):
    return getattr(settings, name, _DEFAULTS[name])


def is_enabled() -> bool:
    return bool(_value("EMAIL_VERIFICATION_ENABLED"))


def code_ttl_seconds() -> int:
    return int(_value("EMAIL_VERIFICATION_CODE_TTL_SECONDS"))


def max_attempts() -> int:
    return int(_value("EMAIL_VERIFICATION_MAX_ATTEMPTS"))


def resend_cooldown_seconds() -> int:
    return int(_value("EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS"))


def max_sends_per_window() -> int:
    return int(_value("EMAIL_VERIFICATION_MAX_SENDS_PER_WINDOW"))


def send_window_seconds() -> int:
    return int(_value("EMAIL_VERIFICATION_SEND_WINDOW_SECONDS"))


def reset_session_ttl_seconds() -> int:
    return int(_value("PASSWORD_RESET_SESSION_TTL_SECONDS"))
