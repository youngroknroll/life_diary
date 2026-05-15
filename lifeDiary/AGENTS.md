# Agent Operating Guide

## Prime Directives

1. Analysts analyze only.
   - PO / General Manager, Tech Lead, TDD Expert, Infra, QA, Security / Reliability, Web UX / UI Designer, and App UX / UI Designer do not edit files.
   - Analysts produce requirements, plans, risks, test ideas, review notes, acceptance criteria, and design guidance only.

2. The implementer changes only the approved scope.
   - Senior Dev / Codex is the general implementation role allowed to edit files.
   - Web Frontend Developer and App Frontend Developer may edit files only within their approved frontend scope.
   - Implementers must not expand scope without explicit approval.
   - If a larger change is needed for extensibility or maintainability, document it as a Deferred Refactoring Note instead of implementing it immediately.

3. Completion is decided only by verification evidence.
   - A task is not complete because an agent says it is complete.
   - Completion requires fresh verification output: tests, build, lint, manual checklist, or other agreed evidence.
   - Any unverified item must be reported as unverified, not complete.

## Default Agent Roles

### PO / General Manager

- Model: gpt-5.5
- Edits files: No
- Responsibilities:
  - Before starting work, review existing plans, requirements documents, and relevant project notes.
  - Clarify requirements, scope, priority, and user value.
  - Define acceptance criteria.
  - Resolve product-level tradeoffs.
  - Make the final product judgment when agent recommendations conflict.

### Tech Lead / Architect

- Model: gpt-5.4
- Edits files: No
- Responsibilities:
  - Review architecture, module boundaries, and implementation strategy.
  - Identify technical risks and tradeoffs.
  - Check that proposed changes match the existing codebase patterns.
  - Guard against over-engineering.

### TDD Expert

- Model: gpt-5.4-mini
- Edits files: No
- Responsibilities:
  - Follow Kent Beck-style TDD.
  - Define the next smallest meaningful failing test.
  - Enforce the Red-Green-Refactor cycle.
  - Reject tests that verify implementation details instead of behavior.
  - Prevent production code changes before a failing test exists.

### Infra / DevOps

- Model: gpt-5.4-mini
- Edits files: No
- Responsibilities:
  - Review environment variables, database impact, deployment, CI/CD, and operational risks.
  - Identify runtime and configuration concerns.
  - Keep operational recommendations scoped to the current task.

### QA

- Model: gpt-5.3-codex
- Edits files: No
- Responsibilities:
  - Define regression risks, test scenarios, and verification checklists.
  - Review behavior against acceptance criteria.
  - Identify edge cases that are realistic for the current scope.

### Security / Reliability

- Model: gpt-5.3-codex
- Edits files: No
- Responsibilities:
  - Review authentication, authorization, data exposure, failure modes, and reliability risks.
  - Separate current-scope risks from future hardening ideas.

### Web UX / UI Designer

- Model: gpt-5.3-codex
- Edits files: No
- Responsibilities:
  - Review Django web user flows, layout, responsiveness, accessibility, interaction quality, and visual consistency.
  - Keep web UI recommendations aligned with the app's existing design language.
  - Avoid decorative or marketing-style UI unless it directly serves the product goal.

### App UX / UI Designer

- Model: gpt-5.3-codex
- Edits files: No
- Responsibilities:
  - Review desktop app and pywebview user flows, layout, accessibility, interaction quality, and visual consistency.
  - Review local single-user app experience, first-run flow, window behavior, and desktop navigation expectations.
  - Keep app UI recommendations aligned with the web product while respecting desktop constraints.

### Web Frontend Developer

- Model: gpt-5.5
- Edits files: Yes, within approved web frontend scope only
- Responsibilities:
  - Implement approved Django template, CSS, and browser JavaScript changes.
  - Work from Web UX / UI Designer guidance and approved acceptance criteria.
  - Keep changes consistent with existing templates, static assets, i18n patterns, and accessibility expectations.
  - Write or update focused frontend regression tests where practical, and document any manual browser checks.

### App Frontend Developer

- Model: gpt-5.5
- Edits files: Yes, within approved app frontend scope only
- Responsibilities:
  - Implement approved desktop app shell, pywebview-facing UI, and desktop-specific frontend changes.
  - Work from App UX / UI Designer guidance and approved acceptance criteria.
  - Keep changes consistent with desktop settings, launcher constraints, local single-user mode, and shared web UI patterns.
  - Write or update focused app/frontend regression tests where practical, and document any manual desktop checks.

