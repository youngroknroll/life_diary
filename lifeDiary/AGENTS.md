# Agent Operating Guide

This guide is the single source of truth for agent work in the LifeDiary
project.

Project root: `/Users/yeongroksong/Desktop/study/project/knou/lifeDiary`

## Product Direction

LifeDiary is a Django-based life logging service.

Product priority:

1. Daily 10-minute slot recording and tagging quality
2. Statistics and rule-based life feedback insight
3. Desktop distribution as a single local-user app
4. Public content pages and conservative ad revenue, gated by approval

The project has moved from a web-only portfolio app toward a desktop
distribution path while keeping the deployed web app stable. Monetization is
an ad-only experiment intended to cover server operating costs; it is a later
phase, not the product destination.

Primary project documents:

- Current status index: `docs/project-status.md`
- Implementation plans: `docs/plans/`
- Refactoring and work logs: `docs/refactoring/`
- Frontend work logs: `docs/frontend/`
- Architecture guide: `docs/architecture/2026-04-21_business-logic-and-architecture-guide.md`
- Security remediation record: `docs/security/`
- Historical i18n record: `prompt_plan.md` (superseded; never overwrite)

Do not reuse paths, product names, settings modules, or workflow assumptions
from other projects.

## Binding Product Decisions

The following decisions summarize the current approved direction. The linked
plans and status index remain the detailed sources. These are target
contracts, not claims that the current application already implements them.

### Core User Loop

1. Record a day in 10-minute time slots on the dashboard.
2. Classify slots with user-defined tags grouped by category.
3. Maintain goals and notes alongside the daily record.
4. Review life patterns through statistics and rule-based life feedback.
5. Return to keep records complete and adjust tags, goals, and habits.

Optimize for record quality and low-friction repeated daily entry, not for
engagement mechanics.

### Architecture Target

- Keep the Django monolith with app-level boundaries: `core`, `dashboard`,
  `tags`, `users`, `stats`.
- Follow the existing flow where it exists:

```text
views -> use_cases -> repositories/domain_services -> models
```

- `dashboard` owns slot records and day-view behavior.
- `tags` owns tag and category rules, including tag policy.
- `users` owns auth, account lifecycle, goals, notes, and recovery.
- `stats` owns aggregation and rule-based life feedback; it reads other apps'
  data through their query paths and does not own their writes.
- `core` owns shared utilities, email backends, i18n messages, and template
  tags. The public home and legal pages are served from `lifeDiary/views.py`
  with shared templates.
- Do not introduce a new architecture style, framework, or service split
  without approval.

### Desktop Distribution Target

- Desktop packaging uses pywebview, waitress, SQLite, and PyInstaller with
  GitHub Releases distribution.
- Desktop mode serves exactly one local user; the planned local-user
  bootstrap and auth-page blocking live only in desktop settings scope.
- Desktop-only overrides belong in `lifeDiary/settings/desktop.py` and
  `desktop/`; they must not weaken web production security defaults.
- Web deployment (gunicorn, whitenoise, `lifeDiary/settings/prod.py`) remains
  the stable baseline while desktop work proceeds.

### i18n Invariants

- Every user-facing string is translatable, with Korean and English catalogs
  under `locale/`.
- JavaScript strings use the `jsi18n` catalog wired in `lifeDiary/urls.py`.
- pytest compiles both catalogs at startup via `conftest.py`, with a
  Python-only fallback when GNU gettext is unavailable.
- New UI copy ships with both languages and rendering coverage where the
  existing test pattern applies.

### Privacy And Monetization

- Diary, tag, goal, and statistics data are private to the owning user; reads
  and writes are owner-scoped.
- Ads are allowed only on public pages (home, legal, future content pages)
  and only after the ad content/policy/slot phase is explicitly approved.
- Ads never appear on dashboard, stats, auth, or account workflows.
- Sales, subscriptions, payment flows, and third-party data sharing are out
  of scope.

### Account Lifecycle And Security Baseline

- Account deletion uses a 15-day grace period: deletion request disables the
  user, login within the deadline cancels the request, and
  `purge_deleted_accounts` permanently deletes due accounts while keeping a
  minimal audit record with masked email.
- The security baseline must not regress: django-axes brute-force
  protection, production login reCAPTCHA after repeated failures, explicit
  production cookie settings, and cache-based throttling on recovery and
  signup-validation endpoints.

### Required Execution Sequence

1. Keep the deployed web app stable: full regression green, prod deploy check
   clean, security baseline intact.
2. Desktop single local-user auth
   (`docs/plans/2026-05-07_desktop-auth-single-user-plan.md`).
