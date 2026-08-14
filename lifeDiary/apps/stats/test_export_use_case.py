"""내보내기 유스케이스 — 어떤 달을 고를 수 있고, 무엇을 거절하는가."""

from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.use_cases import ExportMonthlyWorkbookUseCase
from apps.tags.models import Category, Tag


@pytest.fixture
def use_case():
    return ExportMonthlyWorkbookUseCase()


@pytest.fixture
def user(make_user):
    return make_user(username="exportcaseuser")


@pytest.fixture
def focus(user):
    return Tag.objects.create(
        user=user, name="집중", category=Category.objects.get(slug="investment")
    )


def record(user, tag, on_date, slots=1, first_slot=0):
    for offset in range(slots):
        TimeBlock.objects.create(
            user=user, date=on_date, slot_index=first_slot + offset, tag=tag
        )


class TestAvailableMonths:
    def test_only_months_that_have_records(self, use_case, user, focus):
        record(user, focus, date(2026, 6, 10))
        record(user, focus, date(2026, 8, 5))

        assert use_case.available_months(user) == [(2026, 8), (2026, 6)]

    def test_newest_first(self, use_case, user, focus):
        for month in (5, 7, 6):
            record(user, focus, date(2026, month, 3))

        assert use_case.available_months(user) == [(2026, 7), (2026, 6), (2026, 5)]

    def test_a_month_appears_once_however_many_days(self, use_case, user, focus):
        record(user, focus, date(2026, 8, 1))
        record(user, focus, date(2026, 8, 2), first_slot=10)
        record(user, focus, date(2026, 8, 3), first_slot=20)

        assert use_case.available_months(user) == [(2026, 8)]

    def test_another_users_months_do_not_leak(self, use_case, user, focus, make_user):
        stranger = make_user(username="exportstranger")
        stranger_tag = Tag.objects.create(
            user=stranger, name="남의것",
            category=Category.objects.get(slug="passive"),
        )
        record(stranger, stranger_tag, date(2026, 7, 1))
        record(user, focus, date(2026, 8, 5))

        assert use_case.available_months(user) == [(2026, 8)]

    def test_no_records_means_no_months(self, use_case, user):
        assert use_case.available_months(user) == []


class TestExecute:
    def test_returns_a_workbook_and_a_filename(self, use_case, user, focus):
        record(user, focus, date(2026, 8, 5))

        book, filename = use_case.execute(user, 2026, 8)

        assert book.sheetnames == ["2026-08"]
        assert filename == "lifediary-2026-08.xlsx"

    def test_refuses_a_month_without_records(self, use_case, user, focus):
        """목록에 없는 달을 주소로 직접 요청한 경우. 빈 파일을 주지 않는다."""
        record(user, focus, date(2026, 8, 5))

        with pytest.raises(ValueError):
            use_case.execute(user, 2026, 7)

    def test_refuses_a_month_that_only_another_user_recorded(
        self, use_case, user, focus, make_user
    ):
        stranger = make_user(username="exportstranger2")
        stranger_tag = Tag.objects.create(
            user=stranger, name="남의것",
            category=Category.objects.get(slug="passive"),
        )
        record(stranger, stranger_tag, date(2026, 7, 1))
        record(user, focus, date(2026, 8, 5))

        with pytest.raises(ValueError):
            use_case.execute(user, 2026, 7)

    def test_refuses_an_impossible_month(self, use_case, user, focus):
        record(user, focus, date(2026, 8, 5))

        with pytest.raises(ValueError):
            use_case.execute(user, 2026, 13)
