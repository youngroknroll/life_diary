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

# 선(딥) 변형 — 면(--color-accent-*)과 짝을 이루는 값. 차트 라인(stats.js의
# CATEGORY_LINE)과 목표 진행 바 채움에 같은 색을 쓴다. 서버가 인라인 style로
# 내보내야 해서 CSS 토큰이 아니라 여기 한 번 더 둔다(apps/tags/models.py의
# INK_ON_ACCENT와 같은 이유).
CATEGORY_LINE_COLOR = {
    "work": "#4E8F63",
    "move": "#4F8B9E",
    "care": "#C1715A",
    "life": "#B9C2BA",
    "sleep": "#8A9A91",
}
