# Statistics performance measurement design

## Decision

Use a pytest-isolated, full-request Django test-client benchmark and a repeatable browser measurement protocol. This gives portfolio evidence without production logging or a new dependency. Alternatives considered: production middleware adds ongoing privacy and deployment scope; browser-only timing cannot separate SQL from application work.

## Backend flow

Seed one user with the existing 30-day, 2,160-block, 5-tag fixture. Authenticate the test client and time the complete `GET /stats/?date=2026-04-15` call. Scope `connection.execute_wrapper()` to each request to record query count and SQL execute time.

SQL execute time covers `cursor.execute()` only. Row fetch and ORM model construction run after the wrapper returns, so the report never presents SQL execute time as the total database cost or as a share of the request. Split each request at the first `template_rendered` test signal into a before-render phase (middleware, authentication, view, context build, data access) and a render phase. A response that renders no template has no phase split.

The project `conftest.py` forces `DummyCache` on every test, so a cache hit cannot occur by default. The benchmark test replaces it with `LocMemCache` in the test body and clears it before and after. The first request in a process pays import and template compilation cost, so send one warm-up request and report it under its own label, outside both distributions. Then repeat five times: invalidate the statistics cache, measure the cache-miss request, measure the cache-hit request.

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