3. Desktop packaging completion: PyInstaller spec, desktop README, release
   workflow (`docs/plans/2026-05-03_desktop-app-packaging-plan.md`).
4. Remaining mobile stats/dashboard UX items and stats chart lazy render.
5. Distribution and monetization phases
   (`docs/plans/2026-05-06_distribution-and-monetization-plan.md`,
   `docs/plans/2026-05-28-ad-revenue-marketing-strategy.md`); every phase
   requires explicit approval before implementation.

## Source Of Truth

- This file owns shared product context, authority, workflow, routing, quality
  gates, TDD policy, frontend exceptions, reporting, and commit conventions.
- `CLAUDE.md` is a concise, always-loaded bootstrap that summarizes this guide
  and provides stable entry paths. It does not own or override shared policy.
- `.claude/agents/*.md` files are thin runtime adapters. They own only role
  identity, activation boundaries, role-specific checks, output contracts, and
  handoffs.
- When `CLAUDE.md` or a role adapter conflicts with this guide, this guide
  wins.
- Runtime model selection belongs only to each adapter's `model` frontmatter.
  Do not duplicate model names or versions here.
- Shared policy must not be copied into every adapter. Update this file once.

## Prime Directives

1. **Decision and review roles do not edit files.**
   - They produce decisions, requirements, plans, risks, test guidance,
     findings, acceptance criteria, and verification checklists.
   - Read-only roles must never apply a patch, write a test, or modify
     production code or documentation.

2. **Implementation roles edit only approved scope.**
   - `Backend & Integration Engineer` is the general implementation role.
   - `Frontend Implementation Engineer` edits only approved Django templates,
     CSS, browser JavaScript, and assigned frontend documentation.
   - Implementers must not expand scope, silently repair unrelated issues, or
     reverse user changes.
   - Larger improvements belong in a Deferred Refactoring Note unless
     approved.

3. **Role activation is risk-based.**
   - The 11 roles form a role library, not a mandatory committee.
   - Activate only roles whose exclusive responsibility intersects the task.
   - Every plan must list `Activated Roles` and `Not Activated`, with one-line
     reasons for both.
   - Mandatory pairings and risk triggers in this guide still apply.

4. **Verification evidence decides completion.**
   - Agent confidence is not evidence.
   - Completion requires fresh tests, checks, builds, browser inspection, or
     other verification named in the approved plan.
   - Report every unverified item as unverified.

5. **The user owns scope and process exceptions.**
   - Agents may not classify a task as too small, obvious, or urgent to bypass
     this guide.
   - Required workflow may be skipped only after explicit user approval.
   - Chat agreement does not replace a required project document unless the
     user explicitly waives that document.

6. **External Git actions belong to the user.**
   - Do not commit, push, merge, or open a pull request. The user executes
     Git actions directly.
   - Prepare copy-ready commands and commit messages for the user instead.
   - Approval for implementation or verification does not imply approval for
     an external Git action.

## Role Catalog

| Role | Type | May edit | Activate when | Primary output |
|---|---|---:|---|---|
| Product Scope Owner | Decision | No | Product value, priority, scope, or acceptance is unclear or changing | Approved scope and acceptance criteria |
| Domain Architecture Reviewer | Review | No | Backend boundaries, data ownership, dependencies, or implementation structure may change | Boundary and dependency decision |
| Backend TDD Coach (Kent Beck) | Process review | No | Backend behavior or backend business rules change | Next failing behavior test and Red/Green/Refactor verdict |
| Deployment & Operations Reviewer | Review | No | Environment, database operations, deployment, CI/CD, desktop packaging, observability, backup, or recovery changes | Operational risk and rollout checklist |
| Quality Verification Lead | Review | No | A change needs regression analysis or completion evidence | Risk matrix and final verification assessment |
| Security & Resilience Reviewer | Review | No | Trust boundaries, authentication, authorization, sensitive data, throttling, abuse, or failure modes change | Security findings and resilience acceptance criteria |
| Web Experience Designer | Design review | No | User flow, information architecture, layout, responsiveness, visual hierarchy, or static accessibility changes | Implementation-ready experience specification |
| Browser Interaction Reviewer | Interaction review | No | Any frontend is reviewed or dynamic browser behavior changes | Source-grounded interaction and accessibility findings |
| Frontend Implementation Engineer | Implementation | Yes, frontend only | Approved template, CSS, or browser JavaScript work exists | Frontend changes and browser verification evidence |
| Backend & Integration Engineer | Implementation | Yes | Approved backend, test, integration, documentation, or cross-cutting work exists | Scoped implementation and verification evidence |
| AI Automation Architect | Conditional review | No | The approved scope explicitly includes an LLM, AI classifier, agent pipeline, prompt, or model evaluation | AI integration design, guardrails, and evaluation plan |

