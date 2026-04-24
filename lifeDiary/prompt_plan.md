# 대시보드 태그 UX 개선 계획

**작성일**: 2026-04-24
**대상**: 대시보드 (`apps/dashboard/`)
**복잡도**: LOW

---

## 요구사항

1. **Feature 1 — 하단 범례 태그 클릭 이벤트**
   그리드 아래 `#tagLegend` 배지를 클릭하면 사이드바 태그 버튼과 **동일한 `selectTag()` 이벤트**가 발생해야 한다. (태그 선택 상태로 전환 → 다음 슬롯 저장 시 사용)

2. **Feature 2 — 사이드바 태그 목록 카테고리화**
   사이드바 `#tagContainer`의 태그 버튼들을 `Category.display_order` 순으로 카테고리별 그룹화하여 출력한다. 카테고리명 헤더 + 그 아래 태그 버튼.
   (범례 `#tagLegend`는 그대로 flat 유지)

---

## 현재 상태 요약

| 위치 | 파일 | 상태 |
|---|---|---|
| 범례 SSR | `apps/dashboard/templates/dashboard/index.html:128-139` | `{% tag_badge %}` flat, 클릭 핸들러 없음 |
| 범례 CSR | `apps/dashboard/static/dashboard/js/dashboard.js:423-432` (`renderTagLegend`) | `<span>` flat, 클릭 핸들러 없음 |
| 사이드바 SSR | `index.html:199-217` | `<button onclick="selectTag(...)">` flat |
| 사이드바 CSR | `dashboard.js:403-421` (`renderTagContainer`) | `<button onclick="selectTag(...)">` flat |
| `selectTag(id, color, name)` | `dashboard.js` (기존 함수) | 그대로 재사용 |
| `tag_badge` 템플릿태그 | `apps/tags/templatetags/tag_ui.py:17-25` | `<span>` 생성, onclick 속성 없음 |
| Tag 모델 | `apps/tags/models.py` | `category` FK 존재 (mandatory) |
| `/api/tags/` 응답 | `apps/tags/views.py:61-77` | `category_id`만 포함 (name/color 없음) |
| `/api/categories/` 응답 | 이미 존재, dashboard init에서 호출 중 (`dashboard.js:47-50`) | 사용 가능 |
| Dashboard view context | `apps/dashboard/views.py:61` | `user_tags`는 `find_accessible_ordered` 결과 (is_default → name) |

---

## Phase 1 — Feature 1: 범례 클릭 핸들러 추가

**목표**: 범례 배지 클릭 시 `selectTag(id, color, name)` 호출.

**변경 파일**
1. `apps/dashboard/static/dashboard/js/dashboard.js` — `renderTagLegend()` 수정
   - `<span>` → `<button>` 또는 `<span role="button" tabindex="0" onclick="...">`
   - 스타일 유지 (bootstrap `badge` 그대로)
   - `data-tag-id` 추가 (사이드바 버튼과 동일한 선택 상태 UI 연동용)
2. `apps/tags/templatetags/tag_ui.py` — `tag_badge` 시그니처 확장
   - 기존 호출자 호환 유지: `clickable=False`, `tag_id=None` 옵션 파라미터 추가
   - `clickable=True`일 때 onclick 추가
3. `apps/dashboard/templates/dashboard/index.html:128-139` — 범례에서 `tag_badge` 호출 시 `clickable=True tag_id=tag.id` 전달

**클릭 시 동작**
- 기존 `selectTag(id, color, name)` 로직 그대로 호출 → 선택 상태 변경 + 사이드바 버튼 active 표시 연동

**접근성**
- `<button type="button" class="badge btn-tag-legend" ...>` 로 구현 (키보드 포커스/엔터 지원)
- 버튼 기본 스타일 리셋 필요 (border 제거, padding 유지)

**리스크**: 없음. 순수 핸들러 추가.

---

## Phase 2 — Feature 2: 사이드바 카테고리 그룹화

