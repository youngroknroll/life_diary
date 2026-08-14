# 그리드 태그 라벨 위치와 시간축 경계 표기 계획

작성일: 2026-08-14
브랜치: `deploy-csrf` 에서 분기한 `feat/grid-label-and-hour-axis` (신규)

## 사용자 요구

1. 태그를 저장하면 태그 이름이 **저장된 첫 블록**에 표시되어야 한다.
   예: 05:40~06:50 에 "수면"을 저장하면 05:40 블록에 "수면"이 보여야 한다.
2. 그리드 세로축이 00~23 으로 끝나 하루가 23시에 끝나는 것처럼 읽힌다.
   00~24 로 읽히게 한다.

## 현재 동작과 원인

### 라벨 위치

`apps/dashboard/services.py:89-107` `_assign_labels` 는 한 구간(stretch)의 라벨을
**폭이 `MIN_LABEL_SPAN`(3) 이상인 첫 행 조각**에 붙인다.

05:40~06:50 은 5시 행에서 조각이 2칸뿐이라 건너뛰고, 6시 행(6칸)이 라벨을 가져간다.
사용자가 본 증상 그대로다.

이 예외는 "좁은 첫 행이 라벨을 가져가면 이름이 통째로 사라진다"는 우려에서 나왔다
(`services.py:90-93` 독스트링). 지금은 `.slot-block__label` 이 nowrap + ellipsis 이고
전체 이름은 항상 `title` 에 들어가므로, 좁은 블록에서도 이름이 사라지지 않고 잘려 보인다.
사용자의 예시(2칸 블록에 "수면")가 이 예외를 명시적으로 뒤집는다.

### 시간축

세로축은 각 행에 `00:00`~`23:00` 을 찍는다(`_day_row.html:8`). 라벨은 이미
`align-items: start` 로 행 위쪽에 붙어 "이 띠가 시작하는 선"으로 읽히게 되어 있다
(`style.css:1391-1398` 주석). 빠진 것은 마지막 띠가 끝나는 선, 즉 `24:00` 하나다.

가로 분축은 같은 문제를 이미 해결해 두었다 — 6칸에 눈금 7개(`:00`…`:60`,
`services.py:11-18`). 세로축만 그 규칙을 따르지 않고 있다.

## 승인 범위

### A. 라벨을 구간의 첫 블록으로 (백엔드)

`_assign_labels` 에서 `MIN_LABEL_SPAN` 게이트와 상수를 제거한다. 구간 중복 방지
(`labelled_stretches` + `_stretch_start`)는 그대로 둔다. 결과적으로 라벨은 항상
구간의 첫 슬롯을 담은 블록에 붙는다.

### B. 변이 응답 갱신 범위 확장 (백엔드) — A 의 필연적 후속

A 이후에는 저장 한 번이 **건드리지 않은 시간대의 라벨**을 옮길 수 있다.

재현: 6:00~6:50 에 "수면"을 저장(6시 행에 라벨) → 이어서 5:40~5:50 에 같은 태그 저장.
구간 시작이 5시로 옮겨가 서버는 5시에 라벨을, 6시에 빈 라벨을 계산한다. 그런데
`views.py:69` 는 `hours_touched([34,35]) == [5]` 만 직렬화해 돌려주므로 클라이언트는
5시 행만 다시 그린다. **6시 행에 옛 라벨이 남아 "수면"이 두 번 보인다.**

`hours_touched` 를 `hours_to_refresh` 로 바꾸고 앞뒤 한 시간씩 확장(0~23 clamp)한다.
구간 시작은 변이 경계에서 한 시간을 넘어 움직일 수 없으므로 ±1 로 충분하다.

이 항목을 빼면 A 는 위 흐름에서 눈에 보이는 버그를 남긴다. 범위에서 제외하려면
사용자 결정이 필요하다.

### C. 세로축 24:00 경계 (프론트엔드)

`#timeGrid` 의 **마지막 자식**으로 경계 행 하나를 추가한다.

```django
<div class="day-row" aria-hidden="true">
    <div class="day-row__label">24:00</div>
    <div class="day-row__cells"></div>
</div>
```

