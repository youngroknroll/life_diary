"""태그 조회·생성·수정·삭제 유스케이스."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils.translation import gettext

from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT
from apps.dashboard.repositories import TimeBlockRepository

from .domain_services import _tag_policy_service
from .repositories import CategoryRepository, TagRepository
from .signals import tags_changed

_tag_repo = TagRepository()
_category_repo = CategoryRepository()
_time_block_repo = TimeBlockRepository()


@dataclass(frozen=True)
class TagData:
    """태그 목록 응답용 값."""

    id: int
    name: str
    color: str
    category_id: int | None
    can_edit: bool
    can_delete: bool
    block_count: int = 0
    total_hours: float = 0.0


class ListTagsUseCase:
    """내가 접근할 수 있는 태그를 기록 수와 함께 나열한다."""

    def execute(self, user) -> list[TagData]:
        """정렬된 태그 목록을 태그별 기록 수와 함께 돌려준다."""
        tags = _tag_repo.find_accessible_ordered(user)
        blocks_by_tag = _time_block_repo.count_blocks_by_tag(user)

        return [
            TagData(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                category_id=tag.category_id,
                can_edit=_tag_policy_service.can_edit(user, tag),
                can_delete=_tag_policy_service.can_delete(user, tag),
                block_count=blocks_by_tag.get(tag.id, 0),
                total_hours=round(
                    blocks_by_tag.get(tag.id, 0) * MINUTES_PER_SLOT / MINUTES_PER_HOUR, 1
                ),
            )
            for tag in tags
        ]


# 시안 6c 의 빈 화면이 집어 주는 칩 개수.
FREQUENT_TAG_LIMIT = 4


class ListFrequentTagsUseCase:
    """빈 화면에서 바로 집을 태그 몇 개.

    시안은 제목을 "자주 쓰는 태그"라 하고 설명은 "최근 순으로 재정렬"이라 해
    서로 어긋난다. 빈도로 간다 — 자주 쓰는 것이 다시 쓸 것이고, 저장소가
    이미 세고 있는 값이라 새 집계를 더하지 않는다.
    """

    def execute(self, user, limit: int = FREQUENT_TAG_LIMIT) -> list:
        """기록이 많은 순으로 태그를 limit개까지 돌려준다. 같은 수면 목록 순서를 따른다."""
        tags = list(_tag_repo.find_accessible_ordered(user))
        if not tags:
            return []

        counts = _time_block_repo.count_blocks_by_tag(user)
        # 쓴 적 없는 태그도 남은 자리를 채운다. 정렬만 뒤로 민다.
        ordered = sorted(
            enumerate(tags),
            key=lambda pair: (-counts.get(pair[1].id, 0), pair[0]),
        )
        return [tag for _position, tag in ordered[:limit]]

    def has_usage(self, user) -> bool:
        """기록이 하나라도 있는 태그가 있는지 돌려준다."""
        return bool(_time_block_repo.count_blocks_by_tag(user))


def _notify_tags_changed(sender, user_id: int) -> None:
    transaction.on_commit(
        lambda user_id=user_id: tags_changed.send(sender=sender, user_id=user_id)
    )


class CreateTagUseCase:
    """태그를 만든다."""

    @transaction.atomic
    def execute(self, user, name: str, color: str, category_id) -> dict:
        """태그를 만들어 응답용 딕셔너리로 돌려준다.

        Raises:
            ValueError: 이름·색상·카테고리가 비었거나 같은 이름의 태그가 이미 있을 때.
            LookupError: 카테고리가 존재하지 않을 때.
        """
        if not name or not color:
            raise ValueError(gettext("태그명과 색상을 입력해주세요."))

        if not category_id:
            raise ValueError(gettext("카테고리를 선택해주세요."))

        category = _category_repo.find_by_id(category_id)
        if not category:
            raise LookupError(gettext("존재하지 않는 카테고리입니다."))

        if _tag_repo.exists_duplicate(user, name):
            raise ValueError(gettext("이미 같은 이름의 태그가 존재합니다."))

        tag = _tag_repo.create(user, name, color, category=category)
        _notify_tags_changed(CreateTagUseCase, user.id)
        return {"id": tag.id, "name": tag.name, "color": tag.color,
                "category_id": tag.category_id}


class UpdateTagUseCase:
    """내 태그의 이름·색상·카테고리를 바꾼다."""

    @transaction.atomic
    def execute(self, user, tag_id: int, name: str, color: str, category_id) -> dict:
        """태그를 수정해 응답용 딕셔너리로 돌려준다.

        Raises:
            ValueError: 이름·색상이 비었거나 같은 이름의 태그가 이미 있을 때.
            LookupError: 카테고리가 존재하지 않을 때.
            Http404: 내 태그가 아닐 때.
        """
        tag = _tag_repo.get_for_owner_or_404(tag_id, user)

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
        _tag_repo.save(tag)
        _notify_tags_changed(UpdateTagUseCase, user.id)
        return {"id": tag.id, "name": tag.name, "color": tag.color,
                "category_id": tag.category_id}


class DeleteTagUseCase:
    """내 태그를 삭제한다."""

    @transaction.atomic
    def execute(self, user, tag_id: int, move_to_id: int | None = None) -> str:
        """옮길 곳을 주면 기록을 살린 뒤 지운다.

        그냥 지우면 붙어 있던 구간이 미기록으로 되돌아가 통계 수치가 조용히
        바뀐다. 사용자는 태그 하나를 정리했을 뿐인데 지난달 기록률이 달라진다.
        """
        tag = _tag_repo.get_for_owner_or_404(tag_id, user)

        if move_to_id is not None:
            _time_block_repo.move_blocks_to_tag(tag, self._destination(user, tag, move_to_id))
        else:
            _time_block_repo.delete_blocks_for_tag(tag)

        tag_name = tag.name
        _tag_repo.delete(tag)
        _notify_tags_changed(DeleteTagUseCase, user.id)
        return tag_name

    def _destination(self, user, tag, move_to_id: int):
        if move_to_id == tag.id:
            raise ValueError(gettext("같은 태그로는 옮길 수 없습니다."))

        destination = _tag_repo.find_by_id_accessible(move_to_id, user)
        if not destination:
            raise ValueError(gettext("옮길 태그를 찾을 수 없습니다."))
        return destination
