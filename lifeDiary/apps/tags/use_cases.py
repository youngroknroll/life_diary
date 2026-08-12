from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT
from django.utils.translation import gettext

from .domain_services import _tag_policy_service
from .ordering import assign_display_order
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
    category_id: int | None
    can_edit: bool
    can_delete: bool
    block_count: int = 0
    total_hours: float = 0.0


class ListTagsUseCase:
    def execute(self, user) -> list[TagData]:
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
        return bool(_time_block_repo.count_blocks_by_tag(user))


class ReorderTagsUseCase:
    """사용자가 정한 태그 순서를 저장한다.

    받는 것은 "이 태그를 3 번으로" 같은 부분 지시가 아니라 목록 전체다.
    화면에 보이는 순서 자체가 곧 최종 상태라 서버가 자리를 계산할 필요가
    없고, 두 요청이 겹쳐도 뒤엣것이 온전한 순서로 덮어쓴다.
    """

    @transaction.atomic
    def execute(self, user, tag_ids) -> None:
        mine = {tag.id: tag for tag in _tag_repo.find_accessible(user)}
        requested = [int(tag_id) for tag_id in tag_ids]

        # 목록이 내 태그 집합과 정확히 같아야 한다. 빠진 것이 있으면 남은
        # 태그의 자리를 알 수 없고, 남의 id 가 섞이면 그 태그를 건드리게 된다.
        if len(set(requested)) != len(requested) or set(requested) != set(mine):
            raise ValueError(gettext("태그 목록이 현재 태그와 맞지 않습니다."))

        changed = assign_display_order([mine[tag_id] for tag_id in requested])
        if changed:
            _tag_repo.save_display_order(changed)


class CreateTagUseCase:
    def execute(self, user, name: str, color: str, category_id) -> dict:
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
        return {"id": tag.id, "name": tag.name, "color": tag.color,
                "category_id": tag.category_id}


class UpdateTagUseCase:
    def execute(self, user, tag_id: int, name: str, color: str, category_id) -> dict:
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
        return {"id": tag.id, "name": tag.name, "color": tag.color,
                "category_id": tag.category_id}


class DeleteTagUseCase:
    @transaction.atomic
    def execute(self, user, tag_id: int, move_to_id: int | None = None) -> str:
        """옮길 곳을 주면 기록을 살린 뒤 지운다.

        그냥 지우면 붙어 있던 구간이 미기록으로 되돌아가 통계 수치가 조용히
        바뀐다. 사용자는 태그 하나를 정리했을 뿐인데 지난달 기록률이 달라진다.
        """
        tag = _tag_repo.get_for_owner_or_404(tag_id, user)

        if move_to_id is not None:
            _time_block_repo.move_blocks_to_tag(tag, self._destination(user, tag, move_to_id))

        tag_name = tag.name
        _tag_repo.delete(tag)
        return tag_name

    def _destination(self, user, tag, move_to_id: int):
        if move_to_id == tag.id:
            raise ValueError(gettext("같은 태그로는 옮길 수 없습니다."))

        destination = _tag_repo.find_by_id_accessible(move_to_id, user)
        if not destination:
            raise ValueError(gettext("옮길 태그를 찾을 수 없습니다."))
        return destination