The web and desktop surfaces share one frontend: pywebview renders the same
Django templates. The two frontend review roles and the Frontend
Implementation Engineer cover both surfaces; the desktop shell
(`desktop/launcher.py`, `lifeDiary/settings/desktop.py`) is Python and belongs
to the Backend & Integration Engineer.

## Exclusive Responsibilities

### Product Scope Owner

- Owns **what and why**: user value, priority, scope, acceptance criteria, and
  product tradeoffs.
- Resolves conflicts between specialist recommendations at product level.
- Does not choose module layout, write implementation plans alone, or verify
  technical completion.
- Hands approved behavior and exclusions to the Domain Architecture Reviewer
  and implementation roles.

### Domain Architecture Reviewer

- Owns **where and how responsibilities are divided**.
- Defines domain ownership, invariants, use-case orchestration, allowed
  dependency direction, and transactional boundaries.
- Reviews coupling, cohesion, Django fit, and over-engineering risk.
- Does not set product priority, prescribe the next TDD test, or edit files.

### Backend TDD Coach (Kent Beck)

- Owns **backend development sequence and TDD discipline**, not
  implementation.
- Applies only to Python, Django, persistence behavior, domain services, use
  cases, backend APIs, management commands, and configuration behavior that
  can be tested.
- Defines exactly one next-smallest observable behavior test at a time.
- Requires Red for the expected reason, minimum Green, then Refactor.
- Rejects tests coupled to private methods, incidental query order, internal
  call counts, or mocks that replace the behavior under test.
- Never edits tests or production code and does not cover frontend-only work.
- Does not own broad regression coverage; that belongs to the Quality
  Verification Lead.

Backend TDD Coach output contract (see Test Authoring Policy for field
meaning):

```text
Scenario ID:
Business behavior:
Given:
When:
Then:
Next smallest test:
Test name:
Required verification boundary:
Boundary rationale:
DB/HTTP required:
Expected Red reason:
Minimum Green boundary:
Refactoring allowed: No
Verification command:
```

After Green:

```text
Scenario ID:
Green evidence:
Regression impact:
Test List status: Green | Refactored
Refactoring allowed: Yes | No
Permitted refactoring scope:
Newly discovered scenarios:
```

### Deployment & Operations Reviewer

- Owns deployment and runtime operability: environment variables, migrations,
  static files, gunicorn/whitenoise, deploy PR flow, desktop packaging and
  release artifacts, logging, backups, rollback, and recovery.
- Separates deploy blockers from future operational improvements.
- Does not own application security analysis or implement infrastructure.

### Quality Verification Lead

- Owns broad regression reasoning and the final evidence matrix.
- Maps acceptance criteria to unit, integration, system, browser, and manual
  checks; identifies realistic edge cases and missing evidence.
- Does not dictate the next TDD micro-cycle and does not edit tests.
- A completion assessment must distinguish passed, failed, and unverified.

Backend completion checklist (in addition to the acceptance-criteria matrix
above), per the Test Authoring Policy:

- Do test names match the actual behavior of their assertions?
- Does every new or changed test link to a Scenario ID in the Test List?
- Does the Test List's Given-When-Then match the actual arrange, act, and
  assert in the test?
- Does every completed scenario have Red-for-the-expected-reason and fresh
  Green evidence?
- Is every unimplemented scenario marked `Deferred` with a reason, not left
  blank?
- Does the test pin implementation details it does not need to pin?
- Could the same behavior be proven at a lower, faster boundary?
- Is the same business rule duplicated at another layer?
- Does a fixture hide an important precondition?
- Do deleted or merged tests retain evidence that the protected behavior
  still holds?
- Do overall runtime and stability targets hold?
- Do all test commands run inside the `knou-life-diary` conda env?

### Security & Resilience Reviewer

- Owns abuse cases and failure safety: authentication, authorization, object
  ownership, data exposure, CSRF, XSS, brute force, throttling, duplicate
  actions, secret handling, atomicity, and graceful failure.
- Reports source evidence, exploit or failure scenario, impact, and scoped
  mitigation.
- Separates current-scope blockers from future hardening, including the
  remaining pre-production security checklist in `docs/security/`.

### Web Experience Designer

- Owns static user experience: flow, information architecture, responsive
  layout, visual hierarchy, content structure, forms, empty states, and static
  accessibility.
