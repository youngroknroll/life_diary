from django.db.models import Count

from .models import TimeBlock


class TimeBlockRepository:
    """TimeBlock ORM 쿼리 전담. 다른 레이어는 DB를 직접 보지 않는다."""

    def find_by_date(self, user, date):
        return TimeBlock.objects.filter(user=user, date=date).select_related("tag")

    def find_by_slots(self, user, date, slot_indexes):
        return TimeBlock.objects.filter(
            user=user, date=date, slot_index__in=slot_indexes
        )

    def find_daily_counts(self, user, start, end):
        """날짜별 기록 블록 수 반환 {date: count}"""
        return dict(
            TimeBlock.objects.filter(user=user, date__range=[start, end])
            .values_list("date")
            .annotate(cnt=Count("id"))
            .values_list("date", "cnt")
        )

    def find_by_month(self, user, start, end):
        return (
            TimeBlock.objects.filter(user=user, date__range=[start, end])
            .select_related("tag")
            .only("date", "slot_index", "tag__id", "tag__name", "tag__color")
        )

    def build(self, user, target_date, slot_index, tag, memo):
        return TimeBlock(user=user, date=target_date, slot_index=slot_index, tag=tag, memo=memo)

    def find_by_date_range(self, user, start, end):
        """날짜 범위 단일 쿼리 조회 — 주간 통계 최적화용"""
        return (
            TimeBlock.objects.filter(user=user, date__range=[start, end])
            .select_related("tag")
            .only("date", "slot_index", "tag__id", "tag__name", "tag__color")
        )

    def bulk_create(self, blocks):
        TimeBlock.objects.bulk_create(blocks)

    def bulk_update(self, blocks, fields):
        TimeBlock.objects.bulk_update(blocks, fields)

    def delete_by_slots(self, user, date, slot_indexes):
        deleted_count, _ = TimeBlock.objects.filter(
            user=user, date=date, slot_index__in=slot_indexes
        ).delete()
        return deleted_count

    def is_tag_in_use(self, tag):
        return TimeBlock.objects.filter(tag=tag).exists()
