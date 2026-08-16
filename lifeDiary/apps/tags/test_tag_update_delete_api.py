import json
from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.tags.models import Category, Tag


def _make_tag(user, name="독서", slug="investment"):
    category = Category.objects.get(slug=slug)
    return Tag.objects.create(user=user, name=name, color="#FF5733", category=category)


@pytest.mark.django_db
class TestTagUpdateAPI:
    def test_updating_own_tag_name_returns_updated_tag(self, auth_client):
        tag = _make_tag(auth_client.user)
        resp = auth_client.put(
            f"/api/tags/{tag.id}/",
            data=json.dumps({
                "name": "공부",
                "color": tag.color,
                "category_id": tag.category_id,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"]
        assert data["tag"]["name"] == "공부"
        tag.refresh_from_db()
        assert tag.name == "공부"


@pytest.mark.django_db
class TestTagDeleteAPI:
    def test_deleting_own_tag_confirms_deletion(self, auth_client):
        tag = _make_tag(auth_client.user)
        resp = auth_client.delete(f"/api/tags/{tag.id}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"]
        assert "message" in data
        assert not Tag.objects.filter(id=tag.id).exists()

    def test_deleting_tag_moves_blocks_to_requested_tag(self, auth_client):
        source = _make_tag(auth_client.user, name="독서")
        destination = _make_tag(auth_client.user, name="공부", slug="proactive")
        block = TimeBlock.objects.create(
            user=auth_client.user, date=date(2026, 8, 1), slot_index=0, tag=source,
        )
        resp = auth_client.delete(
            f"/api/tags/{source.id}/",
            data=json.dumps({"move_to_id": destination.id}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        block.refresh_from_db()
        assert block.tag_id == destination.id
        assert not Tag.objects.filter(id=source.id).exists()