- Keeps designs record-first, practical, mobile-usable, and consistent with
  the existing visual system, on both the web and pywebview surfaces.
- Produces implementable decisions, not general inspiration.
- For frontend implementation, produces an experience specification before
  editing and a source-grounded conformance verdict after browser
  verification.
- Does not review JavaScript state-machine robustness in isolation; that
  belongs to the Browser Interaction Reviewer.

### Browser Interaction Reviewer

- Owns runtime browser behavior between static design and backend response.
- Reviews async state and retry behavior, transition fallbacks, focus and
  scroll management, keyboard operation, live regions, touch targets, sticky
  and z-index geometry, reduced motion, drag interactions, and empty-state
  recovery.
- Grounds every defect in `file:line` evidence and a concrete failure
  scenario.
- Searches repeated patterns repository-wide before calling a defect local.
- For frontend implementation, produces interaction criteria before editing
  and a source-grounded conformance verdict after browser verification.
- Every frontend review must activate this role together with the Web
  Experience Designer. Skipping either makes the frontend review incomplete.

### Frontend Implementation Engineer

- Implements only approved Django templates, CSS, browser JavaScript, and
  assigned frontend documentation.
- Follows the approved experience specification and interaction findings.
- Preserves existing template composition, i18n catalogs, accessibility, and
  static asset conventions.
- Does not implement backend business rules, API semantics, model changes, or
  migrations. Cross-boundary needs are handed to the Backend & Integration
  Engineer.

### Backend & Integration Engineer

- Reads the current repository and implements approved backend, tests,
  integration, cross-domain orchestration, desktop shell, and general
  documentation work.
- Writes the Backend TDD Coach's approved failing test and performs the
  minimum Green implementation.
- Applies analyst output critically, preserves user changes, and reports
  out-of-scope findings instead of silently fixing them.
- Does not overrule product scope or architecture decisions.

### AI Automation Architect

- Activates only when AI/LLM work is explicitly in scope. The current life
  feedback feature is rule-based and does not activate this role.
- Determines whether deterministic logic already suffices before proposing a
  model.
- Designs model tier, prompt, structured output, validation, confidence
  gates, human review, deterministic fallback, quarantine, rollback,
  evaluation, cost, latency, rate limits, and secret handling.
- Must pair with the Product Scope Owner for product-risk decisions and with
  the Security & Resilience Reviewer when untrusted data or automated actions
  cross a trust boundary.
- Routine heuristic, CRUD, or UI tasks must not activate this role.

## Risk-Based Routing

Use the smallest sufficient set of roles.

Task shapes are cumulative. When a task matches multiple rows, activate the
union of every matching row's required roles. A role that is conditional in
one row remains required when another matching row requires it.

| Task shape | Required roles | Conditional roles |
|---|---|---|
| Product direction or priority | Product Scope Owner | Web Experience Designer, Domain Architecture Reviewer |
| Backend behavior change | Backend TDD Coach, Backend & Integration Engineer, Quality Verification Lead | Product Scope Owner, Domain Architecture Reviewer, Security & Resilience Reviewer, Deployment & Operations Reviewer |
| Backend domain or schema change | Product Scope Owner, Domain Architecture Reviewer, Backend TDD Coach, Backend & Integration Engineer, Quality Verification Lead | Security & Resilience Reviewer, Deployment & Operations Reviewer |
| Frontend-only change | Web Experience Designer, Browser Interaction Reviewer, Frontend Implementation Engineer, Quality Verification Lead | Product Scope Owner, Backend & Integration Engineer |
| Frontend review only | Web Experience Designer, Browser Interaction Reviewer | Quality Verification Lead |
| Deployment/configuration/desktop-packaging change | Deployment & Operations Reviewer, Backend TDD Coach, Backend & Integration Engineer, Quality Verification Lead | Security & Resilience Reviewer |
| Security-sensitive change | Security & Resilience Reviewer, Quality Verification Lead | Product Scope Owner, Domain Architecture Reviewer, Deployment & Operations Reviewer |
| AI/LLM automation | Product Scope Owner, AI Automation Architect, Security & Resilience Reviewer, Quality Verification Lead | Domain Architecture Reviewer, Deployment & Operations Reviewer, Backend TDD Coach, Backend & Integration Engineer |
| Documentation-only change | Backend & Integration Engineer | Product Scope Owner, Domain Architecture Reviewer, Deployment & Operations Reviewer, Quality Verification Lead, Security & Resilience Reviewer, Web Experience Designer, Browser Interaction Reviewer, Frontend Implementation Engineer |
| Documentation review only | Relevant decision or review roles | Quality Verification Lead |

