"""통계 entry의 안정 identity key. 표시명은 사용자가 바꿀 수 있어 key가 아니다."""

UNCLASSIFIED_KEY = "unclassified"


def real_tag_key(tag_id: int) -> str:
    return f"tag:{tag_id}"
