"""실행취소 스냅샷 보관소 — TTL과 1회 사용 규칙.

세션에 값을 담지만 만료 판정과 소비 규칙 자체는 시간을 주입받는 순수 로직이라
DB 없이 증명한다. 토큰은 발급된 스냅샷에만 대응하므로, 뒤이은 저장이 앞선
토큰을 조용히 무효화하지 않는다.
"""

from datetime import datetime, timedelta, timezone

from apps.dashboard.undo import (
    MAX_PENDING_SNAPSHOTS,
    UNDO_TTL_SECONDS,
    pop_snapshot,
    save_snapshot,
)


NOW = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)


def snapshot(target_date="2026-08-01", slots=None):
    return {
        "date": target_date,
        "slots": slots if slots is not None else [{"slot_index": 54, "tag_id": None, "memo": ""}],
    }


def test_saving_returns_a_token():
    session = {}

    token = save_snapshot(session, snapshot(), now=NOW)

    assert token


def test_each_save_gets_a_distinct_token():
    session = {}

    first = save_snapshot(session, snapshot(), now=NOW)
    second = save_snapshot(session, snapshot(), now=NOW)

    assert first != second


def test_popping_returns_the_snapshot_that_was_saved():
    session = {}
    token = save_snapshot(session, snapshot(target_date="2026-07-30"), now=NOW)

    restored = pop_snapshot(session, token, now=NOW)

    assert restored["date"] == "2026-07-30"


def test_a_token_can_only_be_popped_once():
    session = {}
    token = save_snapshot(session, snapshot(), now=NOW)

    pop_snapshot(session, token, now=NOW)

    assert pop_snapshot(session, token, now=NOW) is None


def test_unknown_token_returns_nothing():
    session = {}
    save_snapshot(session, snapshot(), now=NOW)

    assert pop_snapshot(session, "누가봐도-아닌-토큰", now=NOW) is None


def test_popping_from_an_untouched_session_returns_nothing():
    assert pop_snapshot({}, "무엇이든", now=NOW) is None


def test_token_still_works_at_the_last_moment_before_expiry():
    session = {}
    token = save_snapshot(session, snapshot(), now=NOW)

    just_in_time = NOW + timedelta(seconds=UNDO_TTL_SECONDS - 1)

    assert pop_snapshot(session, token, now=just_in_time) is not None


def test_token_expires_after_the_ttl():
    session = {}
    token = save_snapshot(session, snapshot(), now=NOW)

    too_late = NOW + timedelta(seconds=UNDO_TTL_SECONDS + 1)

    assert pop_snapshot(session, token, now=too_late) is None


def test_a_later_save_does_not_invalidate_an_earlier_token():
    """탭을 두 개 열어 각각 저장해도 앞선 되돌리기가 살아 있어야 한다."""
    session = {}
    first = save_snapshot(session, snapshot(target_date="2026-07-30"), now=NOW)
    save_snapshot(session, snapshot(target_date="2026-07-31"), now=NOW)

    restored = pop_snapshot(session, first, now=NOW)

    assert restored["date"] == "2026-07-30"


def test_oldest_snapshots_are_evicted_beyond_the_cap():
    """세션이 무한히 불어나지 않도록 보관 개수를 제한한다."""
    session = {}
    tokens = [
        save_snapshot(session, snapshot(), now=NOW + timedelta(seconds=index))
        for index in range(MAX_PENDING_SNAPSHOTS + 1)
    ]

    assert pop_snapshot(session, tokens[0], now=NOW) is None
    assert pop_snapshot(session, tokens[-1], now=NOW) is not None


def test_expired_entries_are_swept_on_save():
    session = {}
    stale = save_snapshot(session, snapshot(), now=NOW)

    save_snapshot(session, snapshot(), now=NOW + timedelta(seconds=UNDO_TTL_SECONDS + 1))

    assert len(session["dashboard_undo"]) == 1
    assert pop_snapshot(session, stale, now=NOW) is None
