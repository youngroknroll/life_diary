from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Category, Tag


class CategoryRepository:
    """Category ORM 쿼리 전담."""

    def find_all(self):
        return Category.objects.all()

    def find_by_slug(self, slug):
        return Category.objects.filter(slug=slug).first()

    def find_by_id(self, category_id):
        return Category.objects.filter(id=category_id).first()


class TagRepository:
    """Tag ORM 쿼리 전담."""

    def find_accessible(self, user):
        """태그는 전부 개인 소유다. 접근 가능 = 본인 것."""
        return Tag.objects.filter(user=user)

    def find_accessible_ordered(self, user):
        """카테고리 순 → 사용자가 정한 순 → 이름 순."""
        return self.find_accessible(user).order_by(
            "category__display_order", "display_order", "name"
        )

    def find_by_id_accessible(self, tag_id, user):
        """사용자가 접근 가능한 특정 태그 조회. 없으면 None."""
        return Tag.objects.filter(id=tag_id, user=user).first()

    def find_by_id(self, tag_id):
        return Tag.objects.filter(id=tag_id).first()

    def get_for_owner_or_404(self, tag_id, user):
        """본인 태그만. superuser 도 남의 태그를 다루지 않는다."""
        return get_object_or_404(Tag, id=tag_id, user=user)

    def exists_duplicate(self, user, name, exclude_id=None):
        """같은 사용자 안에서 같은 이름 존재 여부"""
        qs = Tag.objects.filter(user=user, name=name)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def create(self, user, name, color, category=None):
        return Tag.objects.create(
            user=user,
            name=name,
            color=color,
            category=category,
        )

    def find_by_category(self, user, category):
        """특정 카테고리의 사용자 접근 가능 태그"""
        return self.find_accessible(user).filter(category=category)

    def save(self, tag):
        tag.save()
        return tag

    def save_display_order(self, tags):
        """순서만 쓴다. Tag.save() 를 거치지 않으므로 색은 그대로다."""
        Tag.objects.bulk_update(tags, ["display_order"])

    def delete(self, tag):
        tag.delete()
