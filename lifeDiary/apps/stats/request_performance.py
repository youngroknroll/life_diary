from __future__ import annotations

from dataclasses import dataclass

from django.db import connection


@dataclass(frozen=True)
class RequestSample:
    status_code: int
    response_bytes: int
    query_count: int


def measure_request(client, path: str) -> RequestSample:
    executed = []

    def record_query(execute, sql, params, many, context):
        executed.append(1)
        return execute(sql, params, many, context)

    with connection.execute_wrapper(record_query):
        response = client.get(path)
        body = response.content

    return RequestSample(
        status_code=response.status_code,
        response_bytes=len(body),
        query_count=len(executed),
    )
