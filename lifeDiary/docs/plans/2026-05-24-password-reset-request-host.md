# Password Reset Request Host Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make password reset emails use the current request host instead of the default `example.com` Site domain.

**Architecture:** Keep Django's `PasswordResetView` and existing rate limit behavior. Override only the save options in `RateLimitedPasswordResetView.form_valid()` so `domain_override` is set to `request.get_host()`.

**Tech Stack:** Django auth views/forms, pytest mail outbox tests.

---

### Task 1: Request Host Password Reset Links

**Files:**
- Modify: `apps/users/views.py`
- Test: `apps/users/test_password_reset.py`

**Step 1: Write failing test**

Assert a password reset POST with `HTTP_HOST="127.0.0.1:8000"` sends an email containing `http://127.0.0.1:8000` and not `example.com`.

**Step 2: Run RED**

Run:

```bash
pytest apps/users/test_password_reset.py::TestPasswordReset::test_reset_email_uses_request_host_not_default_site_domain --tb=short
```

Expected: FAIL with email body containing `http://example.com/...`.

**Step 3: Implement**

Pass `domain_override=self.request.get_host()` into `form.save()` inside `RateLimitedPasswordResetView.form_valid()`.

**Step 4: Verify**

Run:

```bash
pytest apps/users/test_password_reset.py::TestPasswordReset::test_reset_email_uses_request_host_not_default_site_domain --tb=short
pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py --tb=short
git diff --check
```
