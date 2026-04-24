# 2026-04-24 대시보드 태그 UX 개선 + 통계 탭 상태 보존 실행 로그

> 실행일: 2026-04-24
> 목표: (1) 대시보드 태그 범례 클릭 이벤트 추가 (2) 사이드바 태그 목록 카테고리 그룹화 (3) inline onclick 전면 제거 + XSS 방어 공통화 (4) 통계 페이지 날짜 변경 시 활성 탭 유지

---

## Phase 1 — 대시보드 태그 UX: 범례 클릭 + 카테고리 그룹화

### 변경 파일
- `apps/tags/repositories.py`
- `apps/tags/templatetags/tag_ui.py`
- `apps/dashboard/templates/dashboard/index.html`
- `apps/dashboard/static/dashboard/js/dashboard.js`
- `apps/core/static/core/js/utils.js`

### 문제
1. 그리드 하단 태그 범례(`#tagLegend`) 배지는 display-only로 클릭 불가 → 사용자가 범례에서 바로 태그 선택 불가.
2. 사이드바 태그 목록(`#tagContainer`)이 is_default + name 순으로 flat 출력 → 카테고리 구조(수동적 소비 / 주도적 사용 / 투자 / 기초 생활 / 수면)가 UI에 반영되지 않음.
3. 기존 SSR/CSR 모두 `onclick="selectTag({{id}}, '{{color}}', '{{name}}')"` 형태의 inline onclick에 사용자 입력(태그 이름)을 삽입 → 태그 이름에 validator가 없어 `'` 등 특수문자 주입 시 JS 파싱 파괴 및 XSS 위험.

### 조치

**A. 카테고리 우선 정렬**
- `TagRepository.find_accessible_ordered`: `-is_default, name` → `category__display_order, -is_default, name`
- Category 모델은 `display_order` 기준 정렬이 Meta에 이미 존재

**B. `{% tag_badge %}` 템플릿 태그 확장**
- `clickable=False, tag_id=None` optional 파라미터 추가 (기존 호출자 호환)
- `clickable=True + tag_id` 시 `<button type="button" class="badge btn-tag-legend" data-tag-id="..." data-tag-color="..." data-tag-name="...">` 렌더링
- `format_html` 자동 이스케이프 + data-attr 방식 → inline onclick 없이 안전

**C. SSR 템플릿 (`dashboard/index.html`)**
- 범례: `{% tag_badge ... clickable=True tag_id=tag.id %}` 적용
- 사이드바: `{% regroup user_tags by category as tags_by_category %}` → 카테고리 헤더 + 그룹별 태그 버튼 렌더링
- 사이드바 버튼도 inline onclick 제거, data-tag-* 속성 사용

**D. CSR (`dashboard.js`)**
- `initializeTagSelectDelegation(containerId)` 공용 위임 함수 추출
  - `#tagLegend`, `#tagContainer` 두 곳에 동일 로직 적용
  - `event.target.closest('[data-tag-id]')` → data attrs 파싱 후 `selectTag()` 호출
- `renderTagButton(tag)` 헬퍼 추출 → 중복 제거
- `renderTagContainer(tags)`: `window._categories` 사용해 카테고리별 그룹 + 헤더 출력 (미로드 시 flat 폴백)
- `renderTagLegend(tags)`: `<span>` → `<button>` + data-attr

**E. `escapeHtml` 공용 유틸 추가**
- `core/utils.js`에 `escapeHtml(value)` 추가 (5개 엔티티: `& < > " '`)
- innerHTML 삽입 시 XSS 방어용

### TDD 사이클 (총 10건 신규 테스트)

| Phase | 테스트 | RED → GREEN |
|---|---|---|
| 1 | `find_accessible_ordered` 카테고리 display_order 정렬 | ✓ |
| 2a | `tag_badge` 기본 호출 호환성 (span, no onclick) | ✓ |
| 2b | `tag_badge clickable=True` → button + data-tag-* | ✓ |
| 2c | `tag_badge` 악성 name 이스케이프 | ✓ |
| 3a | 대시보드 페이지 카테고리 헤더 렌더링 | ✓ |
| 3b | 카테고리 헤더 → 태그 버튼 순서 | ✓ |
| 3c | `#tagLegend` 배지에 data-tag-id 존재 | ✓ |
| 4a | 사이드바 버튼 data-attr 사용 + no onclick | ✓ |
| 4b | 사이드바 버튼 악성 name 이스케이프 (onclick/script 없음) | ✓ |

