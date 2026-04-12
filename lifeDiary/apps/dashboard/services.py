from apps.core.utils import TOTAL_SLOTS_PER_DAY


SLOT_END_MINUTES = [10, 20, 30, 40, 50, 60]


def build_time_headers(slot_end_minutes=None):
    minutes = slot_end_minutes or SLOT_END_MINUTES
    return [f"{minute}분" for minute in minutes * 2]


def validate_slot_indexes(slot_indexes):
    return isinstance(slot_indexes, list) and all(
        isinstance(slot_index, int) and 0 <= slot_index < TOTAL_SLOTS_PER_DAY
        for slot_index in slot_indexes
    )
