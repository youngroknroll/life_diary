# Legal Policy Pages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add first-pass public legal policy pages for privacy and terms, and expose them from the site footer.

**Architecture:** Keep the scope intentionally small by rendering static Django templates from `lifeDiary.views` and wiring them in the root URLconf. The pages are informational and do not introduce new models, forms, database writes, or business rules.

**Tech Stack:** Django views/templates, Bootstrap-based existing layout, pytest/Django test client.

---

## Approved Scope

- Add `/privacy/` and `/terms/` public pages.
- Add footer links to Privacy Policy and Terms of Service.
- Draft page copy based on the current product behavior:
  - account signup/login
  - username/email/password reset flows
  - diary/time-block/tag/statistics data
  - session, CSRF, language, and security cookies
  - contact email `logbetter.info@gmail.com`
- Keep cookie notice inside the privacy policy for this first pass.
- Do not add a separate `/security/`, `/contact/`, or `/cookies/` page in this task.
- Do not add consent banners or tracking controls.

## TDD Boundary

The user explicitly limited TDD to business logic. This task does not introduce business logic, so implementation will not force a Red-Green cycle before template/view work.

Verification still requires focused regression tests after implementation:

- privacy page returns HTTP 200 and contains key policy sections
- terms page returns HTTP 200 and contains key terms sections
- footer exposes links to both public pages

## Acceptance Criteria

- Anonymous users can open `/privacy/` and `/terms/`.
- The pages extend the existing base template and match the current site shell.
- The privacy page mentions:
  - collected account/contact data
  - user-created diary/tag/statistics data
  - cookies used for login/session/security/language
  - password reset/account recovery email flows
  - user rights and contact email
- The terms page mentions:
  - account responsibility
  - acceptable use
  - user content/data responsibility
  - service changes/availability
  - contact email
- Footer links are visible on the home page.
- Focused tests pass.

## Implementation Steps

### Task 1: Add Views And URLs

**Files:**
- Modify: `lifeDiary/views.py`
- Modify: `lifeDiary/urls.py`

**Steps:**
1. Add `privacy_policy(request)` and `terms_of_service(request)` views that render static templates.
2. Add root URL patterns:
   - `path("privacy/", views.privacy_policy, name="privacy")`
   - `path("terms/", views.terms_of_service, name="terms")`

### Task 2: Add Templates

**Files:**
- Create: `templates/legal/privacy.html`
- Create: `templates/legal/terms.html`

**Steps:**
1. Extend `base.html`.
2. Use restrained content layout consistent with existing Bootstrap pages.
3. Keep copy clear, factual, and specific to the current service.
4. Mark the documents as informational first-pass policy pages, not legal advice.

### Task 3: Add Footer Links

**Files:**
- Modify: `templates/base.html`
- Modify: `locale/en/LC_MESSAGES/django.po`

**Steps:**
1. Add a compact legal link row above or below the copyright/contact lines.
2. Link to `{% url 'privacy' %}` and `{% url 'terms' %}`.
3. Keep the footer from overflowing on mobile.
4. Add English translations for the new footer labels and policy page copy.
5. Ensure the shared `<html lang>` attribute follows Django's active language.

### Task 4: Add Regression Tests

**Files:**
- Modify: `apps/core/tests.py`
- Modify: `apps/core/test_i18n_phase1.py`

**Steps:**
1. Add tests for privacy page rendering.
2. Add tests for terms page rendering.
3. Add a footer link test on the home page.
4. Add English locale rendering tests for footer links and policy pages.
5. Add KO/EN checks for the rendered `<html lang>` value.

**Verification Command:**

```bash
pytest apps/core/tests.py apps/core/test_i18n_phase1.py --tb=short
```

### Task 5: Final Verification And Documentation

**Files:**
- Create: `docs/refactoring/2026-05-25_legal-policy-pages.md`
- Modify: `docs/project-status.md`

**Steps:**
1. Run focused tests.
2. Run `git diff --check`.
3. Record changed behavior, verification evidence, and deferred work.
4. Update `docs/project-status.md` with the new legal policy page status.

## Deferred Work

Deferred Refactoring Note

- Topic: Separate cookie, security, and contact/support pages.
- Why it is not part of the current scope: The current task is the minimum public legal-policy baseline.
- Why it may be needed later: Analytics, marketing cookies, incident reporting, account deletion workflow, or privacy rights workflows may need dedicated pages and forms.
- Trigger condition: Non-essential cookies, telemetry, paid accounts, or formal support/security reporting are introduced.
- Expected change location: `lifeDiary/views.py`, `lifeDiary/urls.py`, `templates/legal/`, `apps/core/tests.py`.
- Related tests: Public legal page rendering and footer navigation tests.