**목표**: `#tagContainer` 버튼을 카테고리별 그룹으로 묶어 렌더링.

### 2-1. API 응답 보강

`/api/tags/` 응답에 카테고리 메타 추가:

```python
# apps/tags/views.py:61-77
{
    "tags": [...],
    "categories": [
        {"id": 1, "name": "수면시간", "color": "#...", "display_order": 1},
        ...
    ],
}
```

- `apps/tags/use_cases.py` — 카테고리 조회 유스케이스 재사용 또는 추가
- Tag 직렬화에 `category_id`는 이미 있음 (변경 불필요)

**대안**: 기존 `/api/categories/` 별도 호출 유지 후 JS에서 병합 (이미 init에서 호출 중).
→ **채택**: 대시보드는 이미 둘 다 호출 중이므로 `availableCategories` 모듈 변수에 저장 후 `renderTagContainer`에서 사용. API 변경 최소화.

### 2-2. CSR — `renderTagContainer()` 그룹화

```javascript
function renderTagContainer(tags) {
    const container = document.getElementById('tagContainer');
    if (tags.length === 0) { /* empty state */ return; }

    // availableCategories는 init에서 /api/categories/ 로드 후 저장된 모듈 변수
    const byCategory = new Map();
    for (const tag of tags) {
        const key = tag.category_id;
        if (!byCategory.has(key)) byCategory.set(key, []);
        byCategory.get(key).push(tag);
    }

    const sortedCategories = [...availableCategories]
        .sort((a, b) => a.display_order - b.display_order);

    container.innerHTML = sortedCategories
        .filter(cat => byCategory.has(cat.id))
        .map(cat => `
            <div class="tag-category-group">
                <div class="tag-category-header small text-muted fw-bold mt-2">
                    <span class="category-dot" style="background-color:${cat.color}"></span>
                    ${escapeHtml(cat.name)}
                </div>
                <div class="d-grid gap-1">
                    ${byCategory.get(cat.id).map(tag => renderTagButton(tag)).join('')}
                </div>
            </div>
        `).join('');
}
```

- `renderTagButton(tag)` 헬퍼 추출 → 기존 버튼 HTML 재사용
- XSS 방어: `escapeHtml()` 사용 (기존 `utils.js`에 있는지 확인, 없으면 추가)

### 2-3. SSR — `index.html:199-217` 그룹화

Django `{% regroup %}` 템플릿 태그 사용:

```django
{% regroup user_tags by category as tags_by_category %}
<div class="d-grid gap-2" id="tagContainer">
    {% if user_tags %}
        {% for cat_group in tags_by_category %}
            <div class="tag-category-group">
                <div class="tag-category-header small text-muted fw-bold mt-2">
                    {% tag_dot cat_group.grouper.color %}
                    {{ cat_group.grouper.name }}
                </div>
                <div class="d-grid gap-1">
                    {% for tag in cat_group.list %}
                        <button class="btn btn-outline-secondary btn-sm tag-btn text-start"
                                data-tag-id="{{ tag.id }}"
                                onclick="selectTag({{ tag.id }}, '{{ tag.color }}', '{{ tag.name }}')">
                            {% tag_dot tag.color %}
                            {{ tag.name }}
                            {% if tag.is_default %}<i class="fas fa-star text-warning ms-1" title="기본 태그"></i>{% endif %}
                        </button>
                    {% endfor %}
                </div>
            </div>
        {% endfor %}
    {% else %}
        <div class="text-center py-2">
            <p class="text-muted small">태그가 없습니다.<br>'새 태그' 버튼으로 추가하세요.</p>
        </div>
    {% endif %}
</div>
```

**주의**: `{% regroup %}`은 미리 정렬된 쿼리셋이 필요. `find_accessible_ordered`는 현재 `is_default, name` 순.
→ `apps/dashboard/views.py:61` 에서 `user_tags`를 `category__display_order, is_default, name` 순으로 재정렬하거나, 뷰에서 파이썬으로 정렬.

