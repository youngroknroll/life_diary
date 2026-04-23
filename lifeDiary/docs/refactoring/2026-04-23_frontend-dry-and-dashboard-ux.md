# 2026-04-22 ~ 23 프론트엔드 DRY 리팩터링 + 대시보드 UX 개선 실행 로그

> 실행 기간: 2026-04-22 ~ 2026-04-23
> 목표: (1) POST 폼 스피너/오버레이 UX 정비 (2) 대시보드 기능 버그·UX 개선 (3) 프론트엔드 중복 마크업·JS 로직 공통화 (4) 리뷰 후속 잠복 버그 수정

---

## Phase 0 — POST 폼 전역 로딩 스피너

### 변경 파일
- `templates/base.html`
- `apps/users/templates/users/signup.html`

### 문제
페이지별로 submit 스피너를 개별 인라인 스크립트로 관리 → 대다수 폼은 피드백 없이 네트워크 대기.

### 조치
`base.html`에 document-level `submit` 핸들러 추가:
- `e.submitter`로 클릭된 제출 버튼 특정 → `setButtonLoading()` 자동 적용
- AJAX 폼(`preventDefault` 호출)은 `e.defaultPrevented`로 스킵
- `data-no-loading` 속성으로 개별 폼 opt-out
- `signup.html`의 중복 인라인 스크립트 제거

### 영향
로그인·회원가입·로그아웃·목표/노트 CRUD·삭제 확인 페이지 등 모든 POST 폼에 자동 스피너 적용. 마이페이지 AJAX 목표 추가는 자체 핸들러가 UI 관리하므로 제외.

### 커밋
- `9cd2dc8 feat(ui): 모든 POST 폼 제출 버튼에 전역 로딩 스피너 적용`

---

## Phase 1 — 시간블록 삭제 시 통계 캐시 무효화 누락 수정

### 변경 파일
- `apps/dashboard/use_cases.py`

### 문제
`UpsertTimeBlocksUseCase`는 `invalidate_stats_cache` 호출이 있었으나 `DeleteTimeBlocksUseCase`에는 누락. 삭제 후에도 통계 페이지가 TTL(오늘 5분 / 과거 24시간) 동안 구(舊) 데이터를 반환.

### 조치
`DeleteTimeBlocksUseCase.execute` 말미에 `invalidate_stats_cache(cmd.user_id, cmd.target_date)` 추가.

### 커밋
- `c7207fe fix(dashboard): 시간블록 삭제 시 통계 캐시 무효화 누락 수정`

---

## Phase 2 — 대시보드 저장/삭제 오버레이 + 드래그 선택 개선

### 변경 파일
- `apps/dashboard/static/dashboard/js/dashboard.js`
- `apps/dashboard/templates/dashboard/index.html`

### 2-1. 저장/삭제 시 전체화면 오버레이
`base.html`의 `#loadingOverlay` DOM을 재사용. 아이콘 구분(저장=`fa-save`, 삭제=`fa-trash`). 성공 시 오버레이 유지 → 1초 후 리로드 (빈 화면 없음). 실패 시 오버레이 숨김 + 에러 알림.

### 2-2. 드래그 선택 로직 개선

| 드래그 형태 | 이전 | 이후 |
|---|---|---|
| 대각선/가로 (00:00 → 02:10) | 사각형 영역 `{0,1,12,13}` 4칸 | 시작~끝 연속 `{0..13}` 14칸 |
| 세로 (같은 열) | 그대로 | 해당 열 각 블록만 (기존 유지) |

판정: `startPos.col === endPos.col && startPos.row !== endPos.row` → 세로 분기, 외에는 연속 범위.

### 2-3. Ctrl/Cmd + 드래그 다중 선택
- `startDrag(slotIndex, event)`로 이벤트 인자 추가 (템플릿도 `onmousedown="startDrag({{ slot.index }}, event)"`로 갱신)
- Ctrl/Cmd 감지 → `isAdditiveDrag` 플래그 + `dragBaseSelection` 스냅샷
- 추가 모드에서는 `clearSelection()` 생략, `dragOver`에서 스냅샷 복원 후 범위 추가
- Ctrl+클릭 단일 토글: `dragOver` 미호출 → 기존 `selectSlot` 토글 로직 그대로 작동

### 커밋
- `2c0fc5d feat(dashboard): 저장/삭제 오버레이 + 드래그 선택 개선`

---

## Phase 3 — 프론트엔드 DRY 리팩터링 (6단계)

### 공통 목표
반복되는 템플릿 블록·JS 로직을 공용 partial / 헬퍼로 수렴. 향후 UX·스타일 변경 시 단일 진입점 확보.

### 단계 1 — 삭제 확인 공통화

