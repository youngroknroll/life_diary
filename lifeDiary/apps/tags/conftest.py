import pytest

from apps.tags.models import Category, Tag


@pytest.fixture
def category_factory(db):
    counter = {"n": 0}

    def _make(name=None, slug=None, color="#FF0000", display_order=0, **kwargs):
        counter["n"] += 1
        return Category.objects.create(
            name=name or f"카테고리{counter['n']}",
            slug=slug or f"cat-{counter['n']}",
            color=color,
            display_order=display_order,
            **kwargs,
        )

    return _make


@pytest.fixture
def tag_factory(db, category_factory):
    counter = {"n": 0}

    def _make(user, name=None, category=None, color="#0000FF", is_default=False, **kwargs):
        counter["n"] += 1
        return Tag.objects.create(
            user=user,
            category=category or category_factory(),
            name=name or f"태그{counter['n']}",
            color=color,
            is_default=is_default,
            **kwargs,
        )

    return _make
