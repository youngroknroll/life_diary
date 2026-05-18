# Production Deploy Email Readiness

## Scope

This pass focused on production deployment safety for the existing web email/account recovery infrastructure.

Implemented scope:

- Added a production settings regression test.
- Set production `DEBUG` to `False`.
- Added a deploy PR verification gate before PR creation/update.
- Documented that live recovery email delivery remains deferred until a sender domain is purchased and verified in Resend.

Non-scope:

- No account recovery UI or flow rewrite.
- No SMTP fallback or mail provider switch.
- No changes to real local `.env` secrets.
- No live Resend delivery test because no verified sender domain is available.

## Changed Files

- `lifeDiary/test_prod_settings.py`
- `lifeDiary/settings/prod.py`
- `/Users/yeongroksong/Desktop/study/project/knou/.github/workflows/deploy-pr.yml`
- `.env.example`
- `docs/plans/2026-05-15_production-deploy-email-readiness.md`
- `docs/project-status.md`

## Verification

Commands run on 2026-05-15:

```bash
conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short
# 3 passed in 0.07s

DJANGO_SECRET_KEY=test-ci-secret-value-for-deploy-readiness-checks-only-1234567890 DB_NAME=test_db DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost DB_PORT=6543 RESEND_API_KEY=re_test_dummy DEFAULT_FROM_EMAIL='LifeDiary <noreply@example.com>' conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
# System check identified no issues (0 silenced).

ruby -e "require 'yaml'; YAML.load_file('/Users/yeongroksong/Desktop/study/project/knou/.github/workflows/deploy-pr.yml'); puts 'yaml ok'"
# yaml ok

conda run -n knou-life-diary pytest --tb=short
# 167 passed in 73.18s
```

## Deferred Refactoring Note

- Topic: Live recovery email delivery through Resend
- Why it is not part of the current scope: the project does not yet have a purchased/configured sender domain verified in Resend.
- Why it may be needed later: password reset and username recovery need real email delivery in production web mode.
- Trigger condition: a production sender domain is purchased, DNS records are configured, and Resend marks the domain as verified.
- Expected change location: Render/production environment variables, Resend domain settings, and optional recovery email smoke-test documentation.
- Related tests: `apps/core/test_email_backends.py`, `apps/users/test_password_reset.py`, `apps/users/test_username_recovery.py`

## Remaining Risks

- The parent GitHub Actions workflow was updated but not executed on GitHub in this local session.
- Production migrations and Render deploy hooks were not changed in this pass.
- The settings modules still have a larger deferred architecture issue: `prod.py` imports from `dev.py`.
