from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .repositories import CategoryRepository
from .seed_tags import seed_names_by_category

_category_repo = CategoryRepository()


@login_required
def index(request):
    return render(request, "tags/index.html")


# 안내 화면의 예시일 뿐 사용자 태그가 아니다. 시안 7a 의 세 번째 열.


@login_required
@require_GET
def category_guide(request):
    """소비시간 다섯 분류 설명. 색이 무엇을 뜻하는지 읽는 화면이다."""
    # 예시는 가입 시 실제로 만들어 주는 시드 태그와 같은 집합이다.
    # 두 곳에 적으면 한쪽만 바뀌어 설명 화면이 거짓말을 하게 된다.
    examples = seed_names_by_category()
    categories = list(_category_repo.find_all())
    for category in categories:
        category.example_tags = examples.get(category.slug, [])
    return render(
        request,
        "tags/category_guide.html",
        {"categories": categories},
    )
