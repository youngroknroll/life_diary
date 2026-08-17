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
# 면의 색상(hue)을 그대로 따라가야 한다 — 어긋나면 같은 카테고리가 표와
# 그래프에서 다른 색으로 읽힌다. 흰 배경 대비는 3.6~3.9로 맞춘다.
CATEGORY_LINE_COLOR = {
    "work": "#4E8F63",
    "move": "#4F8B9E",
    "care": "#C1715A",
    "life": "#A87A1A",
    "sleep": "#8A78D0",
}