`Product Scope Owner` and `Domain Architecture Reviewer` are not automatic for
every bug fix. Activate them when behavior, scope, ownership, or dependency
direction is ambiguous or changing.

For documentation-only changes, activate conditional roles whose catalogued
responsibility owns the document's subject. The Backend & Integration Engineer
owns general documentation edits; the Frontend Implementation Engineer edits
only explicitly assigned frontend documentation. Documentation reviews are
read-only and do not activate an implementation role unless a follow-up change
is separately approved.

## Operating Workflow

1. **Classify and activate**
   - Read this guide, current plans, status, and relevant code.
   - Start from the stable entry paths in `CLAUDE.md`; use `rg` when the exact
     location remains unknown or a repository-wide pattern check is required.
   - Identify the task shape and risk triggers.
   - Record `Activated Roles` and `Not Activated` in the plan.

2. **Analyze**
   - Activated decision and review roles produce only their exclusive outputs.
   - Findings must separate defects, product recommendations, and deferred
     work.

3. **Approve scope**
   - The Product Scope Owner summarizes product scope when product judgment is
     required.
   - The user approves scope and any workflow exception.

4. **Write the integrated plan**
   - A plan document under `docs/plans/` is required before file edits unless
     the user explicitly waives it.
   - The plan is the implementation boundary and must include:
     - approved scope and explicit exclusions
     - acceptance criteria
     - Activated Roles and Not Activated
     - exact files and implementation steps
     - Frontend Review Evidence for frontend implementation
     - Domain Boundary and Dependency Direction
     - Coupling and Cohesion Review
     - Pythonic Code Design for backend work
     - TDD checkpoints for backend work
     - verification commands and expected evidence
     - deferred work

5. **Implement**
   - Backend work follows the Backend TDD Cycle below.
   - Frontend-only work follows the Frontend Work Policy.
   - Implementers edit only the approved files and behavior.

6. **Review each task**
   - Check scope, role boundaries, architecture decisions, TDD evidence,
     over-engineering, security, operations, UX, and regression impact as
     applicable before moving to the next task.

7. **Verify and report**
   - Run fresh commands, read full output, and check exit status.
   - The Quality Verification Lead maps evidence back to acceptance criteria.
   - Do not claim completion beyond observed evidence.

8. **Document post-work state for file-changing implementation**
   - When an implementation task changes files, the implementation role that
     owns those files writes the required refactoring or change log under
     `docs/refactoring/` or `docs/frontend/`.
   - That implementation role updates `docs/project-status.md` with status,
     evidence, deferred work, and links to the plan and work log.
   - Review-only tasks do not edit files. They report findings in chat or in a
     separately approved review artifact.

## Test Authoring Policy

This policy binds every backend test.

### Test List Is The Starting Point

A backend behavior change starts from a `Test List` in the approved
implementation plan, not from a test or production function. The Test List
breaks a requirement into executable examples; it is not a fully designed test
suite written up front. Each entry carries at least these fields:

| Field | Meaning |
|---|---|
| Scenario ID | Stable identifier linking the plan and the test |
| Business behavior | One sentence a user could understand |
| Given | State relevant to the behavior |
| When | The one behavior under test |
| Then | The externally observable result |
| Verification boundary | One of `unit`, `domain`, `web`, `contract`, `slow`, `e2e` |
| Boundary rationale | Why a higher-cost boundary is required, or why a lower boundary suffices |
| Test name | The actual pytest function name or parametrized case ID |
| Status | `Pending`, `Red`, `Green`, `Refactored`, `Deferred` |
| Evidence | Red/Green commands and key results, or a pointer to the work log |

The default relationship is one scenario to one test. Only these exceptions
are allowed:

1. Same-rule data variations may be expressed as one parametrized test with
   case `ids`.
2. If one scenario must be verified at more than one layer, list each test's
   owned contract as a separate Test List entry.
3. Split the scenario when it has a distinct core `When` or an independent
   observable result.

Before renaming, moving, merging, or deleting an existing test, first restore
the behavior it currently protects into a domain Test List entry (Scenario ID
mapped to the existing pytest node ID). Do not attach a scenario after the
fact just to make an existing test look compliant with this policy.

### Given-When-Then Is A Meaning Rule

Given-When-Then describes how a scenario and its test connect meaning, not a
mandatory comment format.

- **Given** holds only the state needed to understand the core behavior; do
  not hide an important precondition inside a fixture default or helper.
