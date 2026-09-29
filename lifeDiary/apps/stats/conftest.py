from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from statistics import median

import pytest
from django.core.cache import caches
from django.db import connection
from django.test.signals import template_rendered

NANOSECONDS_PER_MILLISECOND = 1_000_000
DISTRIBUTION_FIELDS = ("elapsed_ms", "before_render_ms", "render_ms", "sql_execute_ms")


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
    queries_before_render: int | None
    cache_backend: str


@pytest.fixture
def measure_request():
    return _measure_request


@pytest.fixture
def summarize_samples():
    return _summarize_samples


def _measure_request(client, path: str) -> RequestSample:
    sql_durations_ns = []
    render_starts = []

    # execute 만 잰다. fetch 와 ORM 모델 생성은 래퍼가 끝난 뒤에 일어난다.
    def time_query(execute, sql, params, many, context):
        started_ns = time.perf_counter_ns()
        try:
            return execute(sql, params, many, context)
        finally:
            sql_durations_ns.append(time.perf_counter_ns() - started_ns)

    def mark_render_start(sender, **kwargs):
        render_starts.append((time.perf_counter_ns(), len(sql_durations_ns)))

    template_rendered.connect(mark_render_start)
    try:
        started_ns = time.perf_counter_ns()
        with connection.execute_wrapper(time_query):
            response = client.get(path)
            body = response.content
        finished_ns = time.perf_counter_ns()
    finally:
        template_rendered.disconnect(mark_render_start)

    first_render_ns, queries_before_render = (
        render_starts[0] if render_starts else (None, None)
    )
    return RequestSample(
        status_code=response.status_code,
        response_bytes=len(body),
        query_count=len(sql_durations_ns),
        elapsed_ms=_to_ms(finished_ns - started_ns),
        before_render_ms=_phase_ms(started_ns, first_render_ns),
        render_ms=_phase_ms(first_render_ns, finished_ns),
        sql_execute_ms=_to_ms(sum(sql_durations_ns)),
        database_vendor=connection.vendor,
        queries_before_render=queries_before_render,
        cache_backend=_class_path(caches["default"]),
    )


def _summarize_samples(grouped_samples: dict[str, list[RequestSample]]) -> dict:
    first_sample = next(
        (sample for samples in grouped_samples.values() for sample in samples),
        None,
    )
    if first_sample is None:
        raise ValueError("no samples to summarize")
    return {
        "database_vendor": first_sample.database_vendor,
        "cache_backend": first_sample.cache_backend,
        "groups": {
            label: _summarize_group(samples)
            for label, samples in grouped_samples.items()
        },
    }


def _summarize_group(samples: list[RequestSample]) -> dict:
    distributions = {
        field: _distribution([getattr(sample, field) for sample in samples])
        for field in DISTRIBUTION_FIELDS
    }
    return {
        "samples": [asdict(sample) for sample in samples],
        "query_counts": [sample.query_count for sample in samples],
        **distributions,
    }


def _distribution(values: list[float | None]) -> dict | None:
    measured = [value for value in values if value is not None]
    if not measured:
        return None
    return {"min": min(measured), "median": median(measured), "max": max(measured)}


def _class_path(obj) -> str:
    return f"{type(obj).__module__}.{type(obj).__qualname__}"


def _to_ms(duration_ns: int) -> float:
    return duration_ns / NANOSECONDS_PER_MILLISECOND


def _phase_ms(start_ns: int | None, end_ns: int | None) -> float | None:
    if start_ns is None or end_ns is None:
        return None
    return _to_ms(end_ns - start_ns)
