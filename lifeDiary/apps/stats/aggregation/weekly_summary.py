"""주차별 요약 — 월 집계에서 파생한다.

시안 3d의 마지막 표. 월 탭은 태그 합계 대신 이 표를 둔다. 이미 계산된
`daily_totals`와 태그별 `daily_hours`를 다시 묶기만 하므로 추가 조회가 없다.

주는 달력 주(월~일)다. 롤링 7일을 쓰는 시안과 갈리는 지점이며,
`docs/refactoring/2026-08-01_p0-sian-redesign.md`의 승인된 이탈을 따른다.
"""

from datetime import timedelta

MONDAY = 0


def _week_spans(start_date, total_days):
    """달의 각 날을 달력 주로 묶고, 달 경계에서 자른다."""
    spans = []
    index = 0
    while index < total_days:
        day = start_date + timedelta(days=index)
        remaining_in_week = 7 - ((day.weekday() - MONDAY) % 7)
        length = min(remaining_in_week, total_days - index)
        spans.append((index, length))
        index += length
    return spans


def _sum_slice(values, offset, length):
    return round(float(sum(values[offset:offset + length])), 1)


def _tagged_daily_hours(tag_stats, total_days):
    """`daily_totals` 는 미분류 채움을 포함해 하루가 늘 24h 다.

    기록 열은 태그가 붙은 시간만 세야 한다. 아니면 아직 오지 않은 주까지
    24h 기록으로 보고된다.
    """
    totals = [0.0] * total_days
    for tag in tag_stats:
        if tag.get("is_unclassified"):
            continue
        for index, hours in enumerate(tag.get("daily_hours") or []):
            totals[index] += hours
    return totals


def _top_tag(tag_stats):
    """기록이 0인 달에도 태그가 있으면 열을 유지한다. 열이 사라졌다 나타나면
    표의 모양이 달마다 달라진다."""
    ranked = [t for t in tag_stats if not t.get("is_unclassified")]
    if not ranked:
        return None
    return max(ranked, key=lambda t: t.get("total_hours") or 0)


def build_weekly_summary(monthly_stats, today=None):
    start_date = monthly_stats["start_date"]
    total_days = monthly_stats["total_days"]
    tag_stats = monthly_stats.get("tag_stats") or []
    daily_totals = _tagged_daily_hours(tag_stats, total_days)
    top_tag = _top_tag(tag_stats)

    rows = []
    previous_focus = None
    for offset, length in _week_spans(start_date, total_days):
        week_start = start_date + timedelta(days=offset)
        week_end = week_start + timedelta(days=length - 1)
        hours = _sum_slice(daily_totals, offset, length)

        focus_hours = None
        if top_tag:
            focus_hours = _sum_slice(top_tag["daily_hours"], offset, length)

        delta = None
        if focus_hours is not None and previous_focus is not None:
            delta = round(focus_hours - previous_focus, 1)

        rows.append(
            {
                "start": week_start,
                "end": week_end,
                "days": length,
                "is_partial": length < 7,
                "hours": hours,
                "avg_hours": round(hours / length, 1) if length else 0.0,
                "top_tag_name": top_tag["name"] if top_tag else None,
                "top_tag_hours": focus_hours,
                "delta": delta,
                "in_progress": bool(today and week_start <= today <= week_end),
            }
        )
        previous_focus = focus_hours

    return rows
