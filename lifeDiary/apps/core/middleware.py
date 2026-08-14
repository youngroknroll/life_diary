from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """settings.CONTENT_SECURITY_POLICY 값을 CSP 응답 헤더로 부착한다.

    Why: django-csp 의존성 없이 프로덕션 심층방어 헤더를 제공한다.
    설정이 비어 있으면 아무 것도 하지 않으므로 dev/desktop에는 영향이 없다.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        policy = getattr(settings, "CONTENT_SECURITY_POLICY", "")
        if policy and "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = policy
        return response