### 2-4. 초기 렌더 일관성

- 뷰 컨텍스트에 `categories`도 주입 (`Category.objects.order_by('display_order')`) → 템플릿에서 `{% regroup %}` 그룹 순서를 `display_order`에 맞추기 위해 정렬된 쿼리셋 사용
- CSR/SSR 출력이 동일하도록 확인

---

## 변경 파일 목록

| 파일 | Phase | 변경 유형 |
|------|-------|----------|
| `apps/dashboard/static/dashboard/js/dashboard.js` | 1, 2 | `renderTagLegend` onclick 추가, `renderTagContainer` 그룹화, `availableCategories` 저장 |
| `apps/dashboard/templates/dashboard/index.html` | 1, 2 | 범례 `tag_badge clickable=True`, 사이드바 `{% regroup %}` |
| `apps/tags/templatetags/tag_ui.py` | 1 | `tag_badge`에 `clickable`, `tag_id` 옵션 파라미터 |
| `apps/dashboard/views.py` | 2 | `user_tags` 정렬 수정 (category__display_order 우선) |
| `apps/dashboard/static/dashboard/css/dashboard.css` (있으면) or 인라인 | 1, 2 | 범례 버튼 리셋, 카테고리 헤더 스타일 |

총 4~5개 파일

---

## 테스트 계획

1. **Feature 1 수동 테스트**
   - 범례 배지 클릭 → 사이드바 동일 태그가 active 상태가 되는지 확인
   - 슬롯 선택 후 범례 클릭 → `selectTag` 이벤트로 저장 흐름 정상 동작 확인
   - 키보드 Tab → 범례 포커스 → Enter로 선택되는지 확인

2. **Feature 2 수동 테스트**
   - 5개 카테고리가 `display_order` 순서로 나타나는지
   - 사용자가 생성한 태그가 올바른 카테고리 아래에 배치되는지
   - 특정 카테고리에 태그가 0개면 헤더가 숨겨지는지
   - 태그 생성/삭제 후 리렌더링 시 그룹 유지되는지

3. **Django 단위 테스트**
   - `apps/dashboard/tests.py` — 뷰 컨텍스트에 정렬된 `user_tags`가 들어가는지
   - 기존 `pytest` 55건 통과 유지 확인

4. **회귀**
   - `tag_badge` 기존 호출 4개 이상 (stats 등 다른 페이지) → 호환성 확인

---

## 리스크

| 리스크 | 완화 |
|---|---|
| `tag_badge` 시그니처 변경 시 기존 호출자 깨짐 | 신규 파라미터 모두 optional + 기본값 (기존 동작 유지) |
| SSR/CSR 초기 렌더 플래시 (flat → 그룹) | 뷰 초기 렌더부터 그룹 구조로 출력 → 플래시 없음 |
| `availableCategories` 로딩 실패 시 그룹화 불가 | 폴백: 카테고리 로드 실패 시 기존 flat 렌더링 유지 |
| 범례 `<button>` 변환 시 기존 CSS 영향 | 스타일 격리를 위해 `btn-tag-legend` 전용 클래스 추가 |

---

## 실행 순서

```
Phase 1 (범례 클릭)          → tag_ui.py → dashboard.js renderTagLegend → index.html 범례
Phase 2 (사이드바 카테고리)  → views.py 정렬 → index.html SSR regroup → dashboard.js renderTagContainer + availableCategories 저장
```

---

## 이전 계획

> 이전 계획은 2026-04-21 보안 취약점 수정 계획이며, **2026-04-21 완료** 되었다. 요약:
> - Phase 1: 저장형 XSS 수정 (`stats/index.html` `|safe` → `json_script`) ✅
> - Phase 2: 브루트포스 방어 (`django-axes` 추가) ✅
> - Phase 3: CDN SRI Hash 추가 (`base.html` Chart.js/htmx/Alpine.js) ✅
> - 최종 검증: `manage.py check` clean, `pytest` 55 passed
