class TagPolicyService:
    """
    태그 접근 정책 도메인 서비스.
    ORM 없음, request 없음. 순수 정책 판단만 담당.
    현재 tags/views.py에 분산된 권한 규칙을 한 곳에 집중.
    """

    def can_create_default(self, user) -> bool:
        """기본 태그 생성은 superuser만 가능."""
        return user.is_superuser

    def can_edit(self, user, tag) -> bool:
        """기본 태그는 superuser만, 일반 태그는 본인만 수정 가능."""
        if tag.is_default:
            return user.is_superuser
        return tag.user == user

    def can_delete(self, user, tag) -> bool:
        """기본 태그는 superuser만, 일반 태그는 본인만 삭제 가능."""
        if tag.is_default:
            return user.is_superuser
        return tag.user == user

    def validate_default_flip(self, user, tag, requested_is_default) -> None:
        """
        is_default 변경(True→False 또는 False→True) 시 superuser만 허용.
        위반 시 PermissionError.
        """
        if requested_is_default != tag.is_default and not user.is_superuser:
            raise PermissionError("기본 태그 설정 변경은 관리자만 할 수 있습니다.")

    def validate_create_default(self, user, is_default) -> None:
        """기본 태그로 생성 시 superuser 여부 검사. 위반 시 PermissionError."""
        if is_default and not user.is_superuser:
            raise PermissionError("기본 태그는 관리자만 생성할 수 있습니다.")


_tag_policy_service = TagPolicyService()
