# 인라인 JS 정적 파일 추출 + 버그 수정 + UI 통일

> 날짜: 2026-04-15
> 상태: 구현 완료 (로컬 검증 완료, 배포 대기)

## 배경

1. 태그 페이지에서 `utils.js`의 `defer` 로딩 타이밍으로 `getContrastTextColor is not defined` 오류 발생
2. 태그 페이지를 API 호출 방식으로 전환하여 해결
3. 전체 프로젝트의 인라인 JS를 정적 파일로 추출하고 API 패턴 정규화
4. 통계 페이지 UI를 대시보드와 통일

## 변경 요약

**912줄 삭제, 96줄 추가** (템플릿 기준, 새 정적 파일 제외)

## 1. 버그 수정

### `getContrastTextColor is not defined` (태그 페이지)

- **원인**: `staticfiles/core/js/utils.js`가 `collectstatic` 미실행으로 이전 버전(함수 없는) 서빙
- **수정**: `staticfiles/core/js/utils.js` 최신 버전으로 동기화
- **근본 해결**: 태그 페이지를 서버 렌더링(`initialTags`) → API 호출(`fetchAndRenderTags`)로 전환하여 `defer` 타이밍 이슈 자체를 제거

### Stats JSON 파싱 오류

- **원인**: `<script type="application/json">` 안에서 `{{ daily_stats_json }}` 출력 시 Django 자동 이스케이프가 `"`를 `&quot;`로 변환
- **수정**: `{{ daily_stats_json|safe }}` 필터 적용 (`type="application/json"`은 브라우저가 실행하지 않으므로 XSS 위험 없음)

## 2. 인라인 JS → 정적 파일 추출

### Phase 1: Dashboard JS (~390줄)

| 항목 | 내용 |
|------|------|
| 추출 대상 | 슬롯 선택/드래그, 저장/삭제, 태그 렌더링, 사이드바 토글 등 18개 함수 |
| 생성 파일 | `apps/dashboard/static/dashboard/js/dashboard.js` |
| Django URL 처리 | `{% url 'tags:index' %}` → `data-tags-url` HTML 속성으로 전달 |
| fetch 정규화 | `fetch('/api/categories/')` → `apiCall('/api/categories/')` |

### Phase 2: Stats JS (~353줄)

| 항목 | 내용 |
|------|------|
| 추출 대상 | Chart.js 렌더 함수 6개 (`renderDailyPieChart` 등) |
| 생성 파일 | `apps/stats/static/stats/js/stats.js` |
| 데이터 전달 | `<script id="stats-data" type="application/json">` 패턴 사용 |
| API 생성 | 없음 — 서버 렌더링 JSON blob 유지 (불필요한 DB 호출 방지) |

### Phase 3: Goals JS 중복 제거 (~60줄)

| 항목 | 내용 |
|------|------|
| 추출 대상 | `updateTargetHoursMax()` (mypage.html + usergoal_form.html 동일 코드) |
| 생성 파일 | `apps/users/static/users/js/goals.js` |
| 버그 수정 | period select `change` 이벤트 리스너 추가 (기존 누락) |

### Phase 4: Tags fetch 정규화

- `tags/index.html`의 raw `fetch()` → `apiCall()` 래퍼로 전환
- `Promise.all` 패턴 유지, 에러 처리 `apiCall` 내장 기능 활용

### Phase 5: Dead code 제거

- `stats/ai_feedback.html`: `#aiFeedbackToast` 타겟 Toast JS 제거 (해당 ID 요소 미존재)

## 3. 뷰 정리

### `tags/views.py` — `index()` 간소화

```python
# Before: 서버에서 tags_json, categories_json 직렬화
context = {
    "tags": tags,
    "categories": categories,
    "tags_json": serialize_for_js([...]),
    "categories_json": serialize_for_js([...]),
}

# After: API 호출로 대체, 뷰는 빈 셸만 렌더링
return render(request, "tags/index.html")
```

- 미사용 `serialize_for_js` import 제거

### `dashboard/views.py` — dead code 제거

- `tags_json` 직렬화 제거 (템플릿에서 미사용 dead code)
- `categories_json` 직렬화 + `_category_repo.find_all()` DB 호출 제거 → API 전환
- 미사용 import 정리: `CategoryRepository`, `serialize_for_js`

## 4. UI 통일 (통계 ↔ 대시보드)

### 날짜 카드 헤더

| 항목 | Before (통계) | After (대시보드 통일) |
|------|---------------|----------------------|
| CSS 클래스 | 일반 `d-flex` | `dashboard-date-header` / `dashboard-date-title` |
| 날짜 표시 | `Y년 m월` | `Y년 m월 d일 (l)` (요일 포함) |
| 레이아웃 | `d-flex gap-2` | `d-flex gap-2 flex-wrap` (모바일 대응) |
| 목표 버튼 | 항상 표시 | `is_authenticated and not is_superuser` 조건 |

### 통계 슬롯 카드

| 항목 | Before | After |
|------|--------|-------|
| row 클래스 | `row text-center` | `row text-center dashboard-stats` |
| col 클래스 | `col-md-3` | `col-6 col-md-3 mb-2` (모바일 2열) |

## 생성/수정 파일 전체 목록

### 새 파일 (4개)

| 파일 | 설명 |
|------|------|
| `apps/dashboard/static/dashboard/js/dashboard.js` | 대시보드 인터랙션 로직 |
| `apps/stats/static/stats/js/stats.js` | Chart.js 차트 렌더링 |
| `apps/users/static/users/js/goals.js` | 목표 시간 최대값 자동 조절 |
| `docs/refactoring/2026-04-15-inline-js-extraction.md` | 이 문서 |

### 수정 파일 (11개)

| 파일 | 변경 내용 |
|------|-----------|
| `apps/dashboard/templates/dashboard/index.html` | 인라인 JS 390줄 제거 → `<script src>`, `data-tags-url` 추가 |
| `apps/dashboard/views.py` | `tags_json`, `categories_json` 제거, import 정리 |
| `apps/stats/templates/stats/index.html` | 인라인 JS 353줄 제거 → JSON 데이터 블록 + `<script src>`, UI 통일 |
| `apps/stats/templates/stats/ai_feedback.html` | dead code Toast JS 제거 |
| `apps/tags/templates/tags/index.html` | API 호출 방식 전환, raw fetch → apiCall |
| `apps/tags/views.py` | `index()` 간소화, 미사용 import 제거 |
| `apps/users/templates/users/mypage.html` | 인라인 JS 제거 → `<script src>` |
| `apps/users/templates/users/usergoal_form.html` | 인라인 JS 제거 → `<script src>` |
| `staticfiles/core/js/utils.js` | `getContrastTextColor` 포함 최신 버전 동기화 |
| `staticfiles/core/css/style.css` | dashboard-date-header 스타일 (이전 커밋) |
| `templates/base.html` | `utils.js` defer 유지 확인 |

## 아키텍처 결정 기록

### Stats API를 생성하지 않은 이유

`stats/logic.py`가 4개 통계를 1회 계산하여 JSON 직렬화. API 생성 시:
1. 동일 계산 로직이 뷰와 API에 중복
2. 날짜 변경 시 전체 페이지 리로드 (SPA 아님)
3. 추가 DB 호출 발생

**결론**: 서버 렌더링 JSON blob 유지, 차트 코드만 정적 파일로 추출

### 새 API 엔드포인트 0개

기존 `/api/tags/`, `/api/categories/`, `/api/time-blocks/`만 사용. 불필요한 서버/DB 호출 없음.
