from __future__ import annotations

import time
from dataclasses import dataclass

from django.db import connection
from django.test.signals import template_rendered

NANOSECONDS_PER_MILLISECOND = 1_000_000


@dataclass(frozen=True)
class RequestSample:
    status_code: int
    response_bytes: int
    query_count: int
    elapsed_ms: float
    before_render_ms: float | None
    render_ms: float | None
    sql_execute_ms: float
    database_vendor: str


def measure_request(client, path: str) -> RequestSample:
    sql_durations_ns = []
    render_starts_ns = []

    # execute 만 잰다. fetch 와 ORM 모델 생성은 래퍼가 끝난 뒤에 일어난다.
    def time_query(execute, sql, params, many, context):
        started_ns = time.perf_counter_ns()
        try:
            return execute(sql, params, many, context)
        finally:
            sql_durations_ns.append(time.perf_counter_ns() - started_ns)

    def mark_render_start(sender, **kwargs):
        render_starts_ns.append(time.perf_counter_ns())

    template_rendered.connect(mark_render_start)
    try:
        started_ns = time.perf_counter_ns()
        with connection.execute_wrapper(time_query):
            response = client.get(path)
            body = response.content
        finished_ns = time.perf_counter_ns()
    finally:
        template_rendered.disconnect(mark_render_start)

    first_render_ns = render_starts_ns[0] if render_starts_ns else None
    return RequestSample(
        status_code=response.status_code,
        response_bytes=len(body),
        query_count=len(sql_durations_ns),
        elapsed_ms=_to_ms(finished_ns - started_ns),
        before_render_ms=_phase_ms(started_ns, first_render_ns),
        render_ms=_phase_ms(first_render_ns, finished_ns),
        sql_execute_ms=_to_ms(sum(sql_durations_ns)),
        database_vendor=connection.vendor,
    )


def _to_ms(duration_ns: int) -> float:
    return duration_ns / NANOSECONDS_PER_MILLISECOND


def _phase_ms(start_ns: int | None, end_ns: int | None) -> float | None:
    if start_ns is None or end_ns is None:
        return None
    return _to_ms(end_ns - start_ns)
