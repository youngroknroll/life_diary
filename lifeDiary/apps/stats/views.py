import time
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import date
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext
from django.views.decorators.http import require_GET

from apps.core.utils import safe_date_parse
from .aggregation.goal_progress import with_deadline_states
from .use_cases import ExportMonthlyWorkbookUseCase, GetStatsContextUseCase

_get_stats_context = GetStatsContextUseCase()
_export_workbook = ExportMonthlyWorkbookUseCase()

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
NANOSECONDS_PER_MILLISECOND = 1_000_000


@dataclass(frozen=True)
class _StatsTiming:
    context_ns: int
    execute_ns: int
    query_count: int


class _QueryTimer:
    def __init__(self):
        self.query_count = 0
        self.execute_ns = 0

    def __call__(self, execute, sql, params, many, context):
        started_ns = time.perf_counter_ns()
        try:
            return execute(sql, params, many, context)
        finally:
            self.execute_ns += time.perf_counter_ns() - started_ns
            self.query_count += 1


@login_required
def index(request):
    selected_date = safe_date_parse(request.GET.get("date"))
    result, timing = _timed_stats_context(request.user, selected_date)
    context = result.context
    context["goal_progress_rows"] = with_deadline_states(
        context["goal_progress_rows"], timezone.localdate()
    )
    # 날짜로 넘겨야 템플릿이 YEAR_MONTH_FORMAT 으로 지역화할 수 있다.
    context["export_months"] = [
        date(year, month, 1)
        for year, month in _export_workbook.available_months(request.user)
    ]
    context["export_selected_month"] = selected_date.strftime("%Y-%m")
    response = render(request, "stats/index.html", context)
    if timing is not None:
        response["Server-Timing"] = _server_timing_header(result.cache_hit, timing)
    return response


def _timed_stats_context(user, selected_date):
    if not getattr(settings, "STATS_SERVER_TIMING_ENABLED", False):
        return _get_stats_context.execute(user, selected_date), None
    timer = _QueryTimer()
    measurement = ExitStack()
    try:
        measurement.enter_context(connection.execute_wrapper(timer))
    except Exception:
        # 계측은 진단용이다. 계측을 못 해도 통계 화면은 보여야 한다.
        return _get_stats_context.execute(user, selected_date), None
    started_ns = time.perf_counter_ns()
    with measurement:
        result = _get_stats_context.execute(user, selected_date)
    timing = _StatsTiming(
        context_ns=time.perf_counter_ns() - started_ns,
        execute_ns=timer.execute_ns,
        query_count=timer.query_count,
    )
    return result, timing


def _server_timing_header(cache_hit: bool, timing: _StatsTiming) -> str:
    cache_state = "hit" if cache_hit else "miss"
    return (
        f'cache;desc="{cache_state}", '
        f"ctx;dur={_ms(timing.context_ns)}, "
        f"db;dur={_ms(timing.execute_ns)}, "
        f'db-count;desc="{timing.query_count} queries"'
    )


def _ms(duration_ns: int) -> str:
    return f"{duration_ns / NANOSECONDS_PER_MILLISECOND:.1f}"


@login_required
@require_GET
def export(request):
    """고른 달을 엑셀로 내려준다.

    화면의 목록은 기록이 있는 달만 담으므로 정상 흐름에서는 거절에 닿지
    않는다. 주소를 직접 고친 요청만 여기서 막힌다.
    """
    try:
        year, month = _parse_month(request.GET.get("month"))
        book, filename = _export_workbook.execute(request.user, year, month)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("stats:index")

    stream = BytesIO()
    book.save(stream)
    response = HttpResponse(stream.getvalue(), content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _parse_month(raw):
    """`2026-08` 만 받는다."""
    if not raw:
        raise ValueError(gettext("내보낼 달을 지정해주세요."))
    parts = raw.split("-")
    if len(parts) != 2:
        raise ValueError(gettext("올바른 달이 아닙니다."))
    try:
        year, month = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(gettext("올바른 달이 아닙니다."))
    if not 1 <= month <= 12:
        raise ValueError(gettext("올바른 달이 아닙니다."))
    return year, month
