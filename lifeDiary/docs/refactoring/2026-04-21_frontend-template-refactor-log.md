# 2026-04-21 프론트엔드 템플릿 정비 실행 로그

> 선행 계획: `docs/plans/2026-04-20_frontend-template-remediation-plan.md`
> 실행 기간: 2026-04-20 ~ 2026-04-21
> 목표: 백엔드-템플릿 정합성 확보, 중복 마크업 제거, 인라인 스타일 통합

---

## Phase 1 — stats "가장 활발한 요일" 버그 수정

### 변경 파일
- `apps/stats/aggregation/weekly.py`
- `apps/stats/templates/stats/index.html`
- `apps/stats/tests.py`

### 문제
`{% with most_active_day=weekly_data.0 %}` 블록 내에서 루프로 `most_active_day`를 재할당 시도.
Django `{% with %}` 태그는 블록 내 재할당을 지원하지 않아 **항상 첫 요일**이 표시되는 기능 오류.

### 조치
`get_weekly_stats_data()` 반환 dict에 `most_active_day` 키 추가:
```python
most_active_day = max(weekly_data, key=lambda d: d["total_minutes"]) if weekly_data else None
```
템플릿에서 broken 루프 제거 → `{{ weekly_stats.most_active_day.day_korean }}` 단순 참조.

### 테스트
```
MostActiveDayTests: 3 passed
전체: 41 passed
```

---

## Phase 2 — usergoal_list partial 추출

### 변경 파일
- `apps/users/templates/users/usergoal_list.html`
- `apps/users/templates/users/_goal_table_section.html` (신규)

### 문제
일/주/월 테이블 섹션 3개가 동일 마크업 구조로 복제 (~80줄 중복).

### 조치
`_goal_table_section.html` partial 신규 생성. 파라미터:

| 파라미터 | 역할 |
|----------|------|
| `section_period` | `daily` / `weekly` / `monthly` 필터 |
| `section_heading` | 섹션 제목 |
| `section_icon` | FontAwesome 아이콘 클래스 |
| `section_subtext` | 괄호 안 보조 설명 |
| `section_mb` | 테이블 하단 margin 클래스 |

```django
{% include "users/_goal_table_section.html" with section_period="daily" section_heading="일간 목표" ... %}
```

**결과**: `usergoal_list.html` 141줄 → 23줄 (83% 감소)

---

## Phase 3 — tag_dot / tag_badge 커스텀 template tag

### 변경 파일
- `apps/tags/templatetags/__init__.py` (신규)
- `apps/tags/templatetags/tag_ui.py` (신규)
- `apps/dashboard/templates/dashboard/index.html`
- `apps/stats/templates/stats/index.html`

### 문제
`<span class="badge me-2" style="background-color: {{ tag.color }};">&nbsp;</span>` 패턴이
dashboard/stats 템플릿 7곳에 중복.

### 조치
`apps/tags/templatetags/tag_ui.py`에 `simple_tag` 2개 등록:

```python
@register.simple_tag
def tag_dot(color):
    """색상 점 배지. {% tag_dot tag.color %}"""

@register.simple_tag
def tag_badge(color, text_color, name):
    """전체 배지. {% tag_badge tag.color tag.text_color tag.name %}"""
```

**설계 결정**: 객체 전체가 아닌 값(color 문자열)을 받도록 설계.
→ `daily_stats.tag_stats`는 dict, `user_tags`는 Tag 모델 인스턴스로 타입이 다르지만,
Django 템플릿의 dot-notation(`tag.color`)이 두 타입 모두 해석하므로 Python 코드에서 분기 불필요.

**치환 위치 (7곳)**:

| 파일 | 태그 |
|------|------|
| `dashboard/index.html:146` | `{% tag_badge tag.color tag.text_color tag.name %}` |
| `dashboard/index.html:221` | `{% tag_dot tag.color %}` |
| `stats/index.html:148, 208, 273, 303, 333` | `{% tag_dot tag.color %}` |

**의도적 유지**:
- `dashboard/index.html:112` — `slot.data.tag.color` 동적 div 배경색 (badge 아님)
- `tags/index.html:62` — JavaScript 템플릿 리터럴 (Django tag 적용 불가)

---

## Phase 4 — ai_feedback → life_feedback 명칭 변경

### 변경 파일
- `apps/stats/feedback.py` → `apps/stats/life_feedback.py` (rename)
- `apps/stats/templates/stats/ai_feedback.html` → `life_feedback.html` (rename)
- `apps/stats/views.py`

