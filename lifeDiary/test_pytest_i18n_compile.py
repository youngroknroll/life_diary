from conftest import _compile_test_messages


def test_compile_test_messages_runs_django_compilemessages(monkeypatch):
    calls = []

    def fake_call_command(*args, **kwargs):
        calls.append((args, kwargs))

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