- `data-hour` 없음 → 모든 JS 셀렉터가 `.day-row[data-hour]` 로 스코프되어 있어 무시된다.
- `.day-grid` 안에 두어 행 간 `gap: 3px` 리듬을 그대로 상속한다.
- `.day-row__label` 을 그대로 재사용한다. CSS 변경 없음.
- `24:00` 은 숫자이므로 `{% trans %}` 대상이 아니다.

### 명시적 제외

- `.slot-block` / `.slot-block__label` CSS 변경 없음. 좁은 블록용 별도 폰트·패딩·
  최소 폭 모디파이어를 만들지 않는다.
- `_merge_hour_runs`, `_stretch_start`, `serialize_rows`, JS 선택·드래그·키보드 로직 불변.
- 행 라벨을 구간 표기("00–01")로 바꾸는 대안은 채택하지 않는다. 가로축이 이미
  경계 눈금 규칙을 쓰고 있고, 세로 라벨의 `align-items: start` 도 그 규칙 위에 있다.
- `renderRows` 가 `.day-row__future` / `.day-row__now` 오버레이를 지우는 기존 결함은
  이번 범위 밖이다. 아래 Deferred Refactoring Note 참조.

## 활성 역할

| 역할 | 활성 | 이유 |
|---|---|---|
| Backend TDD Coach | 예 | A·B 가 백엔드 관찰 가능 동작을 바꾼다 |
| Backend & Integration Engineer | 예 | services.py, 테스트 수정 |
| Web Experience Designer | 예 | 프론트엔드 이중 리뷰 게이트 (C) |
| Browser Interaction Reviewer | 예 | 프론트엔드 이중 리뷰 게이트 (C) |
| Frontend Implementation Engineer | 예 | index.html 편집 |
| Quality Verification Lead | 예 | 회귀 범위와 완료 증거 |

미활성: Product Scope Owner(요구가 명확), Domain Architecture Reviewer(경계·의존 방향
불변), Security & Resilience Reviewer(신뢰 경계·권한 불변), Deployment & Operations
Reviewer(설정·마이그레이션 없음), AI Automation Architect(해당 없음).

## 도메인 경계와 의존 방향

변경은 `apps/dashboard` 안에서 끝난다. `services.py` 는 슬롯 표현 규칙을 소유하고
`views.py` 는 그것을 직렬화만 한다. 방향은 `views -> services` 그대로이고 새 의존은
없다. 결합도는 오히려 낮아진다 — `MIN_LABEL_SPAN` 이라는 표현 규칙 상수가 사라진다.

## Test List

| ID | 동작 | 경계 | 테스트 이름 | 상태 |
|---|---|---|---|---|
| DASH-LBL-3 | 3칸 미만 구간도 자기 블록에 태그 이름을 보인다 | unit | `test_label_appears_even_on_a_short_stretch` | Pending |
| DASH-LBL-4 | 라벨은 구간의 첫 슬롯을 담은 블록에 붙고 다음 행에는 붙지 않는다 | unit | `test_stretch_labels_the_block_containing_its_first_slot` | Pending |
| DASH-HRS-1 | 갱신 대상 시간은 앞뒤 한 시간씩 넓어진다 | unit | `test_refresh_hours_expand_by_one_hour_each_side` | Pending |
| DASH-HRS-2 | 확장은 하루 경계에서 잘린다 | unit | `test_refresh_hours_clamp_at_day_boundaries` | Pending |
| DASH-HRS-5 | 인접 시간대 저장이 라벨을 옮기고 옛 라벨을 지운 응답을 준다 | web | `test_save_moves_label_into_a_newly_touched_adjacent_hour` | Pending |

Given/When/Then 은 각 테스트 본문에 직접 드러낸다.

### 교체·수정되는 기존 테스트

AGENTS.md 정책에 따라, 지우기 전에 각 테스트가 지키던 동작을 위 Test List 로 옮겼다.

| 기존 테스트 | 지키던 옛 동작 | 처리 |
|---|---|---|
| `test_slot_rows.py:92` `test_label_appears_only_from_three_slots` | span<3 이면 라벨 없음 | DASH-LBL-3 으로 교체 |
| `test_slot_rows.py:109` `test_stretch_labels_first_row_that_is_wide_enough` | 라벨이 폭 충분한 첫 행으로 이동 | DASH-LBL-4 로 교체 |
| `test_undo.py:78` | 저장 응답이 건드린 시간만 반환 | 기대값 `[9]` → `[8,9,10]` 수정 |
| `test_undo.py:116` | undo 응답이 건드린 시간만 반환 | 기대값 `[9]` → `[8,9,10]` 수정 |

