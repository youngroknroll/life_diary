"""태그 이름 길이 규칙.

기록 화면의 태그 시트와 그리드 라벨은 짧은 이름을 전제로 한다. 설명이 필요한
경우는 기록 저장 시의 메모로 갈음한다(사용자 결정 D3).
"""

MAX_TAG_NAME_LENGTH = 10


def shorten_tag_name(name: str, taken: set[str]) -> str:
    """제한에 맞게 줄이되, 같은 사용자 안에서 겹치지 않는 이름을 돌려준다.

    두 이름이 앞 10자가 같으면 절삭만으로 유니크 제약이 깨진다.
    """
    trimmed = name[:MAX_TAG_NAME_LENGTH]
    if trimmed not in taken:
        return trimmed

    for serial in range(2, 100):
        suffix = str(serial)
        candidate = trimmed[: MAX_TAG_NAME_LENGTH - len(suffix)] + suffix
        if candidate not in taken:
            return candidate

    raise ValueError(f"'{name}' 에 쓸 수 있는 짧은 이름을 찾지 못했습니다.")
