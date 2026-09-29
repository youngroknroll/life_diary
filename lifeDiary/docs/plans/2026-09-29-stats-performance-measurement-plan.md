# Statistics full-request performance measurement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make full `/stats/` test requests report total duration, SQL count and duration, response size, and cold/warm cache distributions without changing production request behavior.

**Architecture:** Add one small measurement helper using `connection.execute_wrapper()` around a supplied Django test-client request. Extend the existing fixed-fixture statistics performance test to request the whole page repeatedly and print structured samples. Record browser measurement conditions and the previously observed live desktop samples in a separate evidence document. All synthetic writes happen inside pytest's test database.

**Tech Stack:** Django 5.2 test client, pytest-django, Python stdlib `time` and `statistics`; no new dependency.

---

## Scope and acceptance

- In scope: authenticated full `/stats/?date=2026-04-15` request, query count, cumulative SQL execution time, whole-request elapsed time, response bytes/status, cold and warm samples, database vendor, reproducible command and evidence document.
- Out of scope: production middleware, live DB writes, PostgreSQL claims from SQLite, automatic browser integration, latency pass/fail threshold, application optimization.
- Success: one command produces at least five successful cold and five successful warm samples with labels and min/median/max. The regular regression test stays deterministic and protects the sample contract. The live browser protocol distinguishes first and repeat loads.

## Activated Roles

- Backend TDD Coach: define the measurement contract test and Red/Green evidence.
- Backend & Integration Engineer: implement test-only measurement helper and evidence.
- Quality Verification Lead: check output and relevant regressions.

## Not Activated

- Product Scope Owner: scope is explicitly selected as performance measurement, without product behavior changes.
- Domain Architecture Reviewer: no domain dependency direction or schema change.
- Security & Resilience Reviewer: synthetic test data and no production endpoint change; privacy rules are listed below.
- Deployment & Operations Reviewer: no deployment or production settings change.
- Web Experience Designer, Browser Interaction Reviewer, Frontend Implementation Engineer: browser behavior is measured, not changed.
- AI Automation Architect: no AI feature change.

## Domain Boundary and Dependency Direction

The helper is only imported by statistics tests. It does not enter views, use cases, or app settings. It calls the test client and observes the DB connection in the same thread. No domain rule or dependency direction changes.

## Coupling and Cohesion Review

The statistics performance test owns the fixture and full-page benchmark. The helper accepts a callable and returns plain measurement data, so it has no knowledge of statistics business rules. Coupling to Django's documented instrumentation hook is limited to the helper.

## Pythonic Code Design

Use a short `RequestSample` dataclass and a scoped SQL wrapper with `perf_counter_ns()`. Keep SQL text, parameters, and user content out of the result. Use `statistics.median()` plus min/max in the reporting test. No general monitoring framework.

## Test List and TDD checkpoints

| ID | Business behavior | Given | When | Then | Boundary | Rationale | Test name | Status |
|---|---|---|---|---|---|---|---|---|
| PERF-01 | A user can measure the complete statistics response | Authenticated user with 2,160 records, cold cache | Request `/stats/` through measurement helper | 200 response; positive response bytes and elapsed time; real query count; SQL time no greater than elapsed time; SQLite label | contract | Full HTTP and DB instrumentation are the contract | `test_full_stats_request_reports_measured_cost` | Pending |
| PERF-02 | Repeated statistics loads show cache state separately | Same user/date, isolated cache keys | Measure five cold and five warm requests | Ten labelled successful samples and warm requests use fewer queries than cold requests | contract | Prevent misleading single-sample and context-only claims | `test_stats_request_benchmark_reports_cold_and_warm_samples` | Pending |
| PERF-03 | A failed page request remains visible in evidence | Anonymous test client | Measure `/stats/` | Status is 302 and sample is retained | web | Failure must not disappear from reported distribution | `test_measurement_retains_redirect_response` | Pending |

## Implementation steps

### Task 1: Measurement helper

**Files:** Create `apps/stats/request_performance.py`; modify `apps/stats/test_stats_perf.py`.

1. Add PERF-01 and PERF-03 tests importing `measure_request(client, path)` and assert observable response/measurement fields. Run each with `conda run -n knou-life-diary python -m pytest apps/stats/test_stats_perf.py::<name> -q -o cache_dir=/tmp/lifediary-pytest-cache`; expect import failure for the missing helper (Red).
2. Implement `RequestSample(status_code, response_bytes, elapsed_ms, query_count, sql_ms, database_vendor)` and `measure_request()`. Time `client.get()` and `response.content`; wrap the database connection only for that call. Record no SQL strings or parameters.
3. Run targeted tests; expect pass (Green). Run the existing four statistics performance tests.

### Task 2: Cold/warm full-request report

**Files:** Modify `apps/stats/test_stats_perf.py`.

1. Add PERF-02 using the existing `seeded_user` fixture, `client.force_login(user)`, and `invalidate_stats_cache(user.id, today)`. Run targeted test; expect failure until the report helper is present or its contract is fulfilled (Red).
2. Add `summarize_samples()` to `apps/stats/request_performance.py`. Report five cold and five warm samples as JSON with database vendor, raw samples, min/median/max for elapsed and SQL time, and query counts. Assert all status 200 and warm query count lower than cold. Do not assert milliseconds.
3. Run targeted and full `apps/stats/test_stats_perf.py` tests. Capture the report with `-s` and verify `sqlite` is explicit.

### Task 3: Browser protocol and evidence

**Files:** Create `docs/refactoring/2026-09-29-stats-performance-measurement.md`; modify `docs/project-status.md`.

1. Record browser setup: authenticated test account, Chromium version, 1365×900 desktop viewport, network mode, navigation method, cache state, and at least five attempts for future comparisons. Explain that current earlier three-sample desktop results are exploratory and the isolated 3.83-second first load is one observation.
2. Record backend command and exact observed cold/warm samples. State that the test database is SQLite and does not measure production PostgreSQL or network transfer.
3. Run `conda run -n knou-life-diary python -m pytest apps/stats/test_stats_perf.py -v -o cache_dir=/tmp/lifediary-pytest-cache`, `conda run -n knou-life-diary python manage.py check`, and `git diff --check`. Report every unverified item.

## Privacy and safety

No credentials in repository files or command examples. No SQL text/parameters in report. The browser test account is used only for read-only navigation. All synthetic records are written by pytest, not the development or production database.

## Deferred work

A disposable PostgreSQL test instance can establish database-specific timing. A larger mobile browser sample can establish a separate rendering distribution. Any optimization follows those measurements and receives its own plan.
