from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext
from django.views.decorators.http import require_GET

from apps.core.utils import safe_date_parse
from .use_cases import ExportMonthlyWorkbookUseCase, GetStatsContextUseCase

_get_stats_context = GetStatsContextUseCase()
_export_workbook = ExportMonthlyWorkbookUseCase()

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@login_required
def index(request):
    selected_date = safe_date_parse(request.GET.get("date"))
    context = _get_stats_context.execute(request.user, selected_date)
    # 날짜로 넘겨야 템플릿이 YEAR_MONTH_FORMAT 으로 지역화할 수 있다.
    context["export_months"] = [
        date(year, month, 1)
        for year, month in _export_workbook.available_months(request.user)
    ]
    context["export_selected_month"] = selected_date.strftime("%Y-%m")
    return render(request, "stats/index.html", context)


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
