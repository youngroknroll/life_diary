---
paths:
  - "apps/**/test_*.py"
  - "apps/**/tests.py"
  - "apps/**/conftest.py"
  - "lifeDiary/test_*.py"
  - "conftest.py"
  - "scripts/test_*.py"
---

# Backend Test Authoring Policy

This file is the Test Authoring Policy section of `AGENTS.md`, loaded by
itself whenever a backend test file is read or edited. It carries that
guide's authority; if the two ever disagree, `AGENTS.md` wins. The Backend
TDD Cycle, role contracts, and the Test List fields stay in `AGENTS.md`.

This policy binds every backend test.

### Test List Is The Starting Point

A backend behavior change starts from a `Test List` in the approved
implementation plan, not from a test or production function. The Test List
breaks a requirement into executable examples; it is not a fully designed test
suite written up front. Each entry carries the fields defined in `AGENTS.md`
(Test Authoring Policy).

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
  slot, tag, category, goal, note, statistics, account
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