유지: `test_multi_hour_stretch_labels_only_the_first_row`,
`test_same_tag_in_separate_stretches_labels_each`, 그 외 병합·메모·헤더 테스트 전부.

## 구현 순서 (Red-Green, 한 번에 하나)

1. DASH-LBL-3 작성 → Red(`MIN_LABEL_SPAN` 게이트가 span 2 를 건너뛰어 `label == ""`)
   → `_assign_labels` 에서 게이트·상수 제거 → Green.
2. DASH-LBL-4 작성. 1번 Green 이후 기존 `:109` 테스트가 새 이유로 실패하므로 그것을
   교체하며 Red 확인 → 추가 구현 없이 Green.
3. DASH-HRS-1 작성 → Red(`hours_to_refresh` 미존재) → `hours_touched` 를
   `hours_to_refresh` 로 바꾸고 ±1 확장 → Green.
4. DASH-HRS-2 작성 → Red/Green.
5. `views.py:22,69,271` 호출부를 새 이름으로 갱신. `test_undo.py` 기대값 2건 수정.
6. DASH-HRS-5 작성 → Red → Green.
7. C(프론트엔드) 구현: `index.html` 에 경계 행 추가.

## 대상 파일

- `apps/dashboard/services.py`
- `apps/dashboard/views.py` (호출부 이름만)
- `apps/dashboard/test_slot_rows.py`
- `apps/dashboard/test_undo.py`
- `apps/dashboard/templates/dashboard/index.html`
- `docs/frontend/2026-08-14-grid-hour-axis-boundary.md` (작업 로그)
- `docs/project-status.md`

CSS 파일은 건드리지 않는다.

## Frontend Review Evidence

리뷰 깊이: **Standard**. 상호작용 추가는 없으나 그리드 DOM 구조와 라벨 렌더 조건이
바뀌고, 드래그·키보드 경로가 그리드 DOM 을 좌표로 탐색하기 때문이다.

### Web Experience Designer 사전 명세 (요약)

- 경계 행은 `#timeGrid` 마지막 자식. 컨테이너 밖에 두면 `mb-2` 급 여백이 필요해
  "닫는 경계"가 아니라 "두 번째 헤더"로 읽힌다.
- `.day-row__label` 무수정 재사용. 다른 굵기·색은 별개 정보로 오독된다.
- `24:00` 은 템플릿 리터럴. `HOURS_PER_DAY` 는 파라미터가 아닌 고정 상수라
  `build_time_headers` 식 파이썬 생성은 근거 없는 추상화다.
- 좁은 블록 라벨에 CSS 변경 불필요 — 색이 1차 채널, 텍스트는 보조 스캔 보조물.
- 수용 기준: 24:00 이 23:00 행 바로 아래 한 번만, 같은 라벨 열에, 3px 리듬으로.
  767.98px 이하에서 40px 열로 줄어들며 줄바꿈·잘림 없을 것. 최소 뷰포트에서
  1칸 블록이 **완전 공백이 아닐 것**(공백이면 회귀로 보고할 것).

### Browser Interaction Reviewer 사전 기준 (요약)

- `data-hour` 없는 후행 `.day-row` 는 모든 JS 셀렉터에 안전. 확인한 지점:
  `dashboard.js:52, 78, 307, 642, 810, 820, 828` 은 전부 `.day-row[data-hour]` 스코프,
  `:391`·`:488` 은 `#timeGrid` 위임. `.day-header`(index.html:100)가 이미 같은 형태로
  공존하는 선례.
- 하드 요구: aria-hidden 컨테이너 안에 포커스 가능한 자손이 0개일 것
  (`role`/`tabindex`/`.slot-block` 없음). 있으면 WCAG 4.1.2 위반.
- 좁은 블록에 라벨 span 이 생기면 접근 가능한 이름이 `title`(이름 · 메모) 대신
  텍스트 콘텐츠(이름)로 바뀐다. span≥3 블록의 기존 동작과 같으므로 회귀는 아니나
  구현 후 접근성 트리에서 확인할 것.
