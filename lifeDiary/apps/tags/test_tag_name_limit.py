"""태그 이름 10자 제한 (사용자 결정 D3).

설명이 필요한 경우는 기록 저장 시의 메모로 갈음한다.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.tags.models import Category, Tag
from apps.tags.name_limit import MAX_TAG_NAME_LENGTH, shorten_tag_name


class TestShortenForMigration:
    def test_a_short_name_is_left_alone(self):
        assert shorten_tag_name("집중 작업", set()) == "집중 작업"

    def test_a_long_name_is_cut_to_the_limit(self):
        assert shorten_tag_name("자격증 공부 정리하기", set()) == "자격증 공부 정리하"

    def test_the_cut_never_exceeds_the_limit(self):
        result = shorten_tag_name("가" * 40, set())

        assert len(result) == MAX_TAG_NAME_LENGTH

    def test_a_collision_gets_a_suffix(self):
        taken = {"자격증 공부 정리하"}

        result = shorten_tag_name("자격증 공부 정리하기", taken)

        assert result != "자격증 공부 정리하"
        assert len(result) <= MAX_TAG_NAME_LENGTH

    def test_repeated_collisions_keep_finding_room(self):
        taken = {"자격증 공부 정리하", "자격증 공부 정리2"}

        result = shorten_tag_name("자격증 공부 정리하기", taken)

        assert result not in taken
        assert len(result) <= MAX_TAG_NAME_LENGTH


@pytest.mark.django_db
class TestModelRejectsLongNames:
    def test_a_name_at_the_limit_is_accepted(self, make_user):
        tag = Tag(
            user=make_user(username="limituser"),
            name="가" * MAX_TAG_NAME_LENGTH,
            category=Category.objects.get(slug="investment"),
        )

        tag.full_clean()

    def test_a_longer_name_is_refused(self, make_user):
        tag = Tag(
            user=make_user(username="overuser"),
            name="가" * (MAX_TAG_NAME_LENGTH + 1),
            category=Category.objects.get(slug="investment"),
        )

        with pytest.raises(ValidationError):
            tag.full_clean()
