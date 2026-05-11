import json

from django.core.mail import EmailMultiAlternatives


class FakeResendResponse:
    status = 200
    reason = "OK"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b'{"id":"email_test_123"}'


class TestResendEmailBackend:
    def test_sends_plain_text_email_through_resend(self, monkeypatch, settings):
        from apps.core.email_backends import ResendEmailBackend

        calls = []

        def fake_urlopen(request, timeout):
            calls.append(
                {
                    "url": request.full_url,
                    "headers": dict(request.header_items()),
                    "payload": json.loads(request.data.decode()),
                    "timeout": timeout,
                }
            )
            return FakeResendResponse()

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        settings.RESEND_API_KEY = "re_test_virtual_key"

        backend = ResendEmailBackend()
        message = EmailMultiAlternatives(
            subject="Reset your password",
            body="Use this link to reset your password.",
            from_email="LifeDiary <noreply@example.com>",
            to=["user@example.com"],
        )

        assert backend.send_messages([message]) == 1
        assert calls == [
            {
                "url": "https://api.resend.com/emails",
                "headers": {
                    "Authorization": "Bearer re_test_virtual_key",
                    "Content-type": "application/json",
                    "User-agent": "lifeDiary-django-resend",
                },
                "payload": {
                    "from": "LifeDiary <noreply@example.com>",
                    "to": ["user@example.com"],
                    "subject": "Reset your password",
                    "text": "Use this link to reset your password.",
                },
                "timeout": 10,
            }
        ]

    def test_prefers_html_alternative_when_available(self, monkeypatch, settings):
        from apps.core.email_backends import ResendEmailBackend

        calls = []

        def fake_urlopen(request, timeout):
            calls.append(json.loads(request.data.decode()))
            return FakeResendResponse()

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        settings.RESEND_API_KEY = "re_test_virtual_key"

        message = EmailMultiAlternatives(
            subject="Username recovery",
            body="Plain fallback",
            from_email="LifeDiary <noreply@example.com>",
            to=["user@example.com"],
            cc=["manager@example.com"],
            bcc=["audit@example.com"],
            reply_to=["support@example.com"],
        )
        message.attach_alternative("<p>HTML body</p>", "text/html")

        backend = ResendEmailBackend()

        assert backend.send_messages([message]) == 1
        assert calls[0] == {
            "from": "LifeDiary <noreply@example.com>",
            "to": ["user@example.com"],
            "subject": "Username recovery",
            "text": "Plain fallback",
            "html": "<p>HTML body</p>",
            "cc": ["manager@example.com"],
            "bcc": ["audit@example.com"],
            "reply_to": ["support@example.com"],
        }
