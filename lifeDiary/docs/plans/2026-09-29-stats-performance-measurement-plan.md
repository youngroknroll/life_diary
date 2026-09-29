# Statistics full-request performance measurement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make full `/stats/` test requests report total duration, before-render and render phase duration, query count, SQL execute time, response size, and cold/warm cache distributions without changing production request behavior.

**Architecture:** Add one small measurement helper using `connection.execute_wrapper()` and the `template_rendered` test signal around a supplied Django test-client request. Extend the existing fixed-fixture statistics performance test to request the whole page repeatedly under a `LocMemCache` override, after one separately labelled warm-up request, and print structured samples. Record browser measurement conditions and the previously observed live desktop samples in a separate evidence document. All synthetic writes happen inside pytest's test database.

**Tech Stack:** Django 5.2 test client, pytest-django, Python stdlib `time` and `statistics`; no new dependency.

---

## Scope and acceptance

- In scope: authenticated full `/stats/?date=2026-04-15` request, query count, SQL execute time (`cursor.execute()` only), whole-request elapsed time, before-render and render phase time, response bytes/status, one warm-up sample, cold and warm samples under `LocMemCache`, database vendor, cache backend, reproducible command and evidence document.
- Out of scope: production middleware, live DB writes, PostgreSQL claims from SQLite, database-cost share claims from SQL execute time, automatic browser integration, latency pass/fail threshold, application optimization.
- Success: one command produces one labelled warm-up sample and at least five successful cold and five successful warm samples with labels and min/median/max. The regular regression test stays deterministic and protects the sample contract. The live browser protocol distinguishes first and repeat loads.

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

The statistics performance test owns the fixture and full-page benchmark. The helper accepts a callable and returns plain measurement data, so it has no knowledge of statistics business rules. Coupling to Django's documented instrumentation hooks (`execute_wrapper`, `template_rendered`) is limited to the helper.

## Pythonic Code Design

Use a short `RequestSample` dataclass, a scoped SQL wrapper, and a scoped `template_rendered` receiver, all timed with `perf_counter_ns()`. Keep SQL text, parameters, and user content out of the result. Use `statistics.median()` plus min/max in the reporting test. No general monitoring framework.

## Test List and TDD checkpoints

Rows are in execution order, smallest scenario first; Scenario IDs are unchanged. The Backend TDD Coach reviewed this list on 2026-09-29 and approved the order and each expected Red reason. No TDD waiver is requested: the full Red-Green-Refactor cycle applies to every row.

| ID | Business behavior | Given | When | Then | Boundary | Rationale | Test name | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| PERF-03 | A failed page request remains visible in evidence | Anonymous test client | Measure `/stats/?date=2026-04-15` once | Sample keeps status 302 with zero response bytes and zero queries | contract | Instrumenting a non-200 outcome needs a real test-client round trip | `test_measurement_retains_redirect_response` | Pending | Pending; work log |
| PERF-01 | A user can measure the complete statistics response | Authenticated user with 2,160 records; default test cache (`DummyCache`, always a miss) | Measure `/stats/?date=2026-04-15` once | 200 response; positive response bytes; query count above zero; SQL execute time, before-render time, and render time each present and no greater than elapsed time; vendor equals `connection.vendor` | contract | Full HTTP, DB, and render instrumentation are the contract | `test_full_stats_request_reports_measured_cost` | Pending | Pending; work log |
| PERF-02 | Repeated statistics loads show cache state separately | Same user/date; test body overrides `settings.CACHES` to `LocMemCache` and clears it; one warm-up request sent and labelled first | Measure five cycles of invalidate, cold request, warm request, then summarize | Ten successful samples; every warm query count is lower than every cold query count; summary names database vendor and cache backend | contract | Cache-dependent query cost needs a real cache backend and real queries | `test_stats_request_benchmark_reports_cold_and_warm_samples` | Pending | Pending; work log |

### Backend TDD Coach output: next test (condensed)

```text
Scenario ID: PERF-03
Business behavior: A failed/redirected statistics request still appears in the measured evidence, not silently dropped.
Given: Anonymous (unauthenticated) Django test client.
When: measure_request(client, "/stats/?date=2026-04-15") is called once.
Then: The returned sample reports status_code == 302, response_bytes == 0, query_count == 0.
Next smallest test: test_measurement_retains_redirect_response (apps/stats/test_stats_perf.py), importing measure_request inside the test body.
Test name: test_measurement_retains_redirect_response
Required verification boundary: contract
Boundary rationale: HTTP+DB instrumentation of a non-200 outcome is the interaction under test and cannot be proven without a real Django test-client round trip.
DB/HTTP required: HTTP (Django test client GET, no login); DB only through connection wrapping, expected to record 0 queries.
Expected Red reason: ModuleNotFoundError raised by the in-body import because apps/stats/request_performance.py does not exist yet.
Minimum Green boundary: RequestSample carrying status_code, response_bytes, query_count, and measure_request(client, path) that performs client.get(path) and counts queries for that call. No timing, phase, vendor, or cache fields yet.
Refactoring allowed: No
Verification command: conda run -n knou-life-diary pytest apps/stats/test_stats_perf.py::test_measurement_retains_redirect_response --tb=short
```

