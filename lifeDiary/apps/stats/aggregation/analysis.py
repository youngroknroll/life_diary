from apps.core.utils import MINUTES_PER_SLOT
from apps.stats.services import minutes_to_hours


def get_tag_analysis_data(user, selected_date, calculator):
    monthly_blocks = calculator.get_monthly_blocks()
    tag_analysis_data = {}

    def process_block(block, tag_info):
        key = tag_info["key"]
        if key not in tag_analysis_data:
            tag_analysis_data[key] = {
                "key": key,
                "tag_id": tag_info["tag_id"],
                "name": tag_info["name"],
                "color": tag_info["color"],
                "total_minutes": 0,
                "total_blocks": 0,
            }
        tag_analysis_data[key]["total_minutes"] += MINUTES_PER_SLOT
        tag_analysis_data[key]["total_blocks"] += 1

    calculator.process_blocks_without_tag(monthly_blocks, process_block)
    calculator.fill_empty_slots_analysis(user, tag_analysis_data)

    analysis_list = [
        {
            "key": d["key"],
            "tag_id": d["tag_id"],
            "name": d["name"],
            "color": d["color"],
            "total_hours": minutes_to_hours(d["total_minutes"]),
            "total_blocks": d["total_blocks"],
        }
        for d in tag_analysis_data.values()
        if not d.get("is_unclassified")
    ]
    return sorted(analysis_list, key=lambda x: x["total_hours"], reverse=True)