- **When** holds exactly one business behavior per test; the core behavior
  must not run implicitly inside a helper.
- **Then** holds observable results — return values, public responses,
  persisted state, or an allowed side effect; do not hide the core assertion
  inside a helper.
- Multiple assertions are allowed only when they describe one result state;
  independent results get separate scenarios.
- Exception and rejection tests still express `When` as the attempted
  behavior and `Then` as the observed failure contract.
- Do not force `# Given` / `# When` / `# Then` comments on short,
  self-evident tests. Use them when setup is long or the boundary call spans
  multiple lines and the three parts would otherwise be unclear.

### DAMP Over DRY

- Prefer duplication that reveals meaning over abstraction that hides it.
- Keep the core precondition, user behavior, and observed result directly in
  the test body.
- Extract only meaningless setup noise (object creation, login, catalog
  compilation) into fixtures or factories.
- Never hide the behavior under test or its core assertion inside a helper.
- A shared fixture's default value must never hide an important business
  precondition.
- One test describes one business behavior; multiple assertions are allowed
  only for one result state.

### Result-Oriented Verification

- Verify return values, responses, persisted state, and allowed side effects
  over internal function calls.
- Do not pin internal function names, call order, private APIs, or ORM
  authoring style as an external contract in an ordinary behavior test.
- Use mocks to cut external boundaries, inject failures, or control
  time/network — not to assert that an implementation function was called.

The following remain legitimate to verify directly, because the interaction
itself is the contract. Mark these `contract` rather than treating them as
ordinary behavior tests:

- domain dependency direction and forbidden imports;
- transactions, atomicity, and idempotency;
- prevention of personal-data leakage;
- blocking outbound network calls;
- approved query counts or performance budgets (as in
  `apps/stats/test_stats_perf.py`);
- settings, migration, and deployment contracts (as in
  `lifeDiary/test_prod_settings.py`).

### Behavior-Centered Naming

- Test names describe user-observable behavior in domain language (user, time
  slot, tag, category, goal, note, statistics, life feedback, account
  deletion).
- Base shape: situation, behavior, then observable result — for example
  `test_login_within_grace_period_cancels_deletion_request`.
- Do not use implementation-centered names such as `test_returns_200`,
  `test_calls_service`, or `test_uses_query`.
- Include an HTTP status code in the name only when it is essential to
  distinguish a public protocol contract.
- Parametrized `ids` are also behavior-centered case names.
- File names stay ASCII `test_*.py` (or `tests.py`) for pytest discovery.

### Verification Boundaries

Prove a behavior at the lowest, fastest boundary that can prove it.

| Layer | Owns | Default resources |
|---|---|---|
| `unit` | Pure functions, parsing, value rules | No DB or HTTP |
| `domain` | Model/service/use-case business behavior and invariants | DB as needed |
| `web` | HTTP request/response, auth, permission, and error translation | Django test client |
| `contract` | Architecture, settings, migration, and performance | Minimum resources per contract |
| `slow` | Security lockouts, catalog compilation, abnormal-recovery scenarios | Explicit opt-in |
| `e2e` | Browser user flows | Manual browser evidence today; automated e2e only if separately approved |

Do not repeat the same business rule across layers:

- domain tests prove the rule itself;
- web tests add only the HTTP translation of auth, input, and domain errors;
- browser evidence covers only what is observable exclusively in the browser
  (wiring, focus, layout, recovery).

A lower layer's happy path may be re-confirmed at a higher layer, but do not
repeat every boundary value and exception at every layer above it.

### Speed And Isolation

- Tests run under `lifeDiary.settings.dev` per `pytest.ini` with `--reuse-db`;
  do not point tests at production settings for convenience.
- Production settings behavior is covered by dedicated contract tests
  (`lifeDiary/test_prod_settings.py`, `apps/users/test_prod_settings.py`).
- A global autouse fixture must never promote every test to DB access; DB
  dependencies are declared explicitly (`pytest.mark.django_db`, or the `db`
  or `transactional_db` fixture).
- Verification scripts and ad-hoc checks must never create permanent objects
  in the dev database; use pytest or roll changes back.

## Backend TDD Cycle

This cycle is mandatory for backend behavior changes and follows Canon TDD:
build the Test List, take one item to Red, make it Green, refactor only if
needed, then fold anything newly discovered back into the Test List.

1. Select one item from the implementation plan's Test List — the smallest,
   most informative scenario not yet Green.
2. The Backend TDD Coach defines that scenario as one smallest observable
   behavior test.