## Implementation steps

Take one scenario at a time. Import the helper inside the test body until that scenario is Green, so the four existing tests in the file keep collecting during Red. Hoist the import to module level only in a Refactor step the Backend TDD Coach permits. Run each targeted test with `conda run -n knou-life-diary python -m pytest apps/stats/test_stats_perf.py::<name> -q -o cache_dir=/tmp/lifediary-pytest-cache`.

### Task 1: Measurement helper

**Files:** Create `apps/stats/request_performance.py`; modify `apps/stats/test_stats_perf.py`.

1. PERF-03 Red: add only `test_measurement_retains_redirect_response`. Expected Red reason: `ModuleNotFoundError` from the in-body import of `apps.stats.request_performance`. Confirm the four existing tests still pass.
2. PERF-03 Green: create `RequestSample(status_code, response_bytes, query_count)` and `measure_request(client, path)`. Call `client.get()`, read `response.content`, and wrap the database connection only for that call. Add no timing, phase, or vendor field yet.
3. PERF-01 Red: add only `test_full_stats_request_reports_measured_cost`. Expected Red reason: `AttributeError` naming a field PERF-03's Green did not add. Quote the attribute name from the traceback in the evidence.
4. PERF-01 Green: extend `RequestSample` with `elapsed_ms, before_render_ms, render_ms, sql_execute_ms, database_vendor`. Time the call, time `cursor.execute()` inside the existing wrapper, connect a `template_rendered` receiver for that call only, and read `connection.vendor`. Phase fields are `None` when no template rendered. Record no SQL strings or parameters.
5. Run both targeted tests; expect pass. Run the existing four statistics performance tests.

### Task 2: Cold/warm full-request report

**Files:** Modify `apps/stats/test_stats_perf.py`; modify `apps/stats/request_performance.py`.

1. PERF-02 Red: add only `test_stats_request_benchmark_reports_cold_and_warm_samples` using the existing `seeded_user` fixture and `client.force_login(user)`. In the test body override `settings.CACHES` to `LocMemCache`, call `cache.clear()`, send one warm-up request, then run five cycles of `invalidate_stats_cache(user.id, today)`, cold request, warm request. Expected Red reason: `ImportError` from the in-body import of `summarize_samples`. The cache override is present from the first run, so Red cannot come from `DummyCache`.
2. PERF-02 Green: add `summarize_samples()` to `apps/stats/request_performance.py`. Report the warm-up sample under its own label, outside both distributions, and five cold and five warm samples as JSON with database vendor, cache backend, raw samples, min/median/max for elapsed, before-render, render, and SQL execute time, and query counts. Assert all ten status 200 and every warm query count lower than every cold query count. Do not assert milliseconds. Clear the cache when the test ends.
3. Run targeted and full `apps/stats/test_stats_perf.py` tests. Capture the report with `-s` and verify the database vendor and cache backend are explicit.

### Task 3: Browser protocol and evidence

**Files:** Create `docs/refactoring/2026-09-29-stats-performance-measurement.md`; modify `docs/project-status.md`.

1. Record browser setup: authenticated test account, Chromium version, 1365×900 desktop viewport, network mode, navigation method, cache state, and at least five attempts for future comparisons. Explain that current earlier three-sample desktop results are exploratory and the isolated 3.83-second first load is one observation.
2. Record backend command and exact observed warm-up, cold, and warm samples. State that the test database is SQLite and does not measure production PostgreSQL or network transfer, and that SQL execute time excludes row fetch and ORM model construction.
3. Run `conda run -n knou-life-diary python -m pytest apps/stats/test_stats_perf.py -v -o cache_dir=/tmp/lifediary-pytest-cache`, `conda run -n knou-life-diary python manage.py check`, and `git diff --check`. Report every unverified item.

## Privacy and safety

No credentials in repository files or command examples. No SQL text/parameters in report. The browser test account is used only for read-only navigation. All synthetic records are written by pytest, not the development or production database.

## Deferred work

A disposable PostgreSQL test instance can establish database-specific timing. Separating row fetch and ORM model construction from Python aggregation inside the before-render phase needs its own instrumentation; the 2026-09-29 probe counted 23,774 model instances per cache-miss request. A larger mobile browser sample can establish a separate rendering distribution. Any optimization follows those measurements and receives its own plan.
