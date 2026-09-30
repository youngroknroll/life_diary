# Statistics performance measurement design

## Decision

Use a pytest-isolated, full-request Django test-client benchmark and a repeatable browser measurement protocol. This gives portfolio evidence without production logging or a new dependency. Alternatives considered: production middleware adds ongoing privacy and deployment scope; browser-only timing cannot separate SQL from application work.

## Backend flow

Seed one user with the existing 30-day, 2,160-block, 5-tag fixture. Authenticate the test client and time the complete `GET /stats/?date=2026-04-15` call. Scope `connection.execute_wrapper()` to each request to record query count and SQL execute time. The helpers are pytest fixtures in `apps/stats/conftest.py`, so they exist only inside the test environment that emits `template_rendered`.

SQL execute time is the time spent inside `cursor.execute()`. Its meaning depends on the database driver, so compare it only within one vendor and never present it as the total database cost or as a share of the request:

- SQLite: preparing the statement and producing the first row, plus any sort or aggregate that must finish first. The remaining rows are produced during fetch, outside the measurement.
- PostgreSQL with client-side cursors (the Django default): server execution plus transfer of every row, because `execute()` waits for the complete result.
- PostgreSQL server-side cursors (`QuerySet.iterator()`): only the `DECLARE` is measured. Later fetches bypass the wrapper and are neither counted nor timed. The application does not use `.iterator()` today.

ORM model construction always runs after `execute()` returns, on every vendor.

Split each request at the first `template_rendered` test signal:

- Before-render: request-side middleware, authentication, the view, context build and data access, context processors, and loading the top-level template.
- Render: template rendering including `{% extends %}` and `{% include %}` loading, then response-side middleware and test-client bookkeeping. In a probe the part after the top-level render was about 0.3 ms.

A response that renders no template has no phase split. Record how many queries ran before the first signal, so the split point is checked without relying on timing.

The project `conftest.py` forces `DummyCache` on every test, so a cache hit cannot occur by default. The benchmark test replaces it with `LocMemCache` in the test body and clears it before and after, including when a request raises. It also sets `DEBUG = False` in the body to match production; the shared fixture turns `DEBUG` on, which routes queries through the debug cursor wrapper. Each sample records the cache backend that actually served it. The first request in a process pays import and template compilation cost, so send one warm-up request and report it under its own label, outside both distributions. Then repeat five times: invalidate the statistics cache, measure the cache-miss request, measure the cache-hit request.

Report status, response bytes, database vendor, cache backend, total duration, before-render and render duration, SQL execute duration, query count, and each sample plus median/min/max. Do not impose unstable latency thresholds in ordinary tests.

## Browser flow

Use the provided test account with a fixed browser version, viewport, network setting, URL, and locale. Repeat each page load at least five times, capturing TTFB, LCP, CLS, and failures. Record first load separately from later loads. Mobile and desktop samples are distinct. The prior mobile-home Lighthouse value cannot be compared with authenticated desktop pages.

## Safety and boundaries

Only pytest's disposable database receives synthetic records. SQLite output is labelled SQLite; PostgreSQL requires a separately configured disposable test database. Never print SQL parameters, diary text, credentials, or cookies. Browser measurements are read-only. No production middleware, persistent metrics, schema change, or new dependency.

## Verification

Test the measurement helper with a failing response, a full authenticated request with real SQL, and a cold/warm benchmark under a real cache backend. Take one scenario at a time in the order the plan's Test List fixes. Run the benchmark and existing statistics performance tests. Save commands, raw samples, and limitations in the work log.

## Review findings (2026-09-29)

A scratch probe outside the repository ran this design against pytest's disposable in-memory SQLite database before implementation. The values are exploratory and are superseded by the evidence Task 3 records.

| Observation | Value |
|---|---|
| Default `DummyCache`, six consecutive requests | 21 queries every time; cache hit never occurs |
| `LocMemCache` cache miss | 21 queries, about 300-330 ms median |
| `LocMemCache` cache hit | 3 queries, about 17-18 ms median |
| First request in the process | 496-797 ms |
| Cache-miss phases | before-render 302-388 ms, render about 9 ms |
| Cache-miss SQL execute time | about 8 ms |
| ORM model instances built per cache-miss request | 23,774 (profiler count) |

These findings changed the design in three places: the cache backend override, the warm-up sample, and the SQL execute label with the phase split.

## Re-review findings (2026-09-30)

After implementation, a Domain Architecture Reviewer, a Quality Verification Lead, and an adversarial reviewer re-reviewed the track. The user approved these changes:

- The helpers moved from `apps/stats/request_performance.py`, a production-shaped module that shipped in the deploy tree and desktop build, into fixtures in `apps/stats/conftest.py`. This also removes the path where a call outside the test environment silently reported no render phases.
- SQL execute time wording now states the per-vendor meaning.
- The phase contents now list context processors and response-side middleware.
- The split point is checked by counting queries before the first render signal. The original assertions could not detect zero SQL time or swapped phases.
- An empty report is rejected with `ValueError`.
- The cache backend is recorded from the backend in use, not passed in.
- The benchmark runs with `DEBUG = False` and cleans its cache in `finally`.

Limits that still apply to every backend number:

- `LocMemCache` is in-process; production and desktop use `FileBasedCache` on disk.
- The dev middleware stack has no CSP middleware, and axes is disabled in tests.
- The test client bypasses the WSGI server and the network.
