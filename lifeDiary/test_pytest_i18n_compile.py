import conftest

from conftest import _compile_test_messages


def test_compile_test_messages_runs_django_compilemessages(monkeypatch):
    calls = []

    def fake_call_command(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/msgfmt")
    monkeypatch.setattr("django.core.management.call_command", fake_call_command)

    _compile_test_messages()

    assert calls == [
        (
            ("compilemessages",),
            {
                "ignore": [".venv/*", ".worktrees/*", "staticfiles/*"],
                "locale": ["en", "ko"],
                "verbosity": 0,
            },
        )
    ]


def test_compile_test_messages_uses_python_fallback_when_msgfmt_is_missing(monkeypatch):
    calls = []

    def fake_python_fallback():
        calls.append("fallback")

    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr(
        conftest,
        "_compile_message_catalogs_without_msgfmt",
        fake_python_fallback,
        raising=False,
    )

    _compile_test_messages()

    assert calls == ["fallback"]
