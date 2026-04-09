from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Tag


class TagRepository:
    """Tag ORM 쿼리 전담."""

    def find_accessible(self, user):
        """사용자 태그 + 기본 태그"""
        return Tag.objects.filter(Q(user=user) | Q(is_default=True))

    def find_accessible_ordered(self, user):
        return self.find_accessible(user).order_by("-is_default", "name")

    def find_by_id_accessible(self, tag_id, user):
        """사용자가 접근 가능한 특정 태그 조회. 없으면 None."""
        return Tag.objects.filter(
            Q(id=tag_id, user=user) | Q(id=tag_id, is_default=True)
        ).first()

    def find_by_id(self, tag_id):
        return Tag.objects.filter(id=tag_id).first()

    def get_for_owner_or_404(self, tag_id, user):
        """일반 사용자: 본인 비기본 태그만. superuser: 전체."""
        if user.is_superuser:
            return get_object_or_404(Tag, id=tag_id)
        return get_object_or_404(Tag, id=tag_id, user=user, is_default=False)

    def exists_duplicate(self, user, name, exclude_id=None):
        """사용자 또는 기본 태그 중 같은 이름 존재 여부"""
        qs = Tag.objects.filter(Q(user=user, name=name) | Q(is_default=True, name=name))
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def create(self, user, name, color, is_default):
        return Tag.objects.create(
            user=None if is_default else user,
            name=name,
            color=color,
            is_default=is_default,
        )

    def save(self, tag):
        tag.save()
        return tag

    def delete(self, tag):
        tag.delete()