### 조치
파일명, import 경로, include 경로 일괄 변경.
`mypage.html`에 life_feedback include 없음 확인 — 범위 축소 (context 명시화 불필요).

---

## Phase 5 — 인라인 스타일 CSS 통합

### 변경 파일
- `apps/core/static/core/css/style.css`
- `apps/stats/templates/stats/index.html`
- `apps/stats/templates/stats/life_feedback.html`
- `apps/dashboard/templates/dashboard/index.html`
- `apps/users/templates/users/mypage.html`
- `apps/users/templates/users/usergoal_form.html`
- `apps/users/templates/users/usernote_list.html`
- `apps/users/templates/users/_goal_table_section.html`

### 추가 CSS 클래스 (style.css)

| 클래스 | 값 | 적용 위치 |
|--------|-----|----------|
| `.date-input-sm` | `width: 150px` | stats + dashboard date input |
| `.chart-container` | `height: 300px` | stats 차트 캔버스 5곳 |
| `.chart-container-lg` | `height: 400px` | stats 주간 차트 |
| `.tag-stats-list` | `max-height: 200px; overflow-y: auto` | 일별 태그 목록 |
| `.tag-analysis-scroll` | `height: 300px; overflow-y: auto` | 태그 분석 패널 |
| `.life-feedback-card` | `min-width: 350px; max-width: 400px` | feedback 카드 |
| `.goal-guide-panel` | `var(--color-primary-soft)` + radius | mypage 안내 패널 |
| `.goal-guide-toggle` | `var(--color-text-muted)` + bold | 안내 토글 버튼 |

### Bootstrap 유틸리티 교체 (5건)

| 인라인 스타일 | 교체 |
|---------------|------|
| `display:inline` | `d-inline` (forms 2곳) |
| `display:flex; align-items:center; gap:10px` | `d-flex align-items-center gap-2` (2곳) |
| `margin-left: 0.5rem` | `ms-2` |

### 의도적 유지
- `background-color: {{ slot.data.tag.color }}` — 동적 값
- `color: {{ slot.data.tag.text_color }}` — 동적 값
- `display: none` (JS 토글 대상)

---

## Phase 6 — 날짜 선택기 공통 partial

### 변경 파일
- `templates/shared/_date_selector.html` (신규)
- `apps/dashboard/templates/dashboard/index.html`
- `apps/stats/templates/stats/index.html`

### 문제
dashboard/stats의 날짜 선택기 + 오늘 버튼 + 목표 확인 버튼 마크업이 거의 동일하게 중복.

### 차이점 처리

| 파라미터 | dashboard | stats |
|----------|-----------|-------|
| `ds_onchange` | 없음 (JS 처리) | `"location.href='?date=' + this.value"` |
| `ds_mypage_label` | `"목표 추가"` | `"목표 확인"` |

`selected_date`, `user`는 부모 context 자동 상속.

```django
{# dashboard #}
{% include "shared/_date_selector.html" with ds_mypage_label="목표 추가" %}

{# stats #}
{% include "shared/_date_selector.html" with ds_onchange="location.href='?date=' + this.value" ds_mypage_label="목표 확인" %}
```

---

## Phase 7 — usernote_form Bootstrap 적용

### 변경 파일
- `apps/users/forms.py`
- `apps/users/templates/users/usernote_form.html`

### 문제
`UserNoteForm`의 Textarea widget에 `form-control` 클래스 미설정 → `form.as_p` 렌더링으로 Bootstrap 스타일 미적용.
signup/login 폼과 시각적 일관성 깨짐.

### 조치
`forms.py` widget 선언에 `class: "form-control"` 추가 (뷰 수정 불필요):
```python
"note": forms.Textarea(
    attrs={"rows": 4, "placeholder": "...", "class": "form-control"}
)
```
템플릿: `form.as_p` → 명시적 필드 렌더링으로 변경.

---

## 최종 테스트

```
41 passed (전 Phase 완료 후 통합 실행)
```

## 변경 파일 요약

| 분류 | 파일 수 |
|------|---------|
| 신규 생성 | 5개 (`_goal_table_section.html`, `templatetags/`, `_date_selector.html`, `life_feedback.py`, `life_feedback.html`) |
| 수정 | 11개 |
| 삭제 (rename) | 2개 (`feedback.py`, `ai_feedback.html`) |