**신규**
- `templates/shared/confirm_delete.html` (베이스 페이지: title/body/cancel_url 블록)
- `utils.js`: `confirmDelete(message)` 헬퍼 (네이티브 confirm 래퍼)

**변경 6곳**
- `usergoal_confirm_delete.html`, `usernote_confirm_delete.html` → 베이스 상속으로 간소화
- `_goal_table_section.html`, `usernote_list.html` (onclick), `tag.js`, `dashboard.js` (JS 호출) → `confirmDelete()` 사용

**효과**: 향후 커스텀 모달 교체 시 단일 진입점 확보.

커밋: `29f7355`

---

### 단계 2 — 폼 필드 에러 렌더링 공용 partial

**신규**
- `templates/shared/_field_errors.html`: `{% if field.errors %}<div class="text-danger">{{ field.errors }}</div>{% endif %}`

**변경 7곳**: `usergoal_form.html` ×3, `usernote_form.html` ×1, `mypage.html` ×3 → `{% include 'shared/_field_errors.html' with field=form.X %}`

**제외**: `signup.html`, `login.html`은 `{% else %}` 헬프텍스트 분기가 달라 공통화 부적합 (과도한 추상화 방지).

커밋: `1f2586e`

---

### 단계 3 — `apiCall` 확장 + `goals.js` 마이그레이션

**`apiCall` 확장 (`utils.js`)**
- `body` 옵션: FormData 등 원본 body 전달 (JSON 직렬화 스킵)
- `responseType`: `'json' | 'text' | 'none'` — HTML partial, 204 대응
- 에러 객체에 `err.status`, `err.data`(파싱된 응답 바디) 부착 → 구조화 에러 접근 가능
- `Content-Type: application/json`은 데이터가 있을 때만 자동 지정

**`goals.js` 마이그레이션**
- 직접 `fetch` 2회 호출 → `apiCall` 2회 (POST FormData + GET partial HTML)
- CSRF 수동 추출 제거 (apiCall이 쿠키에서 처리)
- 상태 관리를 `setStatus(text, kind)` 헬퍼로 집중
- 원래 분기 보존: 204 성공 / 4xx 폼 에러(`{errors}`) / 네트워크 오류

커밋: `9274973`

---

### 단계 4 — 로딩 오버레이 헬퍼 공용화

**신규 (utils.js)**
- `showOverlay(message, icon)` / `hideOverlay()`

**변경**
- `dashboard.js`: 로컬 `showSavingOverlay/hideSavingOverlay` 17줄 제거, 호출부 4곳 교체
- `login.html`: 인라인 DOM 조작 6줄 → 1줄 `showOverlay('로그인 중입니다...', 'fa-sign-in-alt')`

**base.html은 건드리지 않음**: 인라인 스크립트가 HTML 파싱 중 `showLoadingOverlay()`를 즉시 호출하는데 `utils.js`는 `defer`라 이때 미로드. 이름 분리(페이지 네비 = `showLoadingOverlay`, 액션 = `showOverlay`)로 의미도 구분.

커밋: `78701ad`

---

### 단계 5 — 테이블 액션 버튼 공용 partial

**신규**
- `templates/shared/_table_row_actions.html`: `edit_url`, `delete_url`, `edit_class`(기본 `btn-outline-primary`) 파라미터

**변경 2곳**
- `_goal_table_section.html`: 7줄 → 4줄 (`{% url ... as %}` 2개 + `{% include %}`)
- `usernote_list.html`: 7줄 → 4줄 (`edit_class='btn-warning'` 전달)

커밋: `e2b3750`

---

### 단계 6 — stats.js 차트 헬퍼 추출

**신규 (stats.js 모듈 로컬)**
- `prepareChart(canvasId, key)`: canvas context 획득 + 기존 Chart.js 인스턴스 destroy
- `drawEmptyState(ctx, message)`: 데이터 없을 때 canvas 중앙 placeholder 텍스트

**변경**
- 6개 차트 함수의 전처리(2줄) → 1줄
- 3개 차트의 빈상태 블록(5줄) → 1줄
- 파일 크기: 320줄 → 305줄 (-15 순감)

**`utils.js` 승격 안 한 이유**: stats.js 전용 로직 + Chart.js `charts` 전역 맵 참조. 다른 파일에서 쓸 일 생기면 그때 분리(YAGNI).

커밋: `d825141`

---

## Phase 4 — 기술 리뷰 후속 수정 (잠복 버그 3건)

### 변경 파일
- `apps/core/static/core/js/utils.js`
- `apps/dashboard/static/dashboard/js/dashboard.js`

