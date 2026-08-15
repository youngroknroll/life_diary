# 그리드 태그 라벨 위치와 시간축 24:00 경계 — 작업 로그

작업일: 2026-08-14
계획: `docs/plans/2026-08-14_grid-label-and-hour-axis-plan.md`
브랜치: `feat/grid-label-and-hour-axis` (base `main`)

## 무엇을 고쳤나

### A. 태그 이름이 구간의 첫 블록에 붙는다

`_assign_labels` 는 라벨을 "폭 3칸 이상인 첫 행 조각"에 붙였다. 05:40~06:50 "수면"은
5시 행 조각이 2칸이라 건너뛰고 6시 행이 이름을 가져갔다.

`MIN_LABEL_SPAN` 상수와 그 게이트를 제거했다. 구간 중복 방지(`_stretch_start` +
`labelled_stretches`)는 그대로여서 구간당 라벨은 여전히 하나다.

원래 게이트의 근거였던 "좁은 첫 행이 라벨을 가져가면 이름이 사라진다"는 이제
성립하지 않는다. `.slot-block__label` 이 nowrap + ellipsis 이고 전체 이름은 블록
`title` 에 남아, 좁은 블록에서는 사라지는 대신 잘려 보인다.

### B. 라벨이 옮겨간 인접 시간도 갱신 대상에 넣는다

A 만으로는 흔한 흐름에서 라벨이 두 개 보였다. 6:00~6:50 저장(6시에 라벨) 뒤
5:40~5:50 을 같은 태그로 저장하면 구간 시작이 5시로 옮겨가는데, 응답은 건드린
시간(5시)만 실어 보내 6시 행의 옛 라벨이 화면에 남았다.

`hours_touched` 를 `hours_to_refresh` 로 바꾸고 앞뒤 한 시간씩 넓혔다(0~23 clamp).
구간 시작은 변이 경계에서 한 시간을 넘어 움직일 수 없으므로 ±1 로 충분하다.

### C. 세로 시간축이 24:00 으로 끝난다

`#timeGrid` 마지막 자식으로 경계 행 하나를 넣었다. `data-hour` 가 없어 JS 의 행
조회(`.day-row[data-hour]`)에 잡히지 않고, 그리드 안에 있어 행 간 `gap: 3px` 리듬을
그대로 쓴다. `.day-row__label` 재사용이라 CSS 변경은 없다.

가로 분축은 이미 6칸에 눈금 7개(`:00`…`:60`)로 같은 규칙을 쓰고 있었다. 세로축만
끝선이 없었다.

## 바뀐 파일

| 파일 | 내용 |
|---|---|
| `apps/dashboard/services.py` | `MIN_LABEL_SPAN` 제거, `hours_touched` → `hours_to_refresh` (±1 확장) |
| `apps/dashboard/views.py` | 호출부 2곳 이름 변경 |
| `apps/dashboard/templates/dashboard/index.html` | 24:00 경계 행 추가 |
| `apps/dashboard/test_slot_rows.py` | 라벨 테스트 2건 교체 |
| `apps/dashboard/test_refresh_hours.py` | 신규 — 갱신 시간 확장·clamp |
| `apps/dashboard/test_undo.py` | 응답 시간대 기대값 수정 3건, 인접 시간 라벨 이동 테스트 추가 |

CSS 와 `dashboard.js` 는 건드리지 않았다.

## 교체한 기존 테스트

지우기 전에 각 테스트가 지키던 동작을 계획서 Test List 로 옮겼다.

| 기존 | 지키던 옛 동작 | 처리 |
|---|---|---|
| `test_label_appears_only_from_three_slots` | span<3 이면 라벨 없음 | `test_label_appears_even_on_a_short_stretch` 로 교체 |
| `test_stretch_labels_first_row_that_is_wide_enough` | 라벨이 폭 충분한 첫 행으로 이동 | `test_stretch_labels_the_block_containing_its_first_slot` 로 교체 |
| `test_save_returns_only_the_rows_it_touched` | 응답이 건드린 시간만 반환 | 이름·기대값 수정 (`[8,9,10]`) |
| `test_undo_returns_refreshed_rows_and_stats` | 같음 | 기대값 수정 |
| `test_returned_runs_serialize_the_tag` | `runs[0]` 을 위치로 참조 | 시간(9시)으로 행을 찾도록 수정 |

