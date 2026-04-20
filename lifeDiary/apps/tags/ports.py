from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TagReader(Protocol):
    """dashboard 등 외부 앱이 Tag를 읽을 때 사용하는 Port."""

    def find_by_id_accessible(self, tag_id: int, user): ...

    def find_accessible_ordered(self, user): ...