- 터치 타깃 최소치는 비대화형 행에 적용되지 않는다.

### 계획된 브라우저 증거

1. 데스크톱·767.98px 이하 스크린샷: 24:00 이 23:00 아래 같은 열에 정렬, 그리드와 연속.
2. 접근성 트리: 경계 행 하위에 포커스 가능 노드 0, 1칸 라벨 블록의 접근 가능한 이름이
   태그 이름으로 계산됨.
3. 키보드: 23시 행 마지막 블록에서 화살표 이동 시 경계 행으로 포커스가 가지 않음.
4. 드래그: 22~23시에서 시작해 그리드 아래로 끌었다 놓기 — 143 슬롯에서 깔끔히 멈추고
   예외·잔류 선택 없음.
5. 05:40~06:50 "수면" 저장 후 05:40 블록에 이름 표시, 06:00 행에는 미표시.
6. 6:00~6:50 저장 후 5:40~5:50 추가 저장 — 새로고침 없이 라벨이 1개만 보임(B 검증).
7. 긴 한글 태그명을 1칸 블록에 넣어 말줄임 확인, `title` 에 전체 이름 + 메모 유지.
8. 콘솔 오류 0.

사후 두 리뷰어 판정(`Conforms`/`Deviates`/`Unverified`)은 구현 후 이 문서에 기록한다.

## 검증 명령

```bash
conda run -n knou-life-diary pytest apps/dashboard/test_slot_rows.py --tb=short
conda run -n knou-life-diary pytest apps/dashboard/test_undo.py --tb=short
conda run -n knou-life-diary pytest apps/dashboard --tb=short
conda run -n knou-life-diary pytest
conda run -n knou-life-diary python manage.py check
```

JS 변경이 없으므로 `node --check` 는 해당 없음. 마이그레이션 없음.

## 수용 기준

1. 05:40~06:50 "수면" 저장 시 05:40 블록에 "수면"이 보이고 06:00 행에는 보이지 않는다.
2. 1~2칸 구간도 자기 블록에 이름을 보인다(폭이 좁으면 말줄임, `title` 에 전체 이름).
3. 한 구간에 라벨은 정확히 하나. 떨어진 같은 태그 구간은 각각 하나씩.
4. 6시 저장 후 5:40 추가 저장 시, 새로고침 없이도 라벨이 하나만 남는다.
5. 세로축이 00:00 로 시작해 24:00 으로 끝난다.
6. 경계 행은 키보드·드래그·선택·스크린리더에 잡히지 않는다.
7. 전체 pytest 회귀 green, `manage.py check` 클린.

## Deferred Refactoring Note

```text
Deferred Refactoring Note

- Topic: renderRows 가 다시 그리는 행의 .day-row__future / .day-row__now 오버레이를
  지운다.
- Why it is not part of the current scope: 이번 요구(라벨 위치·시간축)와 무관한
  기존 결함이고, 고치려면 변이 응답에 future/now 정보를 실어야 해 API 형태가 바뀐다.
- Why it may be needed later: B 로 갱신 행이 1개에서 최대 3개로 늘어 오늘 화면에서
  "아직 오지 않은 시간" 음영이 더 자주 사라진다. 새로고침하면 복구된다.
- Trigger condition: 사용자가 오늘 화면에서 미래 음영이 사라진다고 보고하거나,
  변이 응답에 future/now 를 싣는 다른 작업이 생길 때.
- Expected change location: apps/dashboard/views.py `_mutation_payload`,
  apps/dashboard/services.py `serialize_rows`, dashboard.js `renderRows`.
- Related tests: apps/dashboard/test_undo.py
```

## 커밋 계획

1. `fix(dashboard): 태그 라벨을 구간의 첫 블록에 붙인다` (A + 테스트)
2. `fix(dashboard): 라벨이 옮겨간 인접 시간도 갱신 대상에 넣는다` (B + 테스트)
3. `design(dashboard): 세로 시간축에 24:00 경계를 표기한다` (C)
4. `docs: 그리드 라벨·시간축 작업 로그와 상태 갱신`

브랜치 `feat/grid-label-and-hour-axis` 로 푸시하고 PR 을 연다. 머지는 사용자 몫이다.
