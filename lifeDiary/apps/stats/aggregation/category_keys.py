"""카테고리 slug → 차트/프런트가 쓰는 짧은 key.

Why: Category.slug는 DB 이력(investment/proactive/passive/basic_life)을 그대로
따르지만, 차트 코드와 CSS 토큰(--color-accent-work 등)은 디자인 스펙이 정한
work/move/care/life/sleep 다섯 키를 쓴다. 이 매핑이 그 경계다.
"""

CATEGORY_KEY_BY_SLUG = {
    "investment": "work",
    "proactive": "move",
    "passive": "care",
    "basic_life": "life",
    "sleep": "sleep",
}
