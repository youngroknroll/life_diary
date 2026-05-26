# Legal Policy Pages Execution Log

## Context

The site had account, dashboard, stats, tag, and recovery flows, but no public policy pages or footer policy links. The immediate requirement was to add the minimum website pages needed for privacy/security trust, with TDD limited to business logic only.

## Changed

- Added public `/privacy/` and `/terms/` routes in `lifeDiary/urls.py`.
- Added static render views in `lifeDiary/views.py`.
- Added `templates/legal/privacy.html` with current-service privacy coverage:
  - account and contact data
  - recovery email flows
  - user-created time block, memo, tag, goal, and statistics data
  - session, CSRF, language, and security cookies
  - deletion/rights contact path
- Added `templates/legal/terms.html` with account responsibility, acceptable use, user content responsibility, availability, and contact terms.
- Added footer links to 개인정보처리방침 and 이용약관 in `templates/base.html`.
- Added focused rendering regression tests in `apps/core/tests.py`.
- Added English translations for the new legal page and footer strings in `locale/en/LC_MESSAGES/django.po`.
- Added English i18n rendering regression tests in `apps/core/test_i18n_phase1.py`.
- Changed the shared `<html lang>` attribute from hardcoded `ko` to the active Django language code.

## Design Reasoning

The pages are informational and do not introduce business logic, persistence, or user input. Keeping them as root-level views and static templates avoids adding an app or abstraction that the current scope does not need. Cookie details are included inside the privacy page for this first pass because the service currently uses only functional/session/security/language cookies.

## Verification

- `pytest apps/core/tests.py apps/core/test_i18n_phase1.py --tb=short`
  - Result: `21 passed in 2.05s`
- Render sample with English language cookie for `/`, `/privacy/`, and `/terms/`
  - Result: each response returned HTTP 200, `Content-Language: en`, `<html lang="en">`, English policy labels, and no Korean policy labels.
- `git diff --check`
  - Result: exit 0

## Not Verified

- Legal review by a qualified attorney was not performed.
- Manual browser inspection on mobile/desktop was not performed.
- Manual legal copy review in English was not performed.

## Deferred Refactoring Note

- Topic: Separate cookie, security, and contact/support pages.
- Why it is not part of the current scope: The current task is the minimum public legal-policy baseline.
- Why it may be needed later: Analytics, marketing cookies, telemetry, paid accounts, incident reporting, account deletion workflow, or formal privacy rights handling may need dedicated pages and forms.
- Trigger condition: Non-essential cookies, telemetry, paid features, public support intake, or security reporting workflow are introduced.
- Expected change location: `lifeDiary/views.py`, `lifeDiary/urls.py`, `templates/legal/`, `apps/core/tests.py`.
- Related tests: Public policy page rendering, footer navigation, and any future form submission tests.
