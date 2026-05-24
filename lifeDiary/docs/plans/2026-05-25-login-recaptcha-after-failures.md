# Login reCAPTCHA After Failures Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Disable account lockout during local development and require reCAPTCHA after repeated failed logins in production.

**Architecture:** Keep the existing username/password login view. Add a small cache-backed login failure counter keyed by client and username; when the counter reaches the configured threshold, render a reCAPTCHA challenge and require server-side verification before allowing login. Disable axes in `dev.py`; enable reCAPTCHA settings in `prod.py` from environment variables.

**Tech Stack:** Django settings/views/templates, Django cache, Google reCAPTCHA server verification API via stdlib `urllib`, pytest.

---

### Task 1: Settings Boundary

**Files:**
- Modify: `lifeDiary/settings/dev.py`
- Modify: `lifeDiary/settings/prod.py`
- Test: `lifeDiary/test_prod_settings.py`
- Test: `apps/users/tests.py`

**Steps:**
1. Add tests for dev axes disabled and prod reCAPTCHA settings.
2. Run focused tests and confirm RED.
3. Set `AXES_ENABLED = False` in dev.
4. Set production `AXES_ENABLED = True`, `LOGIN_RECAPTCHA_ENABLED = True`, keys from env, and threshold `5`.

### Task 2: Login Challenge Flow

**Files:**
- Modify: `apps/users/views.py`
- Modify: `apps/users/templates/users/login.html`
- Test: `apps/users/tests.py`

**Steps:**
1. Add tests that five failed login attempts render reCAPTCHA, missing reCAPTCHA blocks login even with the right password, and valid reCAPTCHA plus right password logs in.
2. Run focused tests and confirm RED.
3. Implement cache-backed failure tracking and server-side reCAPTCHA verification.
4. Render the challenge only when required.

### Task 3: Documentation And Verification

**Files:**
- Create: `docs/refactoring/2026-05-25_login-recaptcha-after-failures.md`
- Modify: `docs/project-status.md`

**Verification commands:**

```bash
pytest apps/users/tests.py lifeDiary/test_prod_settings.py --tb=short
python manage.py check
git diff --check
```
