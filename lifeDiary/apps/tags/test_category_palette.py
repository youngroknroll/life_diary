"""색은 카테고리가 정한다."""

import pytest

from apps.tags.models import INK_ON_ACCENT, Category, Tag


SIAN_PALETTE = {
    "investment": "#7CD9A0",
    "proactive": "#7DCFE8",
    "passive": "#FFA98C",
    "basic_life": "#FFD166",
    "sleep": "#B8A6F0",
}


@pytest.mark.django_db
class TestCategoryPalette:
    @pytest.mark.parametrize("slug,color", SIAN_PALETTE.items())
    def test_category_carries_the_sian_color(self, slug, color):
        assert Category.objects.get(slug=slug).color == color

    def test_every_category_has_a_distinct_color(self):
        colors = list(Category.objects.values_list("color", flat=True))

        assert len(colors) == len(set(colors))


@pytest.mark.django_db
class TestTagFollowsItsCategory:
    def test_a_new_tag_takes_its_category_color(self, make_user):
        user = make_user(username="paletteuser")

        tag = Tag.objects.create(
            user=user,
            name="자격증 공부",
            is_default=False,
            category=Category.objects.get(slug="investment"),
        )

        assert tag.color == "#7CD9A0"

    def test_a_requested_color_is_ignored(self, make_user):
        """색 선택기를 없앴으므로 넘어온 값은 의미를 깨뜨릴 뿐이다."""
        user = make_user(username="paletteuser")

        tag = Tag.objects.create(
            user=user,
            name="자격증 공부",
            color="#FF00FF",
            is_default=False,
            category=Category.objects.get(slug="investment"),
        )

        assert tag.color == "#7CD9A0"

    def test_moving_a_tag_to_another_category_recolors_it(self, make_user):
        user = make_user(username="paletteuser")
        tag = Tag.objects.create(
            user=user,
            name="OTT",
            is_default=False,
            category=Category.objects.get(slug="proactive"),
        )

        tag.category = Category.objects.get(slug="passive")
        tag.save()

        assert tag.color == "#FFA98C"

    def test_tags_in_one_category_share_a_color(self, make_user):
        user = make_user(username="paletteuser")
        investment = Category.objects.get(slug="investment")

        first = Tag.objects.create(
            user=user, name="집중 작업", is_default=False, category=investment
        )
        second = Tag.objects.create(
            user=user, name="회의", is_default=False, category=investment
        )

        assert first.color == second.color

    def test_tag_text_color_is_always_the_shared_ink(self, make_user):
        """밝기에 따라 흰 글자로 뒤집으면 4.5:1을 넘기지 못한다."""
        user = make_user(username="inkuser")

        for category in Category.objects.all():
            tag = Tag.objects.create(
                user=user,
                name=f"태그{category.pk}",
                is_default=False,
                category=category,
            )
            assert tag.text_color == INK_ON_ACCENT

    def test_text_ink_is_readable_on_every_category_color(self):
        """태그 색 위 텍스트는 항상 같은 잉크를 쓴다."""
        user_tag_colors = Category.objects.values_list("color", flat=True)

        for color in user_tag_colors:
            assert _contrast_ratio(color, INK_ON_ACCENT) >= 4.5


def _relative_luminance(hex_color):
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    adjusted = [
        value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * adjusted[0] + 0.7152 * adjusted[1] + 0.0722 * adjusted[2]


def _contrast_ratio(foreground, background):
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)
