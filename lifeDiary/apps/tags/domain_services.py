class TagPolicyService:
    """
    태그 접근 정책 도메인 서비스.
    ORM 없음, request 없음. 순수 정책 판단만 담당.

    태그는 전부 개인 소유이므로 규칙은 하나다 — 자기 것만 다룬다.
    관리자도 예외가 아니다.
    """

    def can_manage(self, user, tag) -> bool:
        return tag.user_id == user.id

    def can_edit(self, user, tag) -> bool:
        return self.can_manage(user, tag)

    def can_delete(self, user, tag) -> bool:
        return self.can_manage(user, tag)


_tag_policy_service = TagPolicyService()
