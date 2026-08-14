"""저장·삭제 응답과 되돌리기 엔드포인트의 HTTP 계약."""

import json
from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.tags.models import Category, Tag


API_URL = "/api/time-blocks/"
UNDO_URL = "/api/time-blocks/undo/"
TODAY = date(2026, 8, 1)


@pytest.fixture
def logged_in(client, make_user):
    user = make_user(username="undouser")
    client.force_login(user)
    focus = Tag.objects.create(
        user=user,
        name="집중",
        color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )
    leisure = Tag.objects.create(
        user=user,
        name="여가",
        color="#C1715A",
        category=Category.objects.get(slug="passive"),
    )
    return client, user, focus, leisure


def save(client, tag, slot_indexes, memo=""):
    return client.post(
        API_URL,
        data=json.dumps(
            {
                "date": TODAY.isoformat(),
                "slot_indexes": slot_indexes,
                "tag_id": tag.id,
                "memo": memo,
            }
        ),
        content_type="application/json",
    )


def undo(client, token, **extra):
    return client.post(
        UNDO_URL,
        data=json.dumps({"undo_token": token, **extra}),
        content_type="application/json",
    )


def tag_ids_by_slot(user, on_date=TODAY):
    return {
        block.slot_index: block.tag_id
        for block in TimeBlock.objects.filter(user=user, date=on_date)
    }


@pytest.mark.django_db
class TestSaveResponse:
    def test_save_hands_back_an_undo_token(self, logged_in):
        client, _, focus, _ = logged_in

        assert save(client, focus, [54, 55, 56]).json()["undo_token"]

    def test_save_returns_the_touched_row_with_its_neighbours(self, logged_in):
        """이웃 시간도 함께 준다. 라벨이 그쪽으로 옮겨갈 수 있어서다."""
        client, _, focus, _ = logged_in

        payload = save(client, focus, [54, 55, 56]).json()

        assert [row["hour"] for row in payload["runs"]] == [8, 9, 10]

    def test_returned_runs_serialize_the_tag(self, logged_in):
        client, _, focus, _ = logged_in

        rows = save(client, focus, [54]).json()["runs"]
        runs = next(row for row in rows if row["hour"] == 9)["runs"]
        filled = next(run for run in runs if run["tag_id"] is not None)

        assert filled["tag_id"] == focus.id
        assert filled["tag_name"] == "집중"
        assert filled["color"] == Category.objects.get(slug="investment").color

    def test_save_moves_label_into_a_newly_touched_adjacent_hour(self, logged_in):
        """06:00–06:50 을 먼저 저장하면 라벨은 6시 행에 있다. 이어서 05:40–05:50 을
        같은 태그로 저장하면 구간 시작이 5시로 옮겨가므로, 응답은 5시에 이름을
        싣고 6시의 옛 이름을 지운 상태로 와야 한다.
        """
        client, _, focus, _ = logged_in
        save(client, focus, [36, 37, 38, 39, 40, 41])

        rows = save(client, focus, [34, 35]).json()["runs"]

        by_hour = {row["hour"]: row["runs"] for row in rows}
        assert by_hour[5][-1]["label"] == "집중"
        assert by_hour[6][0]["label"] == ""

    def test_save_returns_day_stats(self, logged_in):
        client, _, focus, _ = logged_in

        stats = save(client, focus, [54, 55, 56]).json()["stats"]

        assert stats["logged_minutes"] == 30
        assert stats["fill_percentage"] == pytest.approx(2.1, abs=0.05)


@pytest.mark.django_db
class TestUndoEndpoint:
    def test_undo_reverts_the_save(self, logged_in):
        client, user, focus, _ = logged_in
        token = save(client, focus, [54, 55, 56]).json()["undo_token"]

        response = undo(client, token)

        assert response.status_code == 200
        assert tag_ids_by_slot(user) == {}

    def test_undo_returns_refreshed_rows_and_stats(self, logged_in):
        client, _, focus, _ = logged_in
        token = save(client, focus, [54, 55, 56]).json()["undo_token"]

        payload = undo(client, token).json()

        assert [row["hour"] for row in payload["runs"]] == [8, 9, 10]
        assert payload["stats"]["logged_minutes"] == 0

    def test_delete_can_also_be_undone(self, logged_in):
        client, user, focus, _ = logged_in
        save(client, focus, [54, 55])
        token = client.delete(
            API_URL,
            data=json.dumps({"date": TODAY.isoformat(), "slot_indexes": [54, 55]}),
            content_type="application/json",
        ).json()["undo_token"]

        undo(client, token)

        assert tag_ids_by_slot(user) == {54: focus.id, 55: focus.id}

    def test_token_works_only_once(self, logged_in):
        client, _, focus, _ = logged_in
        token = save(client, focus, [54]).json()["undo_token"]

        undo(client, token)

        assert undo(client, token).status_code == 404

    def test_unknown_token_is_refused(self, logged_in):
        client, _, focus, _ = logged_in
        save(client, focus, [54])

        assert undo(client, "누가봐도-아닌-토큰").status_code == 404

    def test_undo_without_any_save_is_refused(self, logged_in):
        client, _, _, _ = logged_in

        assert undo(client, "무엇이든").status_code == 404

    def test_missing_token_field_is_refused(self, logged_in):
        client, _, focus, _ = logged_in
        save(client, focus, [54])

        response = client.post(
            UNDO_URL, data=json.dumps({}), content_type="application/json"
        )

        assert response.status_code == 404

    def test_request_cannot_redirect_the_restore_to_another_date(self, logged_in):
        """날짜는 스냅샷에서만 온다. 본문에 실어 보내도 무시한다."""
        client, user, focus, _ = logged_in
        other_day = date(2026, 7, 20)
        TimeBlock.objects.create(
            user=user, date=other_day, slot_index=54, tag=focus
        )
        token = save(client, focus, [54]).json()["undo_token"]

        undo(client, token, date=other_day.isoformat(), slot_indexes=[54])

        assert tag_ids_by_slot(user, on_date=TODAY) == {}
        assert tag_ids_by_slot(user, on_date=other_day) == {54: focus.id}

    def test_an_earlier_token_survives_a_later_save(self, logged_in):
        """탭을 두 개 열어도 각자의 되돌리기가 살아 있어야 한다."""
        client, user, focus, leisure = logged_in
        first_token = save(client, focus, [54]).json()["undo_token"]
        save(client, leisure, [60])

        undo(client, first_token)

        assert tag_ids_by_slot(user) == {60: leisure.id}

    def test_undo_is_refused_when_the_tag_is_gone(self, logged_in):
        client, user, focus, leisure = logged_in
        save(client, focus, [54])
        token = save(client, leisure, [54]).json()["undo_token"]
        focus.delete()

        response = undo(client, token)

        assert response.status_code == 404
        assert tag_ids_by_slot(user) == {54: leisure.id}

    def test_undo_requires_login(self, client):
        response = undo(client, "무엇이든")

        assert response.status_code in (302, 403)
