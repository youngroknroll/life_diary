# Statistics performance measurement design

## Decision

Use a pytest-isolated, full-request Django test-client benchmark and a repeatable browser measurement protocol. This gives portfolio evidence without production logging or a new dependency. Alternatives considered: production middleware adds ongoing privacy and deployment scope; browser-only timing cannot separate SQL from application work.

## Backend flow

Seed one user with the existing 30-day, 2,160-block, 5-tag fixture. Authenticate the test client and time the complete `GET /stats/?date=2026-04-15` call. Scope `connection.execute_wrapper()` to each request to record query count and cumulative SQL execution time. Repeat cache-miss and cache-hit requests separately. Report status, response bytes, database vendor, total duration, SQL duration, and each sample plus median/min/max. Do not impose unstable latency thresholds in ordinary tests.

## Browser flow

Use the provided test account with a fixed browser version, viewport, network setting, URL, and locale. Repeat each page load at least five times, capturing TTFB, LCP, CLS, and failures. Record first load separately from later loads. Mobile and desktop samples are distinct. The prior mobile-home Lighthouse value cannot be compared with authenticated desktop pages.

## Safety and boundaries

Only pytest's disposable database receives synthetic records. SQLite output is labelled SQLite; PostgreSQL requires a separately configured disposable test database. Never print SQL parameters, diary text, credentials, or cookies. Browser measurements are read-only. No production middleware, persistent metrics, schema change, or new dependency.

## Verification

Test the measurement helper with a full authenticated request, a real SQL query, and a failing response. Run the benchmark and existing statistics performance tests. Save commands, raw samples, and limitations in the work log.
