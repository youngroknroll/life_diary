# 대시보드 사이드바 UX 개선

**날짜:** 2026-04-15
**범위:** 선택 정보 통합 · 삭제 버튼 맥락화 · 모바일 접기/펼치기

---

## 배경 (사용자 피드백 원문)

> - 저장/삭제 버튼이 따로 떨어져 있는 기능처럼 보여서, 삭제는 어떤 걸 삭제하는지 인식이 잘 안 된다.
> - 빠른 입력은 하단에 작은 아이콘으로 접을 수 있으면 좋겠다. 기본은 펼침 상태, X 누르면 접혀서 우하단 아이콘으로.
> - "선택된 슬롯" 영역이 따로 떨어져 있어서 여러 번 눌러보고서야 존재 이유를 알게 되었다.
> - 그리드를 선택했을 때 시간/상태 값이 빠른 입력 영역에서 바로 보이면, 그리드 선택 → 빠른 입력 영역 반응이라는 연결을 인식할 수 있다.
> - 삭제도 그리드를 선택했을 때만 활성화되고, 선택이 없으면 비활성.

---

## 수정 사항

### 1. 선택된 슬롯 정보를 빠른 입력 카드 상단에 통합

**기존**: "빠른 입력" 카드와 "선택된 슬롯" 카드가 분리되어 있어 연관성 인지가 어려웠다.

**변경**: 별도 `slotInfoCard`를 제거하고, 빠른 입력 카드 body 최상단에 `slotInfoInline` 영역을 추가했다.

| 상태 | 표시 내용 |
|------|----------|
| 미선택 | "그리드에서 시간을 선택하세요" 안내 문구 + 포인터 아이콘 |
| 단일 슬롯 선택 | 시간, 상태(빈 슬롯/태그명), 메모(있을 경우) |
| 다중 슬롯 선택 | N개 슬롯, 시간 범위, 총 시간 |

그리드를 클릭하면 빠른 입력 영역 상단이 즉시 반응하므로, "그리드 선택 → 사이드바 변화"의 인과관계를 바로 인식할 수 있다.

### 2. 삭제 버튼을 선택 정보 영역 안으로 이동

**기존**: 저장 버튼 아래에 삭제 버튼이 항상 존재 (disabled 상태). 무엇을 삭제하는지 맥락이 불명확.

**변경**: 
- 기존 위치의 삭제 버튼 제거
- 기록이 있는 슬롯을 선택했을 때만 선택 정보 영역 우측에 삭제 버튼이 동적 노출
- 빈 슬롯만 선택한 경우 삭제 버튼 미표시

```
┌─────────────────────────────────┐
│ 시간: 09:00                     │
│ 상태: 업무               [삭제] │  ← 기록 슬롯일 때만 표시
└─────────────────────────────────┘
```

### 3. 모바일 접기/펼치기 (768px 이하)

모바일에서 사이드바가 그리드 아래에 전체 너비로 펼쳐져 공간을 많이 차지하는 문제를 해결했다.

- **접기**: 카드 헤더의 X 버튼 클릭 → 사이드바 숨김, 우하단 FAB(Floating Action Button) 표시
- **펼치기**: FAB 클릭 → 사이드바 복원, FAB 숨김
- **기본 상태**: 펼침
- **데스크톱(992px 이상)**: X 버튼과 FAB 모두 미표시 (`d-lg-none`)

FAB 스타일은 프로젝트 녹색 테마 그라데이션을 적용했다.

---

## 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `apps/dashboard/templates/dashboard/index.html` | slotInfoCard 제거, slotInfoInline 추가, 삭제 버튼 동적 생성, FAB/닫기 버튼 HTML, toggleSidebar() JS, showSlotInfo() 리팩터 |
| `apps/core/static/core/css/style.css` | `.quick-input-fab` 스타일 추가 |

---

## JS 변경 상세

### `showSlotInfo()` — 렌더링 대상 변경 + 삭제 버튼 통합

```javascript
// 기존: slotInfoCard / slotInfo (별도 카드)
// 변경: slotInfoInline (빠른 입력 카드 내부)

const inlineEl = document.getElementById('slotInfoInline');

// 미선택 시 안내 문구
// 선택 시 시간/상태 + (기록 슬롯이면) 삭제 버튼
```

### `updateButtons()` — deleteBtn 로직 제거

삭제 버튼이 `showSlotInfo()` 내에서 동적 생성되므로, `updateButtons()`에서는 saveBtn만 관리한다.

### `toggleSidebar(show)` — 모바일 접기/펼치기

```javascript
function toggleSidebar(show) {
    const sidebar = document.getElementById('quickInputSidebar');
    const fab = document.getElementById('quickInputFab');
    sidebar.style.display = show ? '' : 'none';
    fab.style.display = show ? 'none' : '';
}
```
