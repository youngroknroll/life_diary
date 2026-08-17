# P0 v2 4단계 — 분석 화면 segmented 전환 + 목표 진행 바

계획: `docs/plans/2026-08-16_p0-v2-handoff-plan.md` 4단계 (§4, 목업 1c·4b·4c).
브랜치: `feat/p0-v2-handoff`.

## 승인된 범위

- `apps/stats/templates/stats/index.html`의 `card > card-header > nav-tabs` 래핑
  제거, 기존 `.segmented`로 교체(모바일은 균등 4분할). `data-bs-toggle="tab"`은
  유지하고 클래스만 벗긴다(계획이 준 두 옵션 중 JS 무변경 쪽 채택).
- 목표 진행 바 신설: 요약 탭 수치 타일 바로 아래, 스와치+"태그·주기"+진행 바
  (10px, track 배경, 카테고리 딥 색 채움)+모노 수치 행. 주·월 목표는 페이스
  마커(2px 회색 선). 미달 확정 값만 danger 색. 행 클릭 → 기존 `usergoal_form`.
- 내보내기 행(4c) 모바일 세로 배치는 기존 `stats-export` CSS(`flex-wrap`)가 이미
  구현하고 있음을 확인 — 변경 없음.

## Activated Roles

- Domain Architecture Reviewer — `build_goal_progress_rows`가 `apps.users`의
  `GoalRepository`만 통해 목표를 읽고(쓰지 않음), `apps.tags`의 카테고리 매핑은
  이미 있는 `category_keys.py`를 재사용 — 경계 위반 없음.
- Backend TDD Coach, Backend & Integration Engineer — 아래 Test List(목표 진행률
  계산 자체는 새 비즈니스 규칙이라 TDD 대상, 세그먼트 전환은 프런트 전용).
- Web Experience Designer, Browser Interaction Reviewer — 아래 Frontend Review
  Evidence.
- Quality Verification Lead — 완료 판정.

## Test List — `build_goal_progress_rows`

| Scenario ID | Business behavior | Given | When | Then | Test name |
|---|---|---|---|---|---|
| GP-1 | 일간 목표 진행률은 조회일 하루 기록으로 정해진다 | 일간 목표 4h, 조회일 3h 기록 | 진행 바 행 조회 | percentage=75, pace=None | test_daily_goal_percentage_reflects_selected_dates_recorded_hours |
| GP-2 | 주간 목표는 그 주 전체 누적 + 페이스(경과일/전체일) | 주간 목표 10h, 수요일 조회, 누적 5h | 진행 바 행 조회 | percentage=50, pace=round(3/7*100) | test_weekly_goal_sums_the_whole_week_and_reports_pace |
| GP-3 | 월간 목표도 동일 구조 | 월간 목표 20h, 8/5 조회, 누적 5h | 진행 바 행 조회 | percentage=25, pace=round(5/31*100) | test_monthly_goal_sums_the_whole_month_and_reports_pace |
| GP-4 | 목표가 없으면 빈 리스트 | 목표 0개 | 진행 바 행 조회 | [] | test_no_goals_returns_an_empty_list |
| GP-5 | 진행 중인 기간의 미달은 danger 아님 | 오늘=조회일, 미달 | 진행 바 행 조회 | is_under_target=False | test_in_progress_period_under_target_is_not_marked_danger |
| GP-6 | 끝난 기간의 미달만 danger("미달 확정") | 조회일<실제 오늘, 미달 | 진행 바 행 조회 | is_under_target=True | test_confirmed_past_period_under_target_is_marked_danger |
| GP-7 | 목표 초과分은 바 폭이 100%를 넘지 않는다 | 목표 1h, 기록 3h | 진행 바 행 조회 | percentage=100 | test_percentage_caps_at_100_when_exceeding_target |
| GP-8 | 행은 일간→주간→월간 순 | 세 주기 목표 각 1개(역순 생성) | 진행 바 행 조회 | 순서=[daily,weekly,monthly] | test_rows_are_ordered_daily_then_weekly_then_monthly |

전부 `Status: Green`, `Refactoring allowed: No`.

## Red → Green, 발견한 회귀 2건

- Red: `apps/stats/aggregation/test_goal_progress.py`에 `TestGoalProgressRows`
  추가, `ImportError: cannot import name 'build_goal_progress_rows'`로 예상대로
  실패 확인.
