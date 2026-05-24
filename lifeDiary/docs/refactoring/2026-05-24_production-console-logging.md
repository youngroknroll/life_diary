# Production Console Logging

- Date: 2026-05-24
- Scope: Production settings error visibility with `DEBUG=False`
- Plan: Skipped by explicit user approval in chat for this small settings change.

## What Changed

- Added a production `LOGGING` setting to `lifeDiary/settings/prod.py`.
- Routed root `WARNING` and higher logs to `logging.StreamHandler`, which writes to the server process console.
- Routed `django.request` `ERROR` logs to the same console handler with `propagate=False`, so request exceptions are visible in deployment logs without exposing debug pages to users.
- Added a settings contract test in `lifeDiary/test_prod_settings.py`.

## Code Design Reason

`DEBUG` must stay `False` in production because Django debug pages can expose sensitive settings, environment values, paths, and stack traces to users. The safer design is to keep user-facing error responses generic while sending operational details to the server logs.

The implementation is intentionally limited to `lifeDiary/settings/prod.py` because this is a deployment observability concern, not a domain behavior change. Using Django's standard `LOGGING` setting avoids adding a custom error middleware or view-level exception handling where the framework already has the right request-error logging path.

The root logger is set to `WARNING` to keep warnings and errors visible without turning normal application flow into noisy logs. `django.request` is set to `ERROR` because the immediate need is deployed error diagnosis from terminal or platform logs.

## Code Insertion Summary

Inserted this settings block after the production email settings in `lifeDiary/settings/prod.py`:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
```

Added `test_prod_settings_send_error_logs_to_console()` to `lifeDiary/test_prod_settings.py` to lock the production logging contract.

## Verification Evidence

Fresh verification run on 2026-05-24:

```bash
pytest lifeDiary/test_prod_settings.py::test_prod_settings_send_error_logs_to_console
# RED before implementation: AttributeError: module 'lifeDiary.settings.prod' has no attribute 'LOGGING'
```

```bash
pytest lifeDiary/test_prod_settings.py::test_prod_settings_send_error_logs_to_console
# 1 passed in 0.03s
```

```bash
pytest lifeDiary/test_prod_settings.py apps/users/test_prod_settings.py
# 4 passed in 0.04s
```

```bash
DJANGO_SECRET_KEY=prod-logging-check-2026-05-24-with-diverse-characters-ABC123xyz789 DB_NAME=test_db DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost DB_PORT=6543 EMAIL_HOST_USER=test@example.com EMAIL_HOST_PASSWORD=test-password DEFAULT_FROM_EMAIL=test@example.com python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
# System check identified no issues (0 silenced).
```

```bash
git diff --check
# exit 0
```

## Not Verified

- A live Render deployment log stream was not checked in this session.
- A real production 500 response was not triggered against the deployed service.

## Deferred Refactoring Note

- Topic: Application-specific exception context logging
- Why it is not part of the current scope: The approved task was to make production errors visible in terminal/deployment logs while keeping `DEBUG=False`.
- Why it may be needed later: Some failures may require request IDs, user IDs, or business operation names beyond Django's default request exception log.
- Trigger condition: Deployed logs show exceptions but lack enough context to diagnose repeated production failures.
- Expected change location: `apps/*/views.py`, `apps/*/use_cases.py`, or a small request logging middleware if request correlation becomes necessary.
- Related tests: focused behavior tests for any affected view/use case, plus logging assertions where practical.
