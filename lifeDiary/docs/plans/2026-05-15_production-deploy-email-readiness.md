# Production Deploy Email Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the web production deployment safer while documenting that real email recovery delivery is deferred until a verified email domain is available.

**Architecture:** Keep the Resend HTTPS mail transport isolated in `apps.core.email_backends`. Treat this task as production settings and deployment-readiness work, not a rewrite of account recovery. The parent deploy PR workflow may validate settings/tests before creating a production deploy PR, but it must not require real Resend credentials.

**Tech Stack:** Django 5.2, pytest-django, GitHub Actions, Resend HTTPS API backend.

---

## Approved Scope

- Set production `DEBUG` to `False`.
- Add a small production settings regression test for the production security and email configuration contract.
- Add deploy PR workflow validation before opening or updating the deploy PR.
- Keep `.env.example` safe and document that real email recovery delivery is deferred until a verified domain is purchased/configured.
- Update `docs/project-status.md` and add a refactoring note after verification.

## Non-Scope

- Do not change real `.env` secret values.
- Do not rebuild password reset or username recovery UI.
- Do not add SMTP fallback or switch away from Resend.
- Do not implement desktop packaging/auth work.
- Do not perform live Resend delivery testing before a verified sender domain exists.

## Acceptance Criteria

- `lifeDiary.settings.prod.DEBUG` is `False`.
- Production settings still use `apps.core.email_backends.ResendEmailBackend`.
- Production settings read `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL` from environment variables.
- Deploy PR workflow runs a verification gate with dummy non-secret env values before creating/updating the deploy PR.
- Documentation says real recovery email delivery is deferred because no verified sender domain has been purchased/configured.
- Fresh verification results are recorded.

## Task 1: Production Settings Regression Test

**Files:**
- Create: `lifeDiary/test_prod_settings.py`
- Modify: none

**Step 1: Write the failing test**

Add tests that reload `lifeDiary.settings.prod` with controlled environment values and assert:

- `DEBUG is False`
- `EMAIL_BACKEND == "apps.core.email_backends.ResendEmailBackend"`
- `RESEND_API_KEY` reads from `RESEND_API_KEY`
- `DEFAULT_FROM_EMAIL` reads from `DEFAULT_FROM_EMAIL`

**Step 2: Run RED**

Run:

```bash
conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py --tb=short
```

Expected: fail on `DEBUG is False` because current prod settings set `DEBUG = True`.

## Task 2: Minimal Production Settings Fix

**Files:**
- Modify: `lifeDiary/settings/prod.py`
- Test: `lifeDiary/test_prod_settings.py`

**Step 1: Implement GREEN**

Change `DEBUG = True` to `DEBUG = False`.

**Step 2: Run GREEN**

Run:

```bash
conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py --tb=short
```

Expected: pass.

## Task 3: Deploy PR Workflow Verification Gate

**Files:**
- Modify: `/Users/yeongroksong/Desktop/study/project/knou/.github/workflows/deploy-pr.yml`

**Step 1: Add verification before PR creation**

Before the deploy PR creation step, add a job step that:

- sets dummy non-secret production env values;
- installs dependencies from `lifeDiary/requirements.txt`;
- runs the prod settings regression test;
- runs the existing email backend test;
- runs `python lifeDiary/manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`.

**Step 2: Verify workflow syntax locally where practical**

Because GitHub Actions cannot be fully executed locally in this environment, inspect the YAML and run the same commands locally from the parent repository path where possible.

## Task 4: Document Deferred Email Delivery

**Files:**
- Modify: `docs/project-status.md`
- Create: `docs/refactoring/2026-05-15_production-deploy-email-readiness.md`

**Step 1: Record deferred work**

Document:

- account recovery/email infrastructure exists;
- real email delivery is deferred until a verified sender domain is purchased/configured for Resend;
- no live Resend delivery verification was performed.

**Step 2: Record verification evidence**

Add fresh command results from this work.

## Final Verification

Run:

```bash
conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short
conda run -n knou-life-diary pytest --tb=short
DJANGO_SECRET_KEY=test-ci-secret-value-for-deploy-readiness-checks-only-1234567890 DB_NAME=test DB_USER=test DB_PASSWORD=test DB_HOST=localhost DB_PORT=6543 RESEND_API_KEY=re_test_dummy DEFAULT_FROM_EMAIL='LifeDiary <noreply@example.com>' conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
```

Report anything not verified, especially live email delivery and real GitHub Actions execution.