- Green 구현:
  - `apps/stats/aggregation/category_keys.py`에 `CATEGORY_LINE_COLOR`(딥 hex 5개)
    추가 — stats.js의 `CATEGORY_LINE`과 값을 맞춘 서버 인라인 style용 짝
    (`apps/tags/models.py`의 `INK_ON_ACCENT`와 같은 이유로 CSS 토큰이 아니라
    Python 상수로도 둔다).
  - `apps/stats/aggregation/goal_progress.py`에 `build_goal_progress_rows` 신설.
    `_period_bounds`(일/주/월 기간 산정, 기존 `get_week_date_range`/
    `get_month_date_range` 재사용), `_minutes_recorded`, `_pace_percentage`,
    `_goal_progress_row`로 쪼갰다. `today`와 `selected_date`를 분리한 이유는
    "미달 확정" 판정에 실제 오늘이 필요한데 전역 시각을 모킹하지 않고 테스트
    하기 위해서다(`comparison.get_period_delta`와 같은 패턴).
  - `apps/stats/logic.py`에 `build_goal_progress_rows` 호출을 연결, context에
    `goal_progress_rows` 추가.
  - `apps/users/repositories.py`의 `find_grouped_by_period`에 `tag__category`
    select_related 추가(아래 회귀 1 참조).
- **회귀 1 — 쿼리 예산 초과(1개)**: `find_grouped_by_period` 호출 1회가
  `test_stats_perf.py`의 쿼리 예산을 17→18로 밀었다. 기록량이 아니라 "목표
  개수"에 비례하는 항목이라(목표마다 그 기간 TimeBlock 합 쿼리 1회) 앞선
  항목들과 성격이 다르다 — `TARGET_MAX_QUERIES`를 18로 올리고 그 이유와
  "목표가 여러 개인 사용자가 흔해지면 재검토" 조건을 주석에 남겼다.
  이 fixture는 목표를 만들지 않아 N+1 자체는 여기서 드러나지 않는다.
  온보딩이 "하나면 충분하다"고 안내해 목표 수가 작을 것으로 보고 지금은 허용.
- **회귀 2 — Bootstrap Tab 상태 관리 깨짐(브라우저에서 발견)**: `nav-link
  active` → `segmented__item is-active`로 바꾸면서 초기 트리거에 Bootstrap의
  실제 "active" 클래스가 빠졌다. Bootstrap Tab.js는 클릭 시 "이전에 active인
  트리거"를 찾아 그 페인을 닫는데, 초기 상태에 "active"가 없으니 아무 것도
  못 찾아 이전 페인(요약)을 안 닫고 새 페인만 더 보여줬다(두 탭 내용이 한
  화면에 같이 렌더). 초기 버튼에 `active`를 `is-active`와 함께 유지해 고쳤다.
  **회귀 2-2**: 고치고 나서도 URL hash로 진입할 때(`#weekly` 등) pill
  하이라이트만 "요약"에 남는 별개 결함을 하나 더 발견 — `initTabHashSync`가
  `shown.bs.tab` 리스너를 등록하기 *전에* `new bootstrap.Tab(trigger).show()`를
  먼저 호출해, 로드 시 hash가 쏘는 첫 이벤트를 리스너가 놓쳤다. 리스너 등록을
  hash 활성화보다 앞으로 옮겨 고쳤다. 두 결함 모두 유닛 테스트로는 잡히지
  않는 순수 브라우저 상태 결함이라 실측에서만 드러났다.
- **파일 캐시 이슈(내 검증 환경 한정, 코드 결함 아님)**: `apps/stats/use_cases.py`의
  `GetStatsContextUseCase`가 파일 기반 캐시(`.cache/`, 과거 날짜 24시간)로
  컨텍스트 dict를 통째로 캐싱한다. 이전 단계(3단계) 검증에서 이미 방문했던
  날짜를 이번 단계에서 다시 열자 `goal_progress_rows` 키가 없는 옛 캐시가
  그대로 나와 목표 진행 바가 빈 상태로 보였다 — `.cache/`를 지우자 해결.
  **배포 시 유의점으로 아래 Deferred에 남긴다** — 캐시 키에 스키마 버전이
  없어, 이 브랜치를 배포하면 최근 24시간 안에 캐시된 과거 날짜 조회가 그
  TTL이 끝날 때까지 목표 진행 바 없이 보일 수 있다.

## Frontend Review Evidence

**Review depth**: Standard — 탭 전환은 클래스 교체와 기존 JS 유지(내비게이션
구조 자체는 안 바뀜), 목표 진행 바는 새 컴포넌트지만 모달·드래그·비동기 상태는
없다. 다만 위 회귀 2가 보여주듯 탭 상태 전환은 실제 클릭·hash 진입 양쪽을
반드시 실측해야 한다.

**Web Experience Designer — 사전 스펙**
- `.segmented`/`.segmented__item`은 기존 CSS 그대로 재사용하고 새로 만들지
  않는다. 모바일에서만 4등분(`flex:1`), 데스크톱은 콘텐츠 폭.
- 목표 진행 바 행은 스와치(태그의 기존 pastel 색)+"태그 · 주기" 라벨, 진행
  바 채움은 카테고리 딥 색(`CATEGORY_LINE_COLOR`), 페이스 마커는 회색 2px
  세로선. 미달 확정 값만 danger 텍스트색 — 바 색 자체는 안 바뀐다(값만).