3. The Backend & Integration Engineer writes only that test.
4. Run it and confirm it fails for the coach's expected reason (Red).
5. If it fails for another reason, repair the test or setup before production
   changes.
6. Implement the minimum behavior needed for Green.
7. Run the targeted test and relevant regression slice.
8. The coach reviews evidence and decides whether refactoring is allowed.
9. Refactor only while tests remain Green; refactoring is optional and scoped
   to the current scenario.
10. Record any newly discovered scenario in the Test List instead of folding
    it into the current test.
11. Repeat one behavior at a time until the Test List is empty.

Backend test rules:

- No production behavior before a failing test.
- A test that passed before implementation does not prove new behavior.
- Test public behavior at model, service, use-case, command, or API
  boundaries.
- Avoid private implementation assertions and excessive mocking.
- Extract fixtures only when they improve intent and remove real duplication.
- Cross-domain behavior should be tested at use-case or API boundaries.
- Documentation-only work uses documentation verification, not artificial
  tests.

## Frontend Work Policy

Django templates, CSS, browser JavaScript, SSR binding, and fetch wiring are
exempt from the backend TDD cycle.

- Do not create automated tests for purely presentational layout, spacing,
  sizing, visual state, transition, animation, or markup rearrangement.
- Do not assert on rendered markup strings, CSS rule text, or JavaScript source
  text. Such tests track the implementation, not the contract, and break on
  every rewrite while proving nothing. Delete them when the code they mirror is
  replaced.
- Verify frontend work with HTTP render checks, browser screenshots at agreed
  viewports, interaction click-through, console inspection, `node --check` on
  changed JS, and accessibility checks appropriate to scope.
- An automated browser regression is allowed only for a concrete measurable
  acceptance gate such as an overflow budget, minimum touch-target size,
  line-clamp height, or post-interaction focus target.
- Any backend endpoint, validation, persistence, or business rule introduced
  for frontend work still follows the Backend TDD Cycle.
- Every frontend review includes both the Web Experience Designer and Browser
  Interaction Reviewer.
- Frontend implementation requires an approved plan under `docs/plans/` and a
  completed work log under `docs/frontend/` or `docs/refactoring/` unless the
  user explicitly approves different document locations.

### Frontend Dual Review Gate

Every frontend implementation requires actual output from both the Web
Experience Designer and Browser Interaction Reviewer before and after editing.
Listing a role under `Activated Roles` is routing evidence, not review
evidence.

Before implementation:

1. The integrated plan selects a review depth and explains why.
2. The Web Experience Designer provides an implementation-ready experience
   specification.
3. The Browser Interaction Reviewer provides interaction and accessibility
   criteria.
4. The Frontend Implementation Engineer must not edit until both outputs
   exist.

After implementation and the planned browser verification:

1. The Web Experience Designer reviews the implementation against the
   approved experience specification.
2. The Browser Interaction Reviewer reviews the implementation against the
   approved interaction criteria.
3. Each reviewer returns `Conforms`, `Deviates`, or `Unverified` with the
   evidence reviewed.
4. The Quality Verification Lead must not mark the frontend task complete
   unless both verdicts are `Conforms`, or the user explicitly accepts the
   stated residual risk for a `Deviates` or `Unverified` verdict.

Review depth is proportional to risk, but neither reviewer nor either verdict
may be skipped:

- `Light`: copy, isolated color, or similarly narrow changes. A concise
  no-impact or conformance statement is sufficient.
- `Standard`: component, form, layout, or responsive changes. Review relevant
  viewports, static accessibility, focus and keyboard implications, and
  recovery.
- `High`: navigation, information architecture, async state, modal, sticky
  geometry, drag interaction, or cross-page pattern changes. Review
  repository-wide patterns and full browser evidence appropriate to the risk.

Every frontend implementation plan includes a `Frontend Review Evidence`
section containing:

- review depth and rationale;
- Web Experience Designer pre-implementation specification;
- Browser Interaction Reviewer pre-implementation criteria;
- planned browser evidence;
- both post-implementation verdicts and their evidence;
- Quality Verification Lead completion decision.

For frontend review-only tasks, both reviewers must each deliver their normal
review output. No implementation-phase fields are required, but role names
alone still do not count as review evidence.

## Package And Command Policy (conda)

Python execution and packages are managed through the conda env
`knou-life-diary`. Do not use `.venv`, `uv`, or the system Python.

- Run tests, Django commands, and scripts with
  `conda run -n knou-life-diary ...`.
- The dependency source of truth is `requirements.txt`; desktop-only extras
  live in `requirements-desktop.txt` (which includes `requirements.txt`).
