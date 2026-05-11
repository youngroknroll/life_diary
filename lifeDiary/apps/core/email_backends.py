import json
import logging
import urllib.request
from urllib.error import HTTPError, URLError

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """Send Django email messages through Resend's HTTPS API."""

    api_url = "https://api.resend.com/emails"
    timeout = 10

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "RESEND_API_KEY", "")
        if not api_key:
            if self.fail_silently:
                return 0
            raise ValueError("RESEND_API_KEY is required for ResendEmailBackend")

        sent_count = 0
        for message in email_messages:
            try:
                self._send_message(message, api_key)
            except (HTTPError, URLError, OSError, ValueError):
                if not self.fail_silently:
                    raise
                logger.exception("Failed to send email through Resend")
            else:
                sent_count += 1
        return sent_count

    def _send_message(self, message, api_key):
        payload = self._build_payload(message)
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "lifeDiary-django-resend",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            if response.status < 200 or response.status >= 300:
                raise ValueError(f"Resend API returned {response.status} {response.reason}")
            response.read()

    def _build_payload(self, message):
        payload = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": list(message.to),
            "subject": message.subject,
            "text": message.body,
        }

        html_body = self._get_html_alternative(message)
        if html_body:
            payload["html"] = html_body
        if message.cc:
            payload["cc"] = list(message.cc)
        if message.bcc:
            payload["bcc"] = list(message.bcc)
        if message.reply_to:
            payload["reply_to"] = list(message.reply_to)

        return payload

    def _get_html_alternative(self, message):
        for content, mimetype in getattr(message, "alternatives", []):
            if mimetype == "text/html":
                return content
        return ""
