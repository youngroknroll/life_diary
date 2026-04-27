from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext

from .domain_services import _tag_policy_service
from .repositories import CategoryRepository, TagRepository
from apps.dashboard.repositories import TimeBlockRepository

_tag_repo = TagRepository()
_category_repo = CategoryRepository()
_time_block_repo = TimeBlockRepository()


@dataclass(frozen=True)
class TagData:
    id: int
    name: str
    color: str
    is_default: bool
    category_id: int | None
    can_edit: bool
    can_delete: bool


class ListTagsUseCase:
    def execute(self, user) -> list[TagData]:
        tags = _tag_repo.find_accessible(user).order_by("is_default", "name")
        return [
            TagData(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                is_default=tag.is_default,
                category_id=tag.category_id,
                can_edit=_tag_policy_service.can_edit(user, tag),
                can_delete=_tag_policy_service.can_delete(user, tag),
            )
            for tag in tags
        ]


class CreateTagUseCase:
    def execute(self, user, name: str, color: str, is_default: bool, category_id) -> dict:
        _tag_policy_service.validate_create_default(user, is_default)

        if not name or not color:
            raise ValueError(gettext("태그명과 색상을 입력해주세요."))

        if not category_id:
            raise ValueError(gettext("카테고리를 선택해주세요."))

        category = _category_repo.find_by_id(category_id)
        if not category:
            raise LookupError(gettext("존재하지 않는 카테고리입니다."))

        if _tag_repo.exists_duplicate(user, name):
            raise ValueError(gettext("이미 같은 이름의 태그가 존재합니다."))

        tag = _tag_repo.create(user, name, color, is_default, category=category)
        return {"id": tag.id, "name": tag.name, "color": tag.color,
                "is_default": tag.is_default, "category_id": tag.category_id}


class UpdateTagUseCase:
    def execute(self, user, tag_id: int, name: str, color: str,
                is_default: bool, category_id) -> dict:
        tag = _tag_repo.get_for_owner_or_404(tag_id, user)
        _tag_policy_service.validate_default_flip(user, tag, is_default)

        if not name or not color:
            raise ValueError(gettext("태그명과 색상을 입력해주세요."))

        if _tag_repo.exists_duplicate(user, name, exclude_id=tag.id):
            raise ValueError(gettext("이미 같은 이름의 태그가 존재합니다."))

        if category_id:
            category = _category_repo.find_by_id(category_id)
            if not category:
                raise LookupError(gettext("존재하지 않는 카테고리입니다."))
            tag.category = category

        tag.name = name
        tag.color = color
        tag.is_default = is_default
        tag.user = None if is_default else user
        _tag_repo.save(tag)
        return {"id": tag.id, "name": tag.name, "color": tag.color,
                "is_default": tag.is_default, "category_id": tag.category_id}


class DeleteTagUseCase:
    def execute(self, user, tag_id: int) -> str:
        tag = _tag_repo.get_for_owner_or_404(tag_id, user)
        if tag.is_default and _time_block_repo.is_tag_in_use(tag):
            raise ValueError(gettext("이 기본 태그는 사용 중이어서 삭제할 수 없습니다."))
        tag_name = tag.name
        _tag_repo.delete(tag)
        return tag_name
