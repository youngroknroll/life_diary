from datetime import timedelta

from apps.core.utils import (
    DAYS_PER_WEEK,
    MINUTES_PER_HOUR,
    MINUTES_PER_SLOT,
    SLEEP_TAG_NAME,
    TOTAL_SLOTS_PER_DAY,
    UNCLASSIFIED_TAG_NAME,
)
from apps.dashboard.repositories import TimeBlockRepository
from apps.stats.services import minutes_to_hours

_time_block_repo = TimeBlockRepository()


def get_weekly_stats_data(user, selected_date, calculator):
    week_dates = [calculator.start_of_week + timedelta(days=i) for i in range(DAYS_PER_WEEK)]

    all_blocks = _time_block_repo.find_by_date_range(user, calculator.start_of_week, week_dates[-1])
    blocks_by_date = {}
    for block in all_blocks:
        blocks_by_date.setdefault(block.date, []).append(block)

    weekly_data = []
    tag_weekly_stats = {}
    excluded_tags = {SLEEP_TAG_NAME, UNCLASSIFIED_TAG_NAME}

    for date_item in week_dates:
        daily_blocks = blocks_by_date.get(date_item, [])
        daily_tag_stats = {}
        active_blocks_count = 0
        active_minutes = 0

        def process_block(block, tag_info, _date=date_item):
            nonlocal active_blocks_count, active_minutes
            tag_name = tag_info["name"]
            tag_color = tag_info["color"]
            daily_tag_stats[tag_name] = daily_tag_stats.get(tag_name, 0) + MINUTES_PER_SLOT
            if tag_name not in excluded_tags:
                active_blocks_count += 1
                active_minutes += MINUTES_PER_SLOT
            if tag_name not in tag_weekly_stats:
                tag_weekly_stats[tag_name] = {
                    "name": tag_name, "color": tag_color,
                    "daily_minutes": [0] * DAYS_PER_WEEK,
                }
            day_index = (_date - calculator.start_of_week).days
            tag_weekly_stats[tag_name]["daily_minutes"][day_index] += MINUTES_PER_SLOT

        calculator.process_blocks_without_tag(daily_blocks, process_block)
        calculator.fill_empty_slots_weekly(daily_blocks, daily_tag_stats, tag_weekly_stats, date_item)
        weekly_data.append({
            "date": date_item,
            "day_name": date_item.strftime("%a"),
            "day_korean": ["월", "화", "수", "목", "금", "토", "일"][date_item.weekday()],
            "total_blocks": active_blocks_count,
            "total_minutes": active_minutes,
            "total_hours": minutes_to_hours(active_minutes),
            "fill_percentage": round((len(daily_blocks) / TOTAL_SLOTS_PER_DAY) * 100, 1),
            "tag_stats": daily_tag_stats,
        })

    for tag_data in tag_weekly_stats.values():
        tag_data["total_hours"] = minutes_to_hours(sum(tag_data["daily_minutes"]))
        tag_data["daily_hours"] = [minutes_to_hours(m) for m in tag_data["daily_minutes"]]
        active_days = sum(1 for m in tag_data["daily_minutes"] if m > 0)
        tag_data["avg_hours"] = round(tag_data["total_hours"] / active_days, 1) if active_days > 0 else 0

    active_days = sum(1 for day in weekly_data if day["total_blocks"] > 0)
    most_active_day = max(weekly_data, key=lambda d: d["total_minutes"]) if weekly_data else None
    return {
        "start_date": calculator.start_of_week,
        "end_date": week_dates[-1],
        "weekly_data": weekly_data,
        "tag_weekly_stats": list(tag_weekly_stats.values()),
        "week_total_hours": round(
            sum(day["total_minutes"] for day in weekly_data) / MINUTES_PER_HOUR, 1
        ),
        "active_days": active_days,
        "most_active_day": most_active_day,
    }
