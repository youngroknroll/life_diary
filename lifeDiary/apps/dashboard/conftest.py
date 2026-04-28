from datetime import date as _date

import pytest

from apps.dashboard.models import TimeBlock


@pytest.fixture
def time_block_factory(db):
    def _make(user, tag=None, slot_index=0, on_date=None, memo="", **kwargs):
        return TimeBlock.objects.create(
            user=user,
            date=on_date or _date.today(),
            slot_index=slot_index,
            tag=tag,
            memo=memo,
            **kwargs,
        )

    return _make
