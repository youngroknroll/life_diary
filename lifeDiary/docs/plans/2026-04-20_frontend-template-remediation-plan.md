# 프론트엔드 템플릿 정비 플랜

> **작성일**: 2026-04-20
> **대상 범위**: `apps/*/templates/**/*.html`, 연관 `views.py` / `templatetags/`
> **배경**: 프론트엔드 전문가 관점 리뷰 — 백엔드-템플릿 정합성, 중복 마크업, 최적화 포인트 발견. 상세 보고 참조.

---

## 0. 원칙

- **Surgical changes**: 리뷰에서 지적된 항목만 수정. 주변 포매팅·주석·스타일 "개선" 금지.
- **Red-Green 검증**: 버그 수정(Phase 1)은 수정 전 재현 → 수정 후 통과 순서로 검증.
- **각 Phase는 독립 커밋**: 순서 보장 외에는 서로 의존하지 않도록 단위화.
- **i18n 정책**: 기존 한글 문자열을 이번 플랜에서 `{% trans %}`로 전환하지 않음. Phase 0 i18n 로드맵 별도 진행.

---

## Phase 1 — 크리티컬 버그: stats "최다 활동 요일" 미표시 (HIGH)

### 문제
- 파일: `apps/stats/templates/stats/index.html:186-190`
- `{% with most_active_day=... %}` 루프 내 재할당으로 최대값 비교 시도
- Django `{% with %}` 태그는 블록 내 재할당 불가 → **항상 첫 요소만 표시**되는 기능 오류

### 조치
1. 템플릿에서 최대값 계산 로직 제거
2. 뷰/로직 계층(`apps/stats/aggregation/` 또는 `apps/stats/logic.py`)에서 `most_active_day` 계산 후 context로 전달
3. 템플릿은 `{{ most_active_day.name }}` / `{{ most_active_day.hours }}` 같은 단순 표시만

### 검증
- 수정 전: 요일별 시간 수기 비교 → 템플릿 출력과 불일치 재현
- 수정 후: 최다 시간 요일이 정확히 표시됨
- 단위 테스트 추가: `apps/stats/test_logic.py` (또는 기존 파일)에서 `get_most_active_day` 케이스

### 수용 기준
- [ ] 버그 재현 테스트 RED → 수정 후 GREEN
- [ ] 기존 stats 관련 테스트 모두 통과
- [ ] 템플릿에서 `{% with %}` 재할당 로직 제거됨

---

## Phase 2 — 중복 마크업 제거: `usergoal_list.html` partial 추출 (HIGH)

### 문제
- 파일: `apps/users/templates/users/usergoal_list.html:19-140`
- 일/주/월 테이블이 동일 구조로 3회 복제 (총 ~120줄 중 80줄 중복)

### 조치
1. 신규 파일: `apps/users/templates/users/_goal_table_section.html`
   - 파라미터: `goals`, `period_label`, `period_code`
2. 기존 3개 섹션을 `{% include %}` 3회로 치환
3. 뷰에서 context에 `daily_goals`, `weekly_goals`, `monthly_goals`를 각각 넘기거나, `goals_by_period` 딕셔너리로 통합

### 수용 기준
- [ ] 렌더링 결과 DOM 동일 (수동 확인 또는 snapshot)
- [ ] `usergoal_list.html` 70% 이상 코드량 감소
- [ ] partial 파일은 context 오염 없이 명시적 파라미터만 사용

---

## Phase 3 — 커스텀 template tag: `tag_badge` (MED)

### 문제
- 태그 배지(색상 + 이름) 마크업이 5개 이상 위치에서 중복
  - `dashboard/index.html:146`
  - `stats/index.html:147, 212, 277, 307`
  - `tags/index.html` (일부)
- `style="background-color: {{ tag.color }};"` + 텍스트 대비 로직이 각각 인라인

### 조치
1. 신규 파일: `apps/core/templatetags/tag_tags.py` (또는 `apps/tags/templatetags/`)
   - `@register.inclusion_tag('partials/_tag_badge.html')`
   - 파라미터: `tag` (필수), `size='sm'|'md'` (선택)
2. 파트ial: `templates/partials/_tag_badge.html`
3. 호출부 5곳 치환: `{% load tag_tags %}` + `{% tag_badge entry.tag %}`

### 수용 기준
- [ ] 5곳 치환 완료
- [ ] 치환 전후 렌더링 결과 동일 (색상·텍스트·크기)
- [ ] templatetags 단위 테스트 1건 추가

---

## Phase 4 — `ai_feedback` include context 명시 전달 (MED)

### 문제
- 파일: `apps/users/templates/users/mypage.html` → `{% include 'stats/ai_feedback.html' %}`
- ai_feedback은 `user_goals_daily/weekly/monthly`를 참조하지만 mypage 뷰(`apps/users/views.py:184-196`)는 해당 키 미전달
- stats/views.py에서만 해당 context 제공 → **mypage에서는 빈 상태로 렌더링**

