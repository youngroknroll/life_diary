"""가입한 사용자에게 처음 쥐여 주는 태그 집합.

공유 기본 태그를 폐지하면서 생긴 자리다. 전 사용자가 한 행을 나눠 쓰는 대신
가입 시점에 각자의 행으로 복제해 준다. 그래야 이름을 고치고 순서를 바꾸고
지우는 일이 남에게 번지지 않는다.

시안 7a 의 카테고리별 예시 태그와 같은 집합이다. 설명 화면이 "이런 태그를
만드세요"라고 보여 준 것을 실제로 만들어 준다.
"""

from django.db import transaction
from django.utils.translation import gettext, gettext_lazy as _

from .models import Category, Tag
from .name_limit import MAX_TAG_NAME_LENGTH


# (카테고리 슬러그, 태그명) — 카테고리 표시 순서대로.
SEED_TAGS = (
    ("investment", "집중 작업"),
    ("investment", "회의"),
    ("investment", "학습"),
    ("proactive", "운동"),
    ("proactive", "약속"),
    ("passive", "여가"),
    ("passive", "멍때림"),
    ("basic_life", "식사"),
    ("basic_life", "이동"),
    ("sleep", "수면"),
    ("sleep", "낮잠"),
)


# SEED_TAGS 의 원문을 makemessages 가 수집하도록 등록한다.
# models.py 의 _CATEGORY_I18N_REGISTRY 와 같은 이유다 — 실제 번역은 생성
# 시점의 gettext 가 하고, 여기서는 추출만 시킨다.
_SEED_I18N_REGISTRY = (
    _("집중 작업"),
    _("회의"),
    _("학습"),
    _("운동"),
    _("약속"),
    _("여가"),
    _("멍때림"),
    _("식사"),
    _("이동"),
    _("수면"),
    _("낮잠"),
)


def seed_names_by_category():
    """카테고리 슬러그별 시드 태그명. 설명 화면의 예시로도 쓴다."""
    grouped = {}
    for slug, source in SEED_TAGS:
        grouped.setdefault(slug, []).append(gettext(source))
    return grouped


@transaction.atomic
def create_seed_tags(user):
    """시드 태그를 개인 소유로 만든다. 이미 쓰는 이름은 건드리지 않는다.

    이름은 가입 시점 언어로 번역해 저장한다. 카테고리와 달리 태그는 사용자가
    고쳐 쓰는 자기 데이터라, 표시할 때마다 번역하면 고친 이름이 원문으로
    되돌아 보인다.
    """
    categories = {category.slug: category for category in Category.objects.all()}
    taken = set(Tag.objects.filter(user=user).values_list("name", flat=True))

    created = []
    for slug, source in SEED_TAGS:
        category = categories.get(slug)
        if category is None:
            continue

        name = gettext(source).strip()[:MAX_TAG_NAME_LENGTH].strip()
        if not name or name in taken:
            continue

        taken.add(name)
        created.append(Tag.objects.create(user=user, name=name, category=category))

    return created