테스트 헬퍼 `_extract_element(html, id)` 추가 — `HTMLParser`로 id 매칭 요소 내부 HTML만 추출 (자식 div 중첩 처리). 외부 요소 onclick과 간섭 방지.

### 영향
- 범례 클릭으로 바로 태그 선택 가능 → 슬롯 선택 후 범례 클릭만으로 저장 가능
- 사이드바에 카테고리 구조 가시화 → 태그가 많아질수록 탐색성 향상
- 태그 이름에 어떤 문자가 들어와도 JS 실행 컨텍스트에 도달하지 않음 → XSS 근본 방어

### 커밋
- `feat(dashboard): 태그 범례 클릭 이벤트 + 사이드바 카테고리 그룹화`
- `docs: prompt_plan.md — 대시보드 태그 UX 계획으로 교체, 이전 보안 계획 아카이브`

---

## Phase 2 — 통계 페이지 날짜 변경 시 활성 탭 유지

### 변경 파일
- `apps/stats/templates/stats/index.html`
- `apps/stats/static/stats/js/stats.js`
- `apps/stats/tests.py`

### 문제
통계 페이지는 일간/주간/월간/태그 분석 4개 탭으로 구성. 날짜 선택기 onchange가 `location.href='?date=' + this.value`로 전체 reload 발동 → Bootstrap 기본 active 탭인 `#daily`로 강제 복귀. 주간·월간 탭을 보던 사용자는 날짜 바꿀 때마다 재클릭 필요.

### 조치

**A. URL hash로 탭 상태 영속화**
- `_date_selector.html`에 전달하는 `ds_onchange`에 `window.location.hash` append
  ```
  ds_onchange="location.href='?date=' + this.value + (window.location.hash || '')"
  ```
- reload 시 `?date=2026-04-24#weekly` 형태로 hash 유지됨

**B. `stats.js` 탭 hash 동기화**
- `initTabHashSync()` 신규 함수:
  - 로드 시 `window.location.hash` 매칭 탭 트리거 탐색 → `bootstrap.Tab(trigger).show()`
  - 탭 전환(`shown.bs.tab`) 시 `history.replaceState`로 hash 갱신 (reload 없이)
- `DOMContentLoaded` 초기화 루틴 앞에 호출

**C. "오늘" 버튼**
- `goToToday()`는 `new URL(window.location)` 사용 → hash 자동 보존됨. 수정 불필요.

### 테스트
- `StatsIndexDatePreservesTabTests.test_date_onchange_preserves_url_hash`: 렌더링된 HTML에 `id="dateSelector"` + `window.location.hash` 포함 확인

### 영향
- 주간/월간/태그 탭 사용자가 날짜를 바꿔도 해당 탭 유지
- 탭 전환은 history에 쌓이지 않음 (`replaceState`) → 뒤로가기 시 탭 스텝 안 거침
- 날짜 변경은 기존대로 history에 기록 (뒤로가기 시 이전 날짜로 복귀 가능)

### 커밋
- `fix(stats): 날짜 변경 시 현재 활성 탭 유지`

---

## 최종 검증

```
pytest          → 66 passed (이전 55 + 신규 11)
manage.py check → no issues
```

### 테스트 증분

| 파일 | 추가 |
|---|---|
| `apps/tags/tests.py` | +5 (정렬 1, tag_badge 3, existing 1 보강) |
| `apps/dashboard/tests.py` | +5 (카테고리 그룹 3, 사이드바 data-attr 2) |
| `apps/stats/tests.py` | +1 (탭 hash 보존) |

---

## 회고

### 잘 된 점
- TDD 사이클을 끝까지 RED → GREEN으로 유지. 중간에 "우연히 통과"한 테스트를 알파벳 순 vs 카테고리 순이 다른 입력으로 교정한 경험이 유효했음.
- 코드 리뷰 단계에서 inline onclick의 XSS 경로를 발견 → 즉시 공통화(data-attr + 위임)로 해결. "그냥 돌아가기만 하면 된다"로 멈추지 않고 근본 수정.
- `tag_badge` 템플릿 태그 확장 시 `clickable=False` 기본값으로 기존 호출자 무중단 호환.

### 개선점
- JS 단위 테스트 환경 부재 → `escapeHtml` 등 유틸 테스트는 수동 확인만. 중기적으로 vitest/jest 도입 검토.
- 통계 탭 상태 보존 기능은 Django TestClient로 표면만 검증. 실제 Bootstrap Tab 활성화 동작은 E2E (Playwright) 범위.

---

**작업 시간**: 2026-04-24 (단일 세션)
