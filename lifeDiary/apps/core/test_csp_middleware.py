import pytest
from django.test import override_settings

CSP_MIDDLEWARE = "apps.core.middleware.ContentSecurityPolicyMiddleware"
TEST_POLICY = "default-src 'self'; object-src 'none'"


def _middleware_with_csp(settings):
    return list(settings.MIDDLEWARE) + [CSP_MIDDLEWARE]


@pytest.mark.django_db
def test_csp_header_attached_when_policy_configured(client, settings):
    with override_settings(
        MIDDLEWARE=_middleware_with_csp(settings),
        CONTENT_SECURITY_POLICY=TEST_POLICY,
    ):
        response = client.get("/")
    assert response["Content-Security-Policy"] == TEST_POLICY


@pytest.mark.django_db
def test_csp_header_absent_when_policy_not_configured(client, settings):
    with override_settings(MIDDLEWARE=_middleware_with_csp(settings)):
        response = client.get("/")
    assert "Content-Security-Policy" not in response