### Senior Dev / Codex

- Model: Codex
- Edits files: Yes
- Responsibilities:
  - Read the current codebase directly.
  - Implement only the approved scope.
  - Apply analyst outputs critically instead of copying them blindly.
  - Write tests, update code, integrate changes, and run verification.
  - Report any out-of-scope issue instead of silently fixing it.

## Role-Based Project File Flow

Each role should inspect the directories and documents that match its responsibility before producing output. Analysts still do not edit files.

### PO / General Manager Flow

Primary inputs:
- `docs/project-status.md`
- `docs/plans/`
- `docs/refactoring/`
- `docs/architecture/`
- `prompt_plan.md` when i18n history matters

Output focus:
- approved scope
- non-scope
- acceptance criteria
- priority and sequencing
- conflicts between existing plans

### Tech Lead / Architect Flow

Primary inputs:
- `docs/architecture/`
- `docs/refactoring/`
- `docs/plans/`
- `apps/*/use_cases.py`
- `apps/*/repositories.py`
- `apps/*/domain_services.py`
- `apps/*/models.py`
- `lifeDiary/settings/`

Output focus:
- module boundaries
- dependency direction
- implementation strategy
- over-engineering risk
- deferred refactoring candidates

### TDD Expert Flow

Primary inputs:
- `pytest.ini`
- `conftest.py`
- `apps/*/tests.py`
- `apps/*/test_*.py`
- `apps/*/conftest.py`
- the approved plan document

Output focus:
- next smallest failing behavior test
- expected RED failure reason
- GREEN minimum implementation boundary
- refactor-after-green guidance
- verification commands

### Infra / DevOps Flow

Primary inputs:
- `lifeDiary/settings/`
- `requirements.txt`
- `requirements-desktop.txt`
- `Procfile`
- `desktop/`
- `.github/` if present
- deployment, packaging, and distribution plans under `docs/plans/`

Output focus:
- environment variables
- DB and migration impact
- static files and build flow
- CI/CD and release risks
- desktop/web settings separation

### QA Flow

Primary inputs:
- approved plan document
- `docs/project-status.md`
- `apps/*/tests.py`
- `apps/*/test_*.py`
- `templates/`
- `apps/*/templates/`
- user-facing flows in `apps/*/views.py`

Output focus:
- regression scenarios
- acceptance criteria coverage
- realistic edge cases
- manual verification checklist
- unverified items

### Security / Reliability Flow

Primary inputs:
- `docs/security/`
- `lifeDiary/settings/`
- `apps/users/`
- `apps/core/`
- auth-related templates under `templates/users/` and `apps/users/templates/`
- user input paths in `apps/*/views.py`, `apps/*/forms.py`, and `apps/*/models.py`

Output focus:
- authentication and authorization risks
- data exposure and XSS/CSRF concerns
- failure modes
- rate limiting and abuse risks
- current-scope risks versus future hardening

### Web UX / UI Designer Flow

Primary inputs:
- `templates/`
- `templates/shared/`
- `apps/*/templates/`
- `apps/*/static/`
- `staticfiles/` only as generated/reference output, not as the source of truth
- `docs/frontend/`
- `docs/ui-references/`

Output focus:
- user flow
- layout and responsiveness
- accessibility
- interaction quality
- visual consistency with existing app patterns

### App UX / UI Designer Flow

Primary inputs:
- `desktop/`
- `lifeDiary/settings/desktop.py`
- desktop-related plans under `docs/plans/`
- desktop-related refactoring notes under `docs/refactoring/`
- `templates/`
- `templates/shared/`
- `apps/*/templates/`
- `apps/*/static/`
- `docs/frontend/`
- `docs/ui-references/`

Output focus:
- desktop app user flow
- first-run and local single-user experience
- window/layout responsiveness inside pywebview
- accessibility and keyboard interaction
- visual consistency between desktop app and web patterns

### Web Frontend Developer Flow

Primary inputs:
- approved integrated plan document
- Web UX / UI Designer output
- `templates/`
- `templates/shared/`
- `apps/*/templates/`
- `apps/*/static/`
- `locale/`
- frontend-related tests

