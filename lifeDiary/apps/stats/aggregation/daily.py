from apps.core.utils import (
    HOURS_PER_DAY,
    MINUTES_PER_SLOT,
    SLOTS_PER_HOUR,
    TOTAL_SLOTS_PER_DAY,
    UNCLASSIFIED_TAG_NAME,
)
from apps.dashboard.repositories import TimeBlockRepository
from apps.stats.services import minutes_to_hours

_time_block_repo = TimeBlockRepository()


def get_daily_stats_data(user, selected_date, calculator):
    time_blocks = _time_block_repo.find_by_date(user, selected_date)
    tag_stats = {}
    hourly_stats = [{} for _ in range(HOURS_PER_DAY)]
    active_blocks_count = 0

    def process_block(block, tag_info):
        nonlocal active_blocks_count
        tag_name = tag_info["name"]
        tag_color = tag_info["color"]
        if tag_name not in tag_stats:
            tag_stats[tag_name] = {"name": tag_name, "color": tag_color, "minutes": 0, "blocks": 0}
        tag_stats[tag_name]["minutes"] += MINUTES_PER_SLOT
        tag_stats[tag_name]["blocks"] += 1
        if tag_name != UNCLASSIFIED_TAG_NAME:
            active_blocks_count += 1
        hour = block.slot_index // SLOTS_PER_HOUR
        hourly_stats[hour][tag_name] = hourly_stats[hour].get(tag_name, 0) + MINUTES_PER_SLOT

    calculator.process_blocks_without_tag(time_blocks, process_block)
    calculator.fill_empty_slots_daily(time_blocks, tag_stats, hourly_stats)
    for tag_data in tag_stats.values():
        tag_data["hours"] = minutes_to_hours(tag_data["minutes"])

    peak_hour, max_minutes = -1, -1
    for hour, hour_data in enumerate(hourly_stats):
        total = sum(hour_data.values())
        if total > max_minutes:
            max_minutes = total
            peak_hour = hour

    sorted_tags = sorted(tag_stats.values(), key=lambda x: x["minutes"], reverse=True)
    return {
        "date": selected_date,
        "tag_stats": sorted_tags,
        "hourly_stats": hourly_stats,
        "total_blocks": TOTAL_SLOTS_PER_DAY,
        "total_hours": float(HOURS_PER_DAY),
        "active_hours": minutes_to_hours(active_blocks_count * MINUTES_PER_SLOT),
        "fill_percentage": round((len(time_blocks) / TOTAL_SLOTS_PER_DAY) * 100, 1),
        "peak_hour": peak_hour,
        "max_minutes": max_minutes,
        "top_tag": sorted_tags[0] if sorted_tags else None,
    }