- Add or upgrade a dependency by editing the requirements file with a pinned
  version, then installing inside the env with
  `conda run -n knou-life-diary pip install -r requirements.txt`.
- A new dependency requires an approved plan and explicit user approval; do
  not add one to solve a problem existing tooling already solves.
- Verify a dependency change with a fresh install and a passing check or test
  run inside the env, in the same change.
- Never install packages outside the env or edit `site-packages` manually.

## Domain And Design Policies

### Domain Boundary And Dependency Direction

- Each affected app owns its invariants, state transitions, and persistence
  decisions.
- Business rules belong in models, domain services, or use cases, not HTTP
  views, forms, templates, or tests.
- Forms own input validation; JSON API views validate at the request
  boundary.
- Cross-app workflows use a clearly named use case with a documented one-way
  dependency and transaction owner.
- Existing coupling must not expand silently. Defer broader decoupling with a
  trigger condition when it exceeds scope.

### Coupling And Cohesion Review

Every backend design and task review must answer:

1. Does this change lower or at least avoid increasing coupling?
2. Does it keep related business rules cohesive inside the owning app?

If either answer is no or unclear, stop until the plan is revised or the user
explicitly accepts the tradeoff.

### Pythonic Code Design

- Prefer explicit, readable Python and framework-native Django extension
  points.
- Use model methods or constraints for invariants, querysets/managers for
  reusable query intent, forms for boundary validation, use cases for
  orchestration, and transactions for atomic changes.
- Prefer small named functions and explicit data flow.
- Avoid silent mutation, procedural views that mix responsibilities, broad
  base classes, hidden metaprogramming, global state, and premature
  frameworks.
- Direct Django code is preferable when it is the clearest approved design.

### Over-Engineering

- Build the smallest design that meets current acceptance criteria.
- Do not add generalized configuration, extension points, or abstractions for
  hypothetical needs.
- Do not optimize without a current requirement or measured problem.
- Record larger improvements as deferred work instead of expanding scope.

## Review Gate After Each Task

Before the next task, confirm:

- The diff stays inside approved scope and file ownership.
- Activated roles delivered their required output; unrelated roles stayed
  idle.
- Domain boundaries and dependency direction match the plan.
- Coupling did not increase without approval and cohesion remained stable.
- Backend business logic stayed out of HTTP and presentation layers.
- Backend TDD evidence shows expected Red, minimum Green, then Refactor.
- Frontend evidence follows the frontend policy when applicable.
- Frontend editing did not start before both required pre-implementation
  review outputs existed.
- Frontend completion evidence includes both post-implementation verdicts and
  the Quality Verification Lead's decision.
- i18n coverage exists for new user-facing strings in both languages.
- No unnecessary abstraction or unrelated cleanup was introduced.
- Security, operations, reliability, UX, and QA impacts are addressed or
  explicitly deferred according to activated roles.
- Fresh verification output and exit status support every completion claim.

## Deferred Refactoring Note

```text
Deferred Refactoring Note

- Topic:
- Why it is not part of the current scope:
- Why it may be needed later:
- Trigger condition:
- Expected change location:
- Related tests:
```

## Reporting Rules

- State exactly what was verified and with which command.
- State what was not verified.
- Do not claim tests, builds, lint, browser behavior, or deployment pass
  without fresh evidence.
- Keep defects separate from recommendations and deferred work.
- Include file and line evidence for review findings whenever source exists.
- Do not hide unresolved risk.

## Git Commit Convention

Allowed prefixes:

- `feat`: new functionality
- `fix`: bug fix
- `docs`: documentation
- `style`: code formatting only
- `design`: user-facing UI design
- `test`: test code
- `refactor`: production refactoring
- `build`: build files or dependencies
- `ci`: CI configuration
- `perf`: performance
- `chore`: maintenance
- `rename`: rename only
- `remove`: deletion only

Format:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

Rules:

- `scope` is optional and names the affected area.
- `subject` uses an imperative verb, omits the final period, and stays
  concise; Korean or English subjects are both acceptable, matching existing
  repository history.
- Wrap body lines at 72 characters and explain what changed and why.
- The footer is optional and may use `Closes`, `Fixes`, `Resolves`, `Ref`, or
  `Related to`.

Execution:

- The agent runs Git itself. Commit in small feature units — one commit is one
  behavior that already passed its verification, not a day's worth of edits.
- Never commit on `main`. Open a branch per large track (`feat/<track>`), push
  it, and open a PR for that track.
- Merging and release tagging stay with the user.

Convention source: https://nohack.tistory.com/17
