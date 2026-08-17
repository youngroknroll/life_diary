from django.db.models import Count

from .models import TimeBlock


class TimeBlockRepository:
    """TimeBlock ORM 쿼리 전담. 다른 레이어는 DB를 직접 보지 않는다."""

    def find_by_date(self, user, date):
        """카테고리까지 함께 가져온다 — stats.daily가 카테고리 단위로 묶는다
        (find_by_date_range와 같은 이유). 이 메서드는 dashboard 화면·API도
        공유하므로 find_by_date_range와 달리 필드를 .only()로 제한하지
        않는다."""
        return TimeBlock.objects.filter(user=user, date=date).select_related(
            "tag", "tag__category"
        )

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
        """카테고리까지 함께 가져온다 — stats.monthly/analysis가 카테고리
        단위로 묶는다(find_by_date_range와 같은 이유)."""
        return (
            TimeBlock.objects.filter(user=user, date__range=[start, end])
            .select_related("tag", "tag__category")
            .only(
                "date",
                "slot_index",
                "tag__id",
                "tag__name",
                "tag__color",
                "tag__category__slug",
                "tag__category__name",
                "tag__category__color",
            )
        )

    def build(self, user, target_date, slot_index, tag, memo):
        return TimeBlock(user=user, date=target_date, slot_index=slot_index, tag=tag, memo=memo)

    def find_by_date_range(self, user, start, end):
        """날짜 범위 단일 쿼리 조회.

        카테고리까지 함께 가져온다 — 통계가 카테고리 단위로 묶으므로
        빼면 태그마다 조회가 한 번씩 더 난다.
        """
        return (
            TimeBlock.objects.filter(user=user, date__range=[start, end])
            .select_related("tag", "tag__category")
            .only(
                "date",
                "slot_index",
                "tag__id",
                "tag__name",
                "tag__color",
                "tag__category__slug",
                "tag__category__name",
                "tag__category__color",
            )
        )

    def bulk_create(self, blocks):
        TimeBlock.objects.bulk_create(blocks)

    def bulk_update(self, blocks, fields):
        TimeBlock.objects.bulk_update(blocks, fields)

    def snapshot_slots(self, user, date, slot_indexes):
        """없는 슬롯도 tag_id=None 으로 자리를 채운다."""
        stored = {
            block.slot_index: block
            for block in TimeBlock.objects.filter(
                user=user, date=date, slot_index__in=slot_indexes
            )
        }
        return [
            {
                "slot_index": slot_index,
                "tag_id": stored[slot_index].tag_id if slot_index in stored else None,
                "memo": stored[slot_index].memo if slot_index in stored else "",
            }
            for slot_index in slot_indexes
        ]

    def delete_by_slots(self, user, date, slot_indexes):
        deleted_count, _ = TimeBlock.objects.filter(
            user=user, date=date, slot_index__in=slot_indexes
        ).delete()
        return deleted_count

    def find_recorded_months(self, user):
        return (
            TimeBlock.objects.filter(user=user)
            .dates("date", "month", order="DESC")
        )

    def count_blocks_by_tag(self, user) -> dict:
        """{태그 id: 블록 수}. 태그마다 조회하면 N+1 이 된다."""
        return dict(
            TimeBlock.objects.filter(user=user, tag__isnull=False)
            .values_list("tag_id")
            .annotate(count=Count("id"))
            .values_list("tag_id", "count")
        )

    def move_blocks_to_tag(self, source_tag, destination_tag) -> int:
        return TimeBlock.objects.filter(tag=source_tag).update(tag=destination_tag)

    def is_tag_in_use(self, tag):
        return TimeBlock.objects.filter(tag=tag).exists()