### Issue 1 — `apiCall` + 204 + `responseType` 타입 불일치
- 이전: 204/`'none'` 응답에서 항상 `{ok, status}` 객체 반환 → text 호출자가 `innerHTML = result` 하면 `"[object Object]"` 렌더
- 수정: `responseType === 'text'` → `''`, `'json'` → `null`, `'none'` → 기존 객체 유지

### Issue 2 — 저장/삭제 성공 후 1초 공백 중복 제출 위험
- 이전: `apiCall` finally에서 버튼 재활성화 → 리로드까지 1초간 Enter 키로 재제출 가능 (오버레이가 마우스는 막지만 키보드 포커스는 살아있음)
- 수정:
  - `saveSlot`: 성공 후 `saveBtn.disabled = true` 재고정
  - `deleteSlot`: 성공 후 `selectedSlots.clear() + updateButtons()` → 저장 버튼 자동 비활성

### Issue 3 — `showOverlay` `innerHTML` 조합 XSS 소지
- 이전: ``text.innerHTML = `<i class="fas ${icon} me-2"></i>${message}` ``
- 현재 호출자는 하드코딩 문자열만 전달해 즉각 위험 없음. 향후 다국어·사용자 입력 유입 대비 방어
- 수정: 아이콘만 `innerHTML`, message는 `document.createTextNode`로 분리 후 appendChild

### 커밋
- `9d81f24 fix(frontend): 기술 리뷰 후속 — apiCall 204 타입, 중복 제출, XSS 소지`

---

## 누적 성과 요약

### 신규 공용 자산

| 유형 | 경로 | 용도 |
|---|---|---|
| Template | `templates/shared/confirm_delete.html` | 삭제 확인 페이지 베이스 |
| Template | `templates/shared/_field_errors.html` | 폼 필드 에러 렌더 |
| Template | `templates/shared/_table_row_actions.html` | 테이블 수정/삭제 버튼 행 |
| JS | `utils.js` `confirmDelete(message)` | 삭제 확인 다이얼로그 |
| JS | `utils.js` `showOverlay(message, icon)` / `hideOverlay()` | 액션 로딩 오버레이 |
| JS | `utils.js` `apiCall` (확장) | `body`/`responseType`/`err.data` 지원 |
| JS | `stats.js` `prepareChart(canvasId, key)` / `drawEmptyState(ctx, msg)` | 차트 전처리·빈상태 |

### 인프라 개선
- 모든 POST 폼에 자동 submit 스피너 (`base.html` document-level 핸들러)
- 오버레이 일원화: 페이지 네비 vs 액션 두 구분된 진입점

### 기능 개선
- 대시보드 시간블록 삭제 후 통계 즉시 반영 (캐시 동기화)
- 드래그 대각선/가로 → 시간 연속 범위 선택
- Ctrl/Cmd + 드래그 → 다중 범위 선택

### 잠복 버그 제거
- `apiCall` 204 + responseType 타입 불일치
- 저장/삭제 성공 후 키보드 Enter 중복 제출
- `showOverlay` message innerHTML XSS 소지

### 테스트
모든 Django pytest 통과 (54건, 사전 존재 홈 카피 테스트 1건은 템플릿 동기화로 수정 후 통과).

---

## 브라우저 수동 확인 체크리스트

- [ ] 로그인/회원가입/로그아웃: submit 버튼 스피너 + 로그인 오버레이 표시
- [ ] 대시보드 저장/삭제: "저장/삭제 중입니다..." 오버레이 → 성공 후 1초간 Enter 재시도해도 무반응
- [ ] 대시보드 드래그
  - [ ] 00:00 → 02:10 대각선: 00:00~02:10 모든 블록 선택
  - [ ] 세로 드래그: 같은 열 블록만 선택 (중간 시간 비움)
  - [ ] Ctrl/Cmd + 드래그: 기존 선택 유지하며 추가
- [ ] 마이페이지 목표 추가(AJAX): 성공 시 목록 갱신, 의도적 에러 시 필드별 메시지
- [ ] 통계 페이지: 6개 차트 정상 렌더, 데이터 없는 경우 "데이터가 없습니다" placeholder
- [ ] 목표/노트 수정·삭제: confirm 다이얼로그 정상, 삭제 후 목록 갱신
- [ ] devtools console: `showOverlay('<script>alert(1)</script>', 'fa-save')` → 스크립트 미실행, 문자 그대로 표시

---

## 관련 메모리 업데이트

- `feedback_commit.md` 확장: Conventional Commits + 한글 본문 + 관심사별 분리 커밋 스타일 확정
- `feedback_no_dev_db_writes.md` 신규: 검증 스크립트에서 dev DB 쓰기 금지 (pytest 격리 또는 transaction rollback 사용)