## 검증 증거

### 백엔드

| 명령 | 결과 |
|---|---|
| `pytest apps/dashboard/test_slot_rows.py` | 12 passed |
| `pytest apps/dashboard/test_refresh_hours.py` | 3 passed |
| `pytest apps/dashboard/test_undo.py` | 15 passed |
| `pytest apps/dashboard` | 96 passed |
| `pytest` (전체) | **501 passed** (286.55s) |
| `manage.py check` | System check identified no issues |
| `makemigrations --check --dry-run` | No changes detected |

Red 확인:
- DASH-LBL-3: `AssertionError: assert '' == '집중 작업'` — span 게이트가 2칸을 건너뜀.
- DASH-LBL-4: 게이트 제거 후 기존 `:109` 테스트가 새 이유로 실패
  (`assert '집중 작업' == ''`, 13시 행이 라벨을 가져감) → 교체.
- DASH-HRS-1: `ImportError: cannot import name 'hours_to_refresh'`.
- DASH-HRS-2: `assert [-1, 0, 1] == [0, 1]`, `assert [22, 23, 24] == [22, 23]` — clamp 없음.

Red-Green 역검증(DASH-HRS-5): 확장을 `(-1,0,1)` → `(0,)` 로 되돌리자
`KeyError: 6` 으로 실패(응답에 6시가 아예 없음) → 복원 후 통과. 테스트가 실제로 그
회귀를 잡는다.

### 브라우저

격리된 임시 SQLite + `runserver 8765` 로 확인했다. dev DB(`db.sqlite3`)는 열지도
않았고 mtime 도 그대로다. 확인 후 임시 DB·시드 스크립트는 삭제했다.

| 항목 | 결과 |
|---|---|
| 24:00 경계 | 1개, `#timeGrid` 마지막 자식, `aria-hidden="true"`, 포커스 가능 자손 0 |
| `.day-row[data-hour]` 수 | 24 (변동 없음) |
| 라벨 열 정렬 | 23:00 라벨과 오른쪽 끝 정수 일치, 행 아래 간격 3px |
| 375px | 라벨 열 40px, 24:00 줄바꿈 없음, 정렬·간격 유지 |
| 05:40(2칸) | 라벨 "수면", 잘림 없음 / 06:00(6칸) 라벨 없음 |
| 13:40(2칸) | 라벨 "집중 작업" / 14:00 라벨 없음 |
| 10:00(1칸, 긴 이름) | 라벨 표시 + 말줄임, `title` 에 전체 이름 |
| 375px 1칸 블록 | 콘텐츠 폭 48px > 한 글자+말줄임 19px — 공백 아님 |
| 키보드 | 23시 마지막 칸에서 ArrowDown → 포커스 유지, 경계 행 진입 없음 |
| 포인터 히트테스트 | 경계 행 위에서 `.closest('.day-row[data-hour]')` === null (23시 행은 정상 해석) |
| B 실동작 | 36~41 저장 상태에서 슬롯 35 저장 → **새로고침 없이** 35에 "수면", 36은 빈 라벨 |
| 콘솔 | 오류·경고 0 |

## 미검증

- 스크린리더(VoiceOver/NVDA) 실제 통과. `aria-hidden` 무시는 구조로만 확인했다.
- span 1 블록의 접근 가능한 이름을 접근성 트리에서 직접 읽지 않았다.
  `role="button"` + 비어 있지 않은 텍스트 콘텐츠로 구조 확인만 했다.
- 그리드 아래로 끌어 놓는 실제 드래그 제스처. 드래그 핸들러가 쓰는
  `elementFromPoint` + `.closest('.day-row[data-hour]')` 경로로 대체 확인했다.

## Deferred

`renderRows` 가 다시 그리는 행의 `.day-row__future` / `.day-row__now` 오버레이를
지우는 기존 결함이 남아 있다. B 로 갱신 행이 최대 3개로 늘어 오늘 화면에서 미래
음영이 더 자주 사라진다(새로고침하면 복구). 상세는 계획서의 Deferred Refactoring
Note 참조.