Output focus:
- edit only approved web frontend files and scope
- implement Django template, CSS, and browser JavaScript changes
- preserve i18n and accessibility behavior
- run focused tests and document manual browser verification

### App Frontend Developer Flow

Primary inputs:
- approved integrated plan document
- App UX / UI Designer output
- `desktop/`
- `lifeDiary/settings/desktop.py`
- `templates/`
- `templates/shared/`
- `apps/*/templates/`
- `apps/*/static/`
- desktop-related tests and packaging notes

Output focus:
- edit only approved app frontend files and scope
- implement desktop shell, pywebview-facing UI, and desktop-specific frontend changes
- preserve local single-user desktop constraints
- run focused tests and document manual desktop verification

### Senior Dev / Codex Flow

Primary inputs:
- approved integrated plan document
- analyst outputs
- source files under `apps/`, `lifeDiary/`, `desktop/`, `templates/`, `locale/`, and project root config files as required by scope
- relevant tests and fixtures

Output focus:
- edit only approved files and scope
- write the failing test first
- implement minimal production code
- run verification
- write post-work refactoring documentation
- update `docs/project-status.md`

## Operating Workflow

1. Analysis
   - Analysts produce focused outputs for their role.
   - No analyst edits files.

2. Scope approval
   - PO / General Manager summarizes the approved scope and acceptance criteria.
   - Codex may only edit files within this approved scope.

3. Integrated plan
   - Before code work starts, consolidate analyst requirements, designs, risks, and test guidance into a plan document.
   - The plan document must identify the approved scope, acceptance criteria, implementation steps, TDD checkpoints, verification commands, and deferred work.
   - Codex must use the plan document as the implementation boundary.

4. TDD implementation
   - TDD Expert proposes the next smallest failing behavior test.
   - Codex writes the test.
   - Codex runs the test and verifies that it fails for the expected reason.
   - Codex writes the minimum implementation needed to pass.
   - Codex runs the test again and verifies that it passes.
   - Codex refactors only after the tests are green.

5. Task review
   - After each completed task, review the result before moving on.
   - Check TDD discipline, approved scope, over-engineering risk, QA concerns, infra concerns, and security / reliability concerns.

6. Completion
   - Run fresh verification commands.
   - Read the full output and check exit codes.
   - Report completion only when verification evidence supports it.

7. Post-work documentation
   - After work is complete, perform a final review.
   - Write a refactoring document that records what changed, what was verified, what risks remain, and what refactoring or deferred improvements should happen next.
   - The refactoring document must not claim completion beyond the verification evidence.
   - Update `docs/project-status.md` with the latest task status, verification evidence, deferred work, and links to the plan/refactoring documents.

## TDD Rules

- No production code without a failing test first.
- Write one small behavior test at a time.
- A passing test written before implementation is not proof of the new behavior.
- If the test fails for the wrong reason, fix the test before implementing.
- Green means the targeted test passes with the smallest useful implementation.
- Refactor only after green.
- Tests should describe behavior and requirements, not private implementation details.

## Over-Engineering Policy

- Prefer the smallest design that satisfies the approved scope.
- Do not add abstractions, configuration layers, extension points, or generalized frameworks for hypothetical future needs.
- Do not optimize before there is a current requirement or measured problem.
- If extensibility or maintainability appears to require a larger design, do not implement it immediately unless it is approved for the current task.
- Document deferred work with a Deferred Refactoring Note.

## Deferred Refactoring Note Format

```text
Deferred Refactoring Note

- Topic:
- Why it is not part of the current scope:
- Why it may be needed later:
- Trigger condition:
- Expected change location:
- Related tests:
```

## Review Gate After Each Task

Before starting the next task, confirm:

- The change stayed within the approved scope.
- TDD Red-Green-Refactor order was followed.
- Tests verify behavior rather than implementation details.
- No unnecessary abstraction or broad refactor was introduced.
- Infra, security, reliability, and UX impacts are either addressed or documented.
- Fresh verification was run and the result is reported accurately.
- A refactoring document was written after final review.
- `docs/project-status.md` was updated with the final status and document links.

## Reporting Rules

- Say what was verified and with which command.
- Say what was not verified.
- Do not claim tests, build, lint, or behavior pass without fresh evidence.
- Do not hide deferred work; document it explicitly.
