"""통계 집계가 요청당 기록을 한 번만 읽어도 결과가 같은지."""

from datetime import date, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.dashboard.repositories import TimeBlockRepository
from apps.stats.aggregation.calculator import StatsCalculator
from apps.tags.models import Category, Tag
from apps.users.models import UserGoal


RECORDS_START = date(2026, 1, 5)
RECORDS_END = date(2026, 8, 31)
MID_MONTH = date(2026, 4, 15)
# 4/13(4/15 의 주 시작) 12주 전부터 4월 끝까지.
MID_MONTH_WINDOW = (date(2026, 1, 19), date(2026, 4, 30))


@pytest.fixture
def owner(make_user):
    return make_user(username="window_owner")


@pytest.fixture
def recorded(owner, make_user):
    """두 사용자가 같은 날짜에 기록한다. 주인의 기록에는 미분류 칸과 빈 날이 섞인다."""
    focus = Tag.objects.create(
        user=owner, name="집중", color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )
    chores = Tag.objects.create(
        user=owner, name="집안일", color="#C99A2E",
        category=Category.objects.get(slug="basic_life"),
    )
    other = make_user(username="window_other")
    others_focus = Tag.objects.create(
        user=other, name="집중", color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )

    blocks = []
    day = RECORDS_START
    while day <= RECORDS_END:
        seed = day.toordinal()
        if seed % 9:
            for n in range(seed % 7 + 3):
                tag = None if n == 0 else (focus if n % 2 else chores)
                blocks.append(
                    TimeBlock(user=owner, date=day, slot_index=(seed * 5 + n * 11) % 144, tag=tag)
                )
            blocks.append(
                TimeBlock(user=other, date=day, slot_index=(seed * 3) % 144, tag=others_focus)
            )
        day += timedelta(days=1)
    TimeBlock.objects.bulk_create(blocks)

    UserGoal.objects.create(user=owner, tag=focus, period="daily", target_hours=1.0)
    UserGoal.objects.create(user=owner, tag=chores, period="weekly", target_hours=5.0)
    UserGoal.objects.create(user=owner, tag=focus, period="monthly", target_hours=20.0)
    return owner


def _block_ids(blocks):
    return [(block.date, block.slot_index, block.tag_id) for block in blocks]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "start, end",
    [
        (MID_MONTH, MID_MONTH),
        (date(2026, 4, 13), date(2026, 4, 19)),
        (date(2026, 4, 1), date(2026, 4, 30)),
        (date(2026, 3, 1), date(2026, 3, 31)),
        (date(2026, 1, 19), date(2026, 4, 12)),
        (date(2026, 4, 9), MID_MONTH),
    ],
    ids=["day", "week", "month", "previous_month", "baseline_weeks", "last_seven_days"],
)
def test_window_returns_the_same_blocks_in_the_same_order_as_direct_reads(
    recorded, start, end
):
    calculator = StatsCalculator(recorded, MID_MONTH, window=MID_MONTH_WINDOW)

    blocks = calculator.blocks_between(start, end)

    direct = TimeBlockRepository().find_by_date_range(recorded, start, end)
    assert _block_ids(blocks) == _block_ids(direct)
