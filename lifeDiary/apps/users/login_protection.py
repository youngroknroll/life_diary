import json
import logging
from urllib import parse
from urllib import request as urlrequest
from urllib.error import URLError

from django.conf import settings
from django.core.cache import caches

logger = logging.getLogger(__name__)


RECOVERY_RATE_LIMIT_MAX_ATTEMPTS = 5


RECOVERY_RATE_LIMIT_WINDOW_SECONDS = 60 * 10


VALIDATION_RATE_LIMIT_MAX_ATTEMPTS = 10


VALIDATION_RATE_LIMIT_WINDOW_SECONDS = 60


LOGIN_RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def _security_cache():
    # 로그인 실패·복구·가입 검증 카운터. 통계 캐시와 분리해 cull·재배포에 지워지지 않는다.
    return caches["security"]


def get_client_identifier(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def is_rate_limited(request, scope, max_attempts_setting, window_setting):
    max_attempts = getattr(settings, max_attempts_setting, globals()[max_attempts_setting])
    window_seconds = getattr(settings, window_setting, globals()[window_setting])
    key = f"rate-limit:{scope}:{get_client_identifier(request)}"
    if _security_cache().add(key, 1, timeout=window_seconds):
        return False
    attempts = _security_cache().incr(key)
    return attempts > max_attempts


def login_recaptcha_enabled():
    return bool(getattr(settings, "LOGIN_RECAPTCHA_ENABLED", False))


def login_failure_limit():
    return getattr(settings, "LOGIN_RECAPTCHA_FAILURE_LIMIT", 5)


def login_failure_cache_timeout():
    return getattr(settings, "LOGIN_RECAPTCHA_CACHE_TIMEOUT", 60 * 60)


def login_failure_key(request, username):
    normalized_username = (username or "").strip().lower() or "anonymous"
    return f"login-failure:{get_client_identifier(request)}:{normalized_username}"


def get_login_failure_count(request, username):
    return int(_security_cache().get(login_failure_key(request, username), 0) or 0)


def record_login_failure(request, username):
    key = login_failure_key(request, username)
    if _security_cache().add(key, 1, timeout=login_failure_cache_timeout()):
        return 1
    try:
        return _security_cache().incr(key)
    except ValueError:
        _security_cache().set(key, 1, timeout=login_failure_cache_timeout())
        return 1


def reset_login_failures(request, username):
    _security_cache().delete(login_failure_key(request, username))


def login_attempts_remaining(failure_count):
    """How many tries are left before reCAPTCHA gates the form.

    Returns None when nothing has failed yet, so the template can stay silent
    instead of announcing a full budget to a first-time visitor.
    """
    if not failure_count:
        return None
    return max(login_failure_limit() - failure_count, 0)


def login_requires_recaptcha(request, username):
    return (
        login_recaptcha_enabled()
        and get_login_failure_count(request, username) >= login_failure_limit()
    )


def verify_recaptcha(token, remote_ip=None):
    if not token:
        return False
    secret = getattr(settings, "RECAPTCHA_SECRET_KEY", "")
    if not secret:
        return False
    data = {
        "secret": secret,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip
    encoded_data = parse.urlencode(data).encode()
    req = urlrequest.Request(LOGIN_RECAPTCHA_VERIFY_URL, data=encoded_data, method="POST")
    try:
        with urlrequest.urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        logger.exception("Failed to verify login reCAPTCHA")
        return False
    return payload.get("success") is True
