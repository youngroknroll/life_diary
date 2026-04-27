"""사용자 메시지 표준 타입.

비즈니스 로직은 `LocalizableMessage`를 반환하고, 표현 계층(템플릿/시리얼라이저)에서
`render_message` 태그 또는 `to_dict()`로 렌더링한다.
"""

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["positive", "info", "warning", "error"]


@dataclass(frozen=True)
class LocalizableMessage:
    code: str
    params: dict = field(default_factory=dict)
    severity: Severity = "info"

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "params": self.params,
            "severity": self.severity,
        }
