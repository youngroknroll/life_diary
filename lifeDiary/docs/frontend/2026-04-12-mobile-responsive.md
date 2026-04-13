# 모바일 대시보드 반응형 개선

**날짜:** 2026-04-12
**범위:** 터치 스크롤/선택 분리 · 시간 헤더 반응형 · 날짜/통계 영역 반응형

---

## 배경

모바일(768px 이하)에서 대시보드 사용 시 두 가지 문제가 있었다.

1. **스크롤 불가** — 타임 그리드 슬롯의 `ontouchstart`/`ontouchmove`에서 `event.preventDefault()`를 무조건 호출하여 브라우저 기본 스크롤이 차단됨. 그리드가 화면 대부분을 차지하므로 페이지 상하 이동이 사실상 불가능.
2. **고정 레이아웃** — 날짜 카드 헤더(날짜 + 버튼), 통계 영역(4열), 시간 헤더(12열)가 데스크톱 레이아웃 그대로 유지되어 모바일에서 넘침/겹침 발생.

---

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `apps/dashboard/templates/dashboard/index.html` | 터치 핸들러 분리, 헤더 클래스 추가, 통계 그리드 반응형 |
| `apps/core/static/core/css/style.css` | touch-action, 헤더 숨김, 날짜/통계 반응형 스타일 |

---

## 변경 상세

### 1. 터치 방향 감지 — 스크롤/선택 분리

**문제:** `startDrag()`에서 `event.preventDefault()` 호출 → 모든 터치가 슬롯 선택으로 처리.

**해결:**
- `handleTouchStart(slotIndex, event)` 신규 함수: 터치 시작 좌표(`touchStartX`, `touchStartY`)를 기록하되 `preventDefault()` 호출하지 않음.
- `handleTouchMove(event)` 수정: 5px 이상 이동 시 방향 판단.
  - `|deltaY| > |deltaX|` → **세로 스와이프** → 드래그 취소, 브라우저 스크롤 허용
  - `|deltaX| >= |deltaY|` → **가로 스와이프** → 슬롯 선택 모드, `preventDefault()` 호출
- `startDrag()`에서 `event.preventDefault()` 제거 (마우스 전용).
- CSS: `.time-grid`에 `touch-action: pan-y` 추가 (768px 이하).

**인라인 핸들러 변경:**
```
Before: ontouchstart="startDrag({{ slot.index }})"
After:  ontouchstart="handleTouchStart({{ slot.index }}, event)"
```

### 2. 시간 헤더 반응형

**문제:** 시간 헤더가 인라인 `style="grid-template-columns: repeat(12, 1fr)"` 고정 → 모바일 6열 전환 시에도 12개 표시.

**해결:**
- 인라인 스타일 제거, `.time-grid` 클래스 공유로 미디어쿼리 자동 반응.
- 768px 이하에서 `.time-header-cell:nth-child(n+7) { display: none }` → 뒷 6개(중복) 숨김.
- 결과: 모바일에서 "10분 20분 30분 40분 50분 60분" 6개만 표시.

### 3. 날짜 카드 헤더 반응형

**문제:** `d-flex justify-content-between`으로 날짜 텍스트와 버튼이 한 줄 고정 → 모바일에서 넘침.

**해결:**
- `.dashboard-date-header` 클래스 부여.
- 데스크톱: `display: flex; justify-content: space-between; align-items: center` (기존과 동일).
- 768px 이하: `flex-direction: column; gap: 0.5rem` → 세로 배치.
- `.dashboard-date-title` 폰트 `1rem`으로 축소.
- 버튼 그룹에 `flex-wrap` 추가.

### 4. 통계 영역 반응형

**문제:** `col-md-3` 4열 → 모바일에서 세로 1열로 길어짐.

**해결:**
- `col-md-3` → `col-6 col-md-3 mb-2` → 모바일에서 2x2 그리드.
- 768px 이하: 값 폰트 `0.9rem`, 라벨 폰트 `0.7rem`으로 축소.

---

## 추가된 CSS 규칙 요약

```css
/* 데스크톱 기본 */
.dashboard-date-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* 768px 이하 추가분 */
@media (max-width: 768px) {
    .time-grid { touch-action: pan-y; }
    .time-header-cell:nth-child(n+7) { display: none; }
    .dashboard-date-header { flex-direction: column; gap: 0.5rem; }
    .dashboard-date-title { font-size: 1rem; }
    .dashboard-stats .fw-bold { font-size: 0.9rem; }
    .dashboard-stats small { font-size: 0.7rem; }
}
```

---

## 검증 방법

1. 브라우저 개발자 도구 모바일 뷰(375px)에서 세로 스와이프 → 페이지 스크롤 동작 확인
2. 모바일 뷰에서 가로 스와이프 → 슬롯 드래그 선택 동작 확인
3. 시간 헤더 6개만 표시되는지 확인
4. 날짜 카드 헤더, 통계 영역 세로/축소 배치 확인
5. 데스크톱에서 기존 레이아웃 및 마우스 드래그 정상 동작 확인
6. `python manage.py test apps.dashboard` — 3개 테스트 통과