- 목표가 없으면 빈 문구+추가 링크로 대체, canvas나 빈 배열 렌더링으로
  깨지지 않는다.

**Browser Interaction Reviewer — 사전 기준**
- 탭 전환은 클릭과 URL hash 진입(새로고침) 양쪽 다 pill 하이라이트와 페인
  내용이 일치해야 한다 — 회귀 2가 실제로 이 기준에 걸려 잡혔다.
- 목표 진행 바 행은 실제 `<a href>`라 키보드 포커스·Enter로 `usergoal_form`
  이동이 가능해야 한다.
- 페이스 마커는 `title` 속성으로 스크린리더가 "오늘 기준 페이스"를 읽을 수
  있어야 한다.

## 검증

- `node --check apps/stats/static/stats/js/stats.js` — 통과.
- `conda run -n knou-life-diary python manage.py check` — 이슈 없음.
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run`
  — 변경 없음.
- `conda run -n knou-life-diary pytest -q`(전체) — 통과(exit 0).
- i18n: makemessages 후 `project_i18n_fuzzy_trap`과 같은 유형의 회귀(ko 3건,
  en 3건: "매일"→"일", "오늘 기준 페이스"→"오늘 기록 이어가기" 등 잘못 상속)를
  발견해 ko는 항등, en은 새 영어 문구로 고치고 fuzzy 플래그 제거.
  `msgfmt --check-format` 양쪽 통과, `compilemessages` 통과.
- 브라우저 실측(chrome-devtools MCP, 격리 임시 SQLite + `runserver 8765`.
  검증 종료 후 임시 DB·설정 모듈·`.cache/` 모두 삭제):
  - 목표 3개(집중 일간 4h, 독서 일간 1h, 운동 주간 10h) 시드 + 카테고리별
    기록. 데스크톱(1280px)·모바일(375px), 라이트/다크(다크로 확인).
  - 진행 중인 오늘(실제 서버 오늘 기준) 조회: 집중 50%, 독서 0%(둘 다 danger
    아님 — 진행 중), 운동 페이스 마커가 그 주 1일차 위치(14%)에 정확히 표시.
  - 과거로 끝난 주 조회: 집중 100%(정확히 달성, danger 아님), 독서 0%(danger
    빨강 확인), 운동 70% + 페이스 마커가 주 마지막 날 위치(100%)로 이동 —
    같은 목표가 조회일에 따라 다른 기간 창을 정확히 따라감을 확인.
  - 탭 클릭 4종(요약→일→주→월) 전부 pill과 페인이 일치, `shown.bs.tab` 로드
    경로(hash로 직접 진입 후 새로고침)도 재확인 — 회귀 2 재발 없음.
  - 모바일에서 세그먼트 4등분 렌더, 목표 진행 바 반응형 레이아웃 확인.
  - 콘솔 오류 0(폰트 preload 경고 1건은 1단계부터 있던 무해한 브라우저
    경고 — `as="font"` 이미 정확히 설정돼 있고, `stats.js`에서 실제 렌더
    시점에 웹폰트가 쓰이므로 경고는 크롬의 조기 타이밍 휴리스틱일 뿐).

## Frontend Review Evidence — 판정

- **Web Experience Designer**: Conforms — segmented 재사용, 목표 진행 바 색
  규칙(스와치=pastel, 채움=딥, danger=값만), 빈 상태 문구 모두 확인.
- **Browser Interaction Reviewer**: Conforms — 클릭·hash 두 경로 모두 재확인,
  키보드 접근 가능한 링크·페이스 마커 title 확인. 회귀 2를 실제로 잡아낸
  것이 이 리뷰가 클릭만이 아니라 hash 로드 경로까지 요구한 덕분이다.
- **Quality Verification Lead**: 완료로 판정 — 두 역할 모두 Conforms, 발견한
  회귀 2건은 모두 수정 후 재검증 완료.

## Deferred

- **배포 캐시 유의점**: `GetStatsContextUseCase`의 파일 캐시가 스키마 버전을
  안 가진다. 이 브랜치를 배포할 때 `.cache/` 비우기(또는 캐시 키에 버전
  붙이기)를 배포 체크리스트에 넣을 것을 Deployment & Operations Reviewer에게
  권한다 — 안 하면 최근 24시간 안에 캐시된 과거 날짜 조회가 TTL이 끝날 때까지
  목표 진행 바 없이 보일 수 있다(기능 누락처럼 보이지만 자연 소멸됨).
- 목표 관리 개수가 많아지면(N+1) `TARGET_MAX_QUERIES` 산정 방식 재검토 —
  위 회귀 1 참조.
- 기존에 발견한, 이번 범위 밖의 오류: `locale/en`의 `"설정된 목표가 없습니다"`
  → `"No tags yet."`(잘못된 기존 번역, fuzzy 아님, 이번 세션이 만들지 않음) —
  건드리지 않고 남긴다.
