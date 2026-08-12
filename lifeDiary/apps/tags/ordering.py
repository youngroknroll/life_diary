"""태그에 표시 순서 번호를 매기는 규칙.

번호는 (사용자, 카테고리) 묶음마다 0 부터 다시 센다. 카테고리를 넘나드는
순서는 두지 않는다 — 태그의 카테고리는 색이자 통계 분류라서 순서를 바꾸는
동작이 그것까지 건드리면 안 된다.

0015 마이그레이션이 같은 규칙으로 첫 번호를 매기지만 그쪽은 이 함수를
부르지 않고 제 안에 복사해 두었다. 데이터 마이그레이션은 한번 적용되면
그때의 동작으로 고정되어야 하는데, 여기를 고치면 아직 적용하지 않은
설치본의 과거 마이그레이션까지 따라 바뀐다.
"""


def assign_display_order(tags):
    """받은 순서대로 번호를 매긴다. 카테고리마다 0 부터.

    태그의 category 는 읽기만 한다. 넘어온 목록에서 카테고리가 뒤섞여
    있어도 각 태그는 제 카테고리 안에서의 자리만 받는다.
    """
    position_by_category = {}
    changed = []

    for tag in tags:
        position = position_by_category.get(tag.category_id, 0)
        position_by_category[tag.category_id] = position + 1
        if tag.display_order != position:
            tag.display_order = position
            changed.append(tag)

    return changed
