from datetime import timedelta

from apps.core.utils import (
    HOURS_PER_DAY,
    MINUTES_PER_HOUR,
    MINUTES_PER_SLOT,
    TOTAL_SLOTS_PER_DAY,
    UNCLASSIFIED_TAG_NAME,
    get_month_date_range,
    get_week_date_range,
)
from apps.dashboard.repositories import TimeBlockRepository
from apps.stats.services import (
    build_unclassified_analysis_entry,
    build_unclassified_daily_entry,
    build_unclassified_monthly_entry,
    build_unclassified_weekly_entry,
)

_time_block_repo = TimeBlockRepository()


class StatsCalculator:
    def __init__(self, user, selected_date):
        self.user = user
        self.selected_date = selected_date
        self.start_of_month, self.end_of_month = get_month_date_range(selected_date)
        self.start_of_week, self.end_of_week = get_week_date_range(selected_date)
        self._monthly_blocks = None
        self._monthly_daily_counts = None

    def get_monthly_blocks(self):
        """월간 TimeBlock을 1회 fetch 후 캐시. monthly + analysis가 공유."""
        if self._monthly_blocks is None:
            self._monthly_blocks = list(
                _time_block_repo.find_by_month(self.user, self.start_of_month, self.end_of_month)
            )
        return self._monthly_blocks

    def get_monthly_daily_counts(self):
        """월간 날짜별 블록 개수를 1회 fetch 후 캐시. monthly + analysis가 공유."""
        if self._monthly_daily_counts is None:
            self._monthly_daily_counts = _time_block_repo.find_daily_counts(
                self.user, self.start_of_month, self.end_of_month
            )
        return self._monthly_daily_counts

    def get_tag_info(self, block):
        if block.tag and block.tag.name:
            return {"name": block.tag.name, "color": block.tag.color or "#808080"}
        return None

    def process_blocks_without_tag(self, blocks, process_func):
        for block in blocks:
            tag_info = self.get_tag_info(block)
            if tag_info:
                process_func(block, tag_info)

    def calculate_empty_slots(self, recorded_blocks_count):
        empty_blocks = TOTAL_SLOTS_PER_DAY - recorded_blocks_count
        return empty_blocks * MINUTES_PER_SLOT

    def add_unclassified_data(self, data_container, empty_minutes, day_index=None, data_type="daily"):
        if empty_minutes <= 0:
            return
        if data_type == "daily":
            if UNCLASSIFIED_TAG_NAME not in data_container:
                data_container[UNCLASSIFIED_TAG_NAME] = build_unclassified_daily_entry()
            data_container[UNCLASSIFIED_TAG_NAME]["minutes"] += empty_minutes
            data_container[UNCLASSIFIED_TAG_NAME]["blocks"] += empty_minutes // MINUTES_PER_SLOT
        elif data_type == "weekly":
            if UNCLASSIFIED_TAG_NAME not in data_container:
                data_container[UNCLASSIFIED_TAG_NAME] = build_unclassified_weekly_entry()
            data_container[UNCLASSIFIED_TAG_NAME]["daily_minutes"][day_index] += empty_minutes
        elif data_type == "monthly":
            pass
        elif data_type == "analysis":
            if UNCLASSIFIED_TAG_NAME not in data_container:
                data_container[UNCLASSIFIED_TAG_NAME] = build_unclassified_analysis_entry()
            data_container[UNCLASSIFIED_TAG_NAME]["total_minutes"] += empty_minutes
            data_container[UNCLASSIFIED_TAG_NAME]["total_blocks"] += empty_minutes // MINUTES_PER_SLOT

    def add_unclassified_to_hourly_stats(self, hourly_stats, hour, empty_minutes):
        if empty_minutes > 0:
            hourly_stats[hour][UNCLASSIFIED_TAG_NAME] = (
                hourly_stats[hour].get(UNCLASSIFIED_TAG_NAME, 0) + empty_minutes
            )

    def fill_empty_slots_daily(self, time_blocks, tag_stats, hourly_stats):
        for hour in range(HOURS_PER_DAY):
            total_minutes_in_hour = sum(hourly_stats[hour].values())
            empty_minutes = MINUTES_PER_HOUR - total_minutes_in_hour
            if empty_minutes > 0:
                self.add_unclassified_data(tag_stats, empty_minutes, data_type="daily")
                self.add_unclassified_to_hourly_stats(hourly_stats, hour, empty_minutes)

    def fill_empty_slots_weekly(self, daily_blocks, daily_tag_stats, tag_weekly_stats, date_item):
        recorded_blocks = len(daily_blocks)
        empty_minutes = (TOTAL_SLOTS_PER_DAY - recorded_blocks) * MINUTES_PER_SLOT
        if empty_minutes > 0:
            self.add_unclassified_data(daily_tag_stats, empty_minutes, data_type="daily")
            day_index = (date_item - self.start_of_week).days
            self.add_unclassified_data(tag_weekly_stats, empty_minutes, day_index, data_type="weekly")

    def fill_empty_slots_monthly(self, user, daily_tag_stats, daily_totals, total_days):
        daily_counts = self.get_monthly_daily_counts()
        for day_index in range(total_days):
            current_date = self.start_of_month + timedelta(days=day_index)
            recorded_blocks = daily_counts.get(current_date, 0)
            empty_blocks = TOTAL_SLOTS_PER_DAY - recorded_blocks
            if empty_blocks > 0:
                empty_hours = empty_blocks * MINUTES_PER_SLOT / MINUTES_PER_HOUR
                if UNCLASSIFIED_TAG_NAME not in daily_tag_stats:
                    daily_tag_stats[UNCLASSIFIED_TAG_NAME] = build_unclassified_monthly_entry(total_days)
                daily_tag_stats[UNCLASSIFIED_TAG_NAME]["daily_hours"][day_index] += empty_hours
                daily_tag_stats[UNCLASSIFIED_TAG_NAME]["total_hours"] += empty_hours
                daily_totals[day_index] += empty_hours

    def fill_empty_slots_analysis(self, user, tag_analysis_data):
        total_days = (self.end_of_month - self.start_of_month).days + 1
        daily_counts = self.get_monthly_daily_counts()
        for day_index in range(total_days):
            current_date = self.start_of_month + timedelta(days=day_index)
            recorded_blocks = daily_counts.get(current_date, 0)
            empty_blocks = TOTAL_SLOTS_PER_DAY - recorded_blocks
            if empty_blocks > 0:
                empty_minutes = empty_blocks * MINUTES_PER_SLOT
                self.add_unclassified_data(tag_analysis_data, empty_minutes, data_type="analysis")