### 조치 (택1)
**옵션 A**: mypage 뷰에서 stats 로직 재사용해 context 추가 전달
**옵션 B**: ai_feedback 템플릿을 "inclusion_tag"로 전환, 내부에서 자체 계산 (권장)

### 권장: 옵션 B
1. `apps/stats/templatetags/ai_feedback_tags.py` 신규
2. `@inclusion_tag('stats/ai_feedback.html', takes_context=True)` + `user`만 받아 goals 계산
3. 사용처: `{% ai_feedback_panel user %}`

### 수용 기준
- [ ] mypage에서도 ai_feedback 섹션이 정상 데이터로 렌더링
- [ ] stats/index.html에서도 동일 동작 유지
- [ ] 암묵적 context 상속 제거 (include 시 `only` 키워드 사용 검토)

---

## Phase 5 — 인라인 스타일 통합 (LOW)

### 문제
- `mypage.html:4-7`, `usergoal_form.html:4-7` — 동일한 `input[name="target_hours"]` width 규칙 중복
- `dashboard/index.html:111`, `stats/index.html:110` 등 — `style="..."` 인라인 분산

### 조치
1. 공통 스타일은 `static/css/app.css`(또는 기존 공용 CSS)로 이동
2. 동적 색상(`tag.color`)만 인라인 유지. 나머지 크기·간격·폰트는 CSS 클래스로
3. 각 템플릿 head의 `<style>` 블록 제거

### 수용 기준
- [ ] 렌더링 결과 시각적 동일
- [ ] 템플릿 내 `<style>` 블록 수 감소

---

## Phase 6 — 날짜 선택기 공통 partial (LOW)

### 문제
- `apps/dashboard/templates/dashboard/index.html:14-38`
- `apps/stats/templates/stats/index.html:9-29`
- 거의 동일한 날짜 선택 + "오늘" 버튼 마크업

### 조치
1. 신규 파일: `templates/shared/_date_selector.html`
2. 파라미터: `selected_date`, `form_action_url`
3. 두 템플릿에서 `{% include %}`로 치환

### 수용 기준
- [ ] 두 페이지 날짜 선택 동작 동일 유지
- [ ] 마크업 중복 제거

---

## Phase 7 — usernote_form Bootstrap 클래스 적용 (LOW, 일관성)

### 문제
- `apps/users/templates/users/usernote_form.html:7` — `{{ form.as_p }}` 사용으로 Bootstrap 미적용
- signup/login은 뷰에서 `form-control` 수동 주입하는 패턴 사용 중

### 조치
- `apps/users/views.py`의 `usernote_create`/`usernote_update`에서 form 필드에 `form-control` 추가
- 또는 forms.py의 `UserNoteForm`에 `widget=forms.Textarea(attrs={'class': 'form-control'})` 선언 (권장: 선언형)

### 수용 기준
- [ ] 메모 작성/수정 폼이 다른 폼과 시각적 일관성 확보

---

## 우선순위 요약

| Phase | 항목 | 난이도 | 파급 | 성격 |
|-------|------|-------|------|------|
| 1 | stats `{% with %}` 버그 | med | high | **버그** |
| 2 | usergoal_list partial | low | high | 중복 제거 |
| 3 | tag_badge template tag | med | high | DRY |
| 4 | ai_feedback context | med | med | 정합성 |
| 5 | 인라인 스타일 통합 | low | med | 최적화 |
| 6 | 날짜 선택기 partial | low | med | 중복 제거 |
| 7 | usernote Bootstrap | low | low | 일관성 |

---

## 제외 (이번 플랜 밖)

- **i18n `{% trans %}` 전환**: 별도 i18n Phase 로드맵 진행 중. 이번 플랜에서 번역 마커 추가하지 않음.
- **접근성(aria-*)**: 별도 스윕 필요. 본 플랜은 기능·중복·정합성에 집중.
- **Chart.js 리팩터링**: 현재 동작 양호, 명확한 니즈 없음.
- **N+1 배치 쿼리 (stats find_by_period 3회)**: 성능 문제 미확인. 측정 후 별도 처리.

---

## 실행 체크리스트

- [ ] Phase 1: stats 버그 수정 + 회귀 테스트
- [ ] Phase 2: usergoal_list partial 추출
- [ ] Phase 3: tag_badge template tag
- [ ] Phase 4: ai_feedback context 명시화
- [ ] Phase 5: 인라인 스타일 CSS 이전
- [ ] Phase 6: 날짜 선택기 partial
- [ ] Phase 7: usernote form Bootstrap 적용

각 Phase 완료 후 독립 커밋 (`feat(ui):`, `fix(stats):`, `refactor(users):` 등).
