# Claude Code Project Context

This is LifeDiary's concise, always-loaded bootstrap. Following current Claude
Code guidance, the project target is to keep this file under 200 lines.
Detailed governance lives in `AGENTS.md` and is read just in time. If this
summary conflicts with `AGENTS.md`, `AGENTS.md` wins.

## Product
LifeDiary is a Django-based life logging service.

Core loop: record a day in 10-minute slots, classify time with tags, manage
goals and notes, then review life patterns through statistics and rule-based
life feedback. Record quality and repeated daily use drive return.

Priority:
1. Daily 10-minute slot recording and tagging quality
2. Statistics and rule-based life feedback insight
3. Desktop distribution as a single local-user app
4. Public content pages and conservative ad revenue, gated by approval

## Binding Product Decisions
- Keep the Django monolith and existing app boundaries. Follow the
  `views -> use_cases -> repositories/domain_services -> models` flow where it
  already exists; do not introduce a new architecture style without approval.
- Desktop target: pywebview + waitress + SQLite + PyInstaller, one local user,
  GitHub Releases distribution. Desktop-only overrides live in
  `lifeDiary/settings/desktop.py` and must not weaken web production defaults.
- All user-facing strings are translatable in Korean and English. pytest
  compiles both message catalogs at startup via `conftest.py`.
- Diary, tag, goal, and statistics data are private to the owning user.
- Ads are allowed only on public pages (home, legal, future content pages) and
  only after explicit phase approval. Ads never appear on dashboard, stats,
  auth, or account workflows.
- Account deletion uses a 15-day grace period; `purge_deleted_accounts`
  permanently deletes due accounts and keeps a minimal masked audit record.
- The security baseline (django-axes brute-force protection, production login
  reCAPTCHA after repeated failures, cookie hardening, recovery-endpoint
  throttling) must not regress.

## Context Loading
- Do not preload every plan, report, or governance document.
- Before planning, role routing, or editing, read `AGENTS.md`.
- Read only the current plan, relevant status section, code, and domain sources.
- Treat `docs/project-status.md` as continuity context, not current source code.
- Verify repository facts from code and configuration before relying on prose.
- Local role adapters live in `.claude/agents/` and load only when activated.
- Do not duplicate detailed role contracts or import all of `AGENTS.md` here.

## Project Map
- `lifeDiary/`: Django configuration, root routing, public home/legal pages,
  `settings/` (`dev`, `prod`, `desktop`)
- `apps/core/`: shared utilities, email backends, i18n messages, template tags
- `apps/dashboard/`: 10-minute slot recording, day view, slot APIs
- `apps/tags/`: tag and category management and tag policy
- `apps/users/`: auth, account lifecycle, goals, notes, recovery flows
- `apps/stats/`: statistics aggregation and rule-based life feedback
- `desktop/`: pywebview launcher for the desktop build
- `templates/`, `locale/`, `scripts/`: shared web UI, translations, local
  tooling
- `docs/`: plans, refactoring logs, status index, security, architecture

## Stable Entry Paths
- Runtime: `manage.py`, `pytest.ini`, `conftest.py`, `lifeDiary/settings/`,
  `lifeDiary/urls.py`, `lifeDiary/views.py`
- Dashboard: `apps/dashboard/models.py`, `apps/dashboard/use_cases.py`,
  `apps/dashboard/repositories.py`, `apps/dashboard/views.py`,
  `apps/dashboard/api_urls.py`
- Tags: `apps/tags/models.py`, `apps/tags/use_cases.py`,
  `apps/tags/domain_services.py`, `apps/tags/repositories.py`
- Users: `apps/users/models.py`, `apps/users/use_cases.py`,
  `apps/users/forms.py`, `apps/users/views.py`,
  `apps/users/account_deletion.py`, `apps/users/repositories.py`
- Stats: `apps/stats/logic.py`, `apps/stats/use_cases.py`,
  `apps/stats/aggregation/`, `apps/stats/life_feedback.py`
- Frontend: `templates/base.html`, `templates/shared/`, `apps/*/templates/`,
  `apps/*/static/`
- Desktop: `desktop/launcher.py`, `lifeDiary/settings/desktop.py`,
  `requirements-desktop.txt`
- Tests and docs: `apps/*/tests.py`, `apps/*/test_*.py`, `docs/plans/`,
  `docs/refactoring/`, `docs/project-status.md`

Start with these stable paths. Use `rg` when the exact location is still
unknown or the task requires a repository-wide repeated-pattern check.

## Stack And Commands
- Python 3.13, Django 5.2, pytest + pytest-django, conda env `knou-life-diary`
- Targeted test: `conda run -n knou-life-diary pytest <test-path> --tb=short`
- Backend regression: `conda run -n knou-life-diary pytest`
- Django check: `conda run -n knou-life-diary python manage.py check`
- Prod deploy check: `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`
- Migration drift: `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run`
- Browser JS syntax: `node --check <static-js-path>`
- Local server: `conda run -n knou-life-diary python manage.py runserver`

The environment is conda, not `.venv` or `uv`. During Red-Green, run the
targeted test before broad regression.

## Working Method
1. Inspect `git status` and preserve existing user changes.
2. Read `AGENTS.md` before planning, task classification, or role routing.
3. Classify task shape and risk, then activate the smallest sufficient role set.
4. Read the approved plan before editing.
5. Backend behavior follows the Backend TDD Coach's one-test-at-a-time Kent
   Beck Red-Green-Refactor contract.
6. Frontend changes require both frontend reviewers' pre-implementation outputs
   and post-implementation verdicts; listing the roles alone is not evidence.
7. Implement only approved scope; record larger ideas as deferred work.
8. Run fresh verification and read complete output before claiming completion.

## Engineering Guardrails
- Prefer current repository patterns and framework-native Django APIs.
- Keep business rules in owning models, domain services, or use cases.
- Avoid speculative abstractions, adjacent cleanup, silent mutation, and broad
  refactors.
- Never create permanent objects in the dev database from verification
  scripts; verify through pytest or roll changes back.
- Never overwrite `prompt_plan.md`; it is a superseded historical i18n record.
- Do not commit, push, merge, or open a PR. The user executes Git actions;
  present copy-ready commands and messages instead.
- Report failed and unverified checks directly; confidence is not evidence.

## Instruction Placement
- `CLAUDE.md`: facts and gates needed in almost every session
- `AGENTS.md`: detailed product constraints, workflow, roles, and review gates
- `.claude/agents/`: local role adapters
- `docs/plans/`, `docs/refactoring/`: task boundaries and completion evidence
- Deterministic restrictions belong in settings or hooks, not advisory prose.
- Repeated procedures become skills or path-scoped rules only after
  demonstrated need.

## Session Continuity
After an implementation task changes files, its owning implementation role
updates the required work log and `docs/project-status.md`.
Recover a fresh session from the plan, Git diff, status, and verification logs.
