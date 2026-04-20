from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT, UNCLASSIFIED_TAG_NAME
from apps.dashboard.repositories import TimeBlockRepository

_time_block_repo = TimeBlockRepository()


def get_monthly_stats_data(user, selected_date, calculator):
    monthly_blocks = _time_block_repo.find_by_month(
        user, calculator.start_of_month, calculator.end_of_month
    )
    total_days = (calculator.end_of_month - calculator.start_of_month).days + 1
    daily_tag_stats = {}
    daily_totals = [0] * total_days

    def process_block(block, tag_info):
        tag_name = tag_info["name"]
        tag_color = tag_info["color"]
        day_index = (block.date - calculator.start_of_month).days
        if tag_name not in daily_tag_stats:
            daily_tag_stats[tag_name] = {
                "name": tag_name, "color": tag_color,
                "daily_hours": [0] * total_days, "total_hours": 0,
            }
        hours_inc = MINUTES_PER_SLOT / MINUTES_PER_HOUR
        daily_tag_stats[tag_name]["daily_hours"][day_index] += hours_inc
        daily_tag_stats[tag_name]["total_hours"] += hours_inc
        daily_totals[day_index] += hours_inc

    calculator.process_blocks_without_tag(monthly_blocks, process_block)
    calculator.fill_empty_slots_monthly(user, daily_tag_stats, daily_totals, total_days)

    for tag_data in daily_tag_stats.values():
        tag_data["daily_hours"] = [round(h, 1) for h in tag_data["daily_hours"]]
        tag_data["total_hours"] = round(tag_data["total_hours"], 1)
        active_days = sum(1 for h in tag_data["daily_hours"] if h > 0)
        tag_data["avg_hours"] = round(tag_data["total_hours"] / active_days, 1) if active_days > 0 else 0

    daily_totals = [round(h, 1) for h in daily_totals]
    tag_list = sorted(daily_tag_stats.values(), key=lambda x: x["total_hours"], reverse=True)
    tag_list = [t for t in tag_list if t["name"] != UNCLASSIFIED_TAG_NAME]

    total_hours = sum(t["total_hours"] for t in tag_list)
    active_days = sum(
        1 for i in range(total_days)
        if sum(t["daily_hours"][i] for t in tag_list) > 0
    )
    return {
        "month": selected_date.strftime("%Y-%m"),
        "start_date": calculator.start_of_month,
        "end_date": calculator.end_of_month,
        "day_labels": [f"{i+1}일" for i in range(total_days)],
        "tag_stats": tag_list,
        "daily_totals": daily_totals,
        "total_hours": round(total_hours, 1),
        "active_days": active_days,
        "total_days": total_days,
        "avg_daily_hours": round(total_hours / total_days, 1) if total_days > 0 else 0,
    }
