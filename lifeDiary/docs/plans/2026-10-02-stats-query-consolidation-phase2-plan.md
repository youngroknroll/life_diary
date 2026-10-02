# 통계 쿼리 통합 2단계 계획: 요청당 기록 1회 조회 (2026-10-02)

- 1단계 계획과 방향 기록: `docs/plans/2026-09-30-stats-query-consolidation-plan.md` "2단계 방향"
- 1단계 실행·운영 측정: `docs/refactoring/2026-09-30-stats-query-consolidation.md`
- 백로그: B-6
- 브랜치: `perf/stats-query-consolidation-phase2`

## 배경

1단계를 배포한 뒤 2026-10-01에 운영에서 쟀다. 캐시 미스 TTFB 중앙값은 2,291ms, 쿼리는 20개, 쿼리당 84.5ms였다. 쿼리 20개 가운데 15개가 같은 사용자의 기록(`dashboard_timeblock`)을 기간만 바꿔 다시 읽는다. 선택일을 D라고 하면 다음과 같다.

| 읽는 곳 | 기간 |
|---|---|
| `daily.py:15` `find_by_date` | D |
| `weekly.py:23` | D의 주 |
| `calculator.py:36` 월간 블록 | D의 달 |
| `calculator.py:44` 날짜별 개수 | D의 달 |
| `comparison.py:92` `_summarize` ×4 | D, D-1, D의 달, 전달 |
| `comparison.py:130` `_baseline` | D의 주 시작 전 12주 |
| `comparison.py:149` `_sparkline` | D-6~D |
| `density.py:22` | D-6~D |
| `summary.py:105` `_rolling_week` | D-6~D |
| `daily_baseline.py:27` | D-6~D |
| `goal_progress.py:30` `goal_hit_dates`(요약 목표 타일, 목표가 있을 때) | D-6~D |
| `goal_progress.py` 1단계 합집합(목표가 있을 때) | D의 주 ∪ D의 달 |

나머지 쿼리는 카테고리 2번(`weekly.py:38`, `monthly.py:21`), 목표 2번, 메모 1번이다.

사용자가 2026-10-02에 2단계 진행을 결정했다. 서버·DB 리전 일치(A-10)는 보류한 상태다.

## 범위

포함:

- 위 기록 조회 15번을 요청당 1번으로 줄인다. `get_stats_context`가 필요한 기간 전체를 덮는 창(window)을 계산하고, `StatsCalculator`가 그 창을 한 번 읽는다. 각 집계는 자기 기간만 그 목록에서 꺼낸다.
- 카테고리 목록을 요청당 1번만 읽는다.
- 창을 받지 않은 호출(기존 테스트, 목표 페이지 등)은 지금처럼 직접 조회한다.

제외:

- 목표 조회 2번 합치기(`summary._goal_tile`의 첫 목표 조회와 목표 진행의 목표 목록 조회). 별도 후보로 둔다.
- 캐시 hit 경로의 요청당 쿼리 3개(세션, 사용자, 내보내기 달 목록).
- 리전 이전(A-10), DB 연결 재수립(A-9), 저장 API(B-10).
- 통계 결과의 모양이나 값 변경, 스키마 변경, 새 의존성.

## 인수 기준

1. 통계 결과는 지금과 같다. 창을 받은 집계와 창 없이 직접 조회한 집계의 결과가 같다(WQ-05). 이를 다음 경우에서 확인한다.
   - 과거 달 중간 날짜
   - 주가 달 경계를 넘는 날짜
   - 오늘(`today` 주입)
   - 목표 기간 3종, 미분류 블록, 전달 기록, 12주 기준선 기록, 같은 날짜의 다른 사용자 기록
2. `get_stats_context`의 쿼리 수는 목표가 없어도 있어도 5개 이하다. `TARGET_MAX_QUERIES`는 18에서 5로 낮춘다.
3. 다른 사용자의 기록은 결과에 섞이지 않는다. 인수 기준 1의 fixture에 같은 날짜의 다른 사용자 기록을 넣는다.
4. 창과 읽은 기록은 `get_stats_context`가 요청마다 새로 만든 `StatsCalculator`의 값이다. 모듈 수준이나 싱글턴에 저장하지 않는다. 원본 기록을 Django 캐시에 넣지 않는다(Security & Resilience Reviewer 조건).
5. 창 조회는 기존 `TimeBlockRepository.find_by_date_range`를 쓴다(`select_related`와 `.only()` 유지).
6. 캐시 키 `:v2`는 인수 기준 1로 결과가 같음을 보였을 때만 유지한다. 보이지 못하면 `:v3`으로 올린다(Deployment & Operations Reviewer 조건).
7. 배포 후 운영 `db-count`가 20에서 5로 준다. 한 번도 열지 않은 과거 날짜 5개 이상에서 miss를 재 1단계 결과(TTFB 중앙값 2,291ms)와 비교한다.

## Activated Roles

- Backend TDD Coach: Test List 확정과 Red/Green 판정.
- Backend & Integration Engineer: 구현, 증거 기록, 문서 갱신.
- Quality Verification Lead: 회귀 위험과 최종 증거 평가.
- Domain Architecture Reviewer: 창의 소유와 집계 함수 시그니처 결정. 2026-09-30 방향 검토를 마쳤고, 이 계획의 구체 설계를 다시 검토한다.
- Security & Resilience Reviewer: 소유권과 요청 지역 값 조건(2026-09-30 제시, 인수 기준 3·4).
- Deployment & Operations Reviewer: 단계별 배포, 측정, 캐시 키 조건(2026-09-30 제시, 인수 기준 6·7).

## Not Activated

- Product Scope Owner: 사용자가 진행을 결정했다.
- Web Experience Designer, Browser Interaction Reviewer, Frontend Implementation Engineer: 템플릿, CSS, 브라우저 JS를 바꾸지 않는다.
- AI Automation Architect: 해당 없음.

## Domain Boundary and Dependency Direction

- 기간 계산은 지금처럼 각 집계 모듈이 소유한다(`comparison._period_bounds`, `ROLLING_DAYS`, `DAYS_PER_PERIOD` 등).
- 창의 범위는 오케스트레이터인 `logic.get_stats_context`가 계산한다. `StatsCalculator`는 받은 창을 담아 구간을 잘라 줄 뿐이고, 소비자의 상수를 import하지 않는다(Domain Architecture Reviewer: 계산기가 모든 소비자를 아는 객체가 되는 것을 막는다).
- 기록 조회는 기존 `TimeBlockRepository.find_by_date_range`만 쓴다. 새 저장소 메서드는 만들지 않는다.
- 의존 방향은 `stats.logic -> stats.aggregation -> dashboard.repositories / tags.repositories / users.repositories` 그대로다.

## Coupling and Cohesion Review

1. 결합도가 조금 는다. 다섯 개 집계 함수(`get_period_delta`, `build_summary`, `get_density_grid`, `get_tag_deltas_vs_week`, `build_goal_progress_rows`)와 `goal_hit_dates`가 `calculator=None` 선택 인자로 `StatsCalculator`를 알게 된다.
   - 선택 인자이므로 기존 호출과 테스트는 바뀌지 않는다.
   - "인자 있음/없음" 두 경로가 계속 남는 것은 Deferred로 관리한다. 트리거는 모든 운영 호출이 계산기를 넘기게 된 시점이다.
2. 응집도는 유지된다. 각 집계의 계산 로직은 그대로이고, "어디서 기록을 가져오느냐"만 바뀐다.
3. 범용 캐시나 전략 객체로 일반화하지 않는다. 이번 요청에 필요한 창 하나만 담는다.

## Pythonic Code Design

- `StatsCalculator(user, selected_date, window=None)`:
  - `window`는 `(start, end)` 튜플이다.
  - `blocks_between(start, end)`가 창 안이면 처음 한 번만 `find_by_date_range(user, window_start, window_end)`를 읽고, 날짜별로 묶어 두었다가 해당 날짜들의 블록을 돌려준다.
  - `TimeBlock.Meta.ordering = ["date", "slot_index"]`이므로, 날짜 순서대로 이어 붙이면 직접 조회와 순서가 같다. 집계 중에는 같은 시간의 태그가 먼저 나온 순서를 따르는 곳이 있어 순서가 중요하다.
  - 창이 없거나 창 밖이면 직접 조회한다. 정합성을 지키는 안전망이다.
- `get_monthly_blocks`와 `get_monthly_daily_counts`:
  - 지금처럼 한 번만 계산하도록 메모한다. 기존 테스트 두 개가 이를 확인한다.
  - 창이 있으면 월간 블록을 창에서 꺼낸다. 날짜별 개수는 그 목록에서 센다(`collections.Counter`).
- `categories()`: 카테고리 목록을 한 번 읽어 메모한다. 주간과 월간 집계가 쓴다.
- 모듈 함수 `read_blocks(user, start, end, calculator=None)`를 `calculator.py`에 둔다. 계산기가 있으면 `blocks_between`을, 없으면 저장소를 부른다. 다섯 모듈에 같은 세 줄이 반복되지 않게 하기 위해서다.
- `logic.get_stats_context`가 창을 계산한다.
  - 시작은 `min(D의 주 시작 − 12주, 전달 1일, D − 6일)`이다.
  - 끝은 `max(D의 주 끝, D의 달 끝)`이다.
  - `BASELINE_MAX_WEEKS`는 `comparison`에서 가져온다.
- 읽은 목록은 읽기만 한다. 블록 객체를 바꾸지 않는다.

메모리: 창은 최대 약 17주다. 매일 144칸을 다 채운 사용자라면 약 1만 7천 행이다. 지금도 기준선 조회 하나가 12주(최대 약 1만 2천 행)를 한 번에 읽고, 다른 조회들이 같은 기록을 다시 읽는다. 그래서 요청 하나가 읽는 행의 총합은 줄어든다고 본다(추정, 재지 않음).

## Test List and TDD checkpoints

새 테스트는 `apps/stats/aggregation/test_stats_window.py`에 둔다. 공통 fixture는 아래를 담는다(인수 기준 1·3).

- 사용자 둘(같은 날짜에 기록)
- 카테고리 2개에 걸친 태그 여러 개
- 미분류 블록(태그 없음)
- 일간·주간·월간 목표
- 기록이 있는 기간:
  - 선택일의 달과 전달
  - 달 경계를 넘는 주
  - 선택일 주 시작 전 12주

"오늘" 경우는 `today`를 주입해 만든다. 시간 고정 라이브러리는 없고, 새로 추가하지 않는다.

진행 순서는 다음과 같다.

1. WQ-01~WQ-04로 계산기를 만든다.
2. 이어 집계마다 다음을 반복한다.
   - WQ-05에 그 집계의 경우를 더한다. 인자가 없으면 TypeError로 Red다. 인자를 받아 저장소 경로를 그대로 쓰게 해 Green을 만든다.
   - 그 집계의 "추가 조회 없음" 계약 테스트를 쓴다. Red를 확인한 뒤 창을 쓰게 해 Green을 만든다.
3. 마지막으로 WQ-14로 전체 예산을 낮춘다.

| ID | 동작 | Given | When | Then | 경계 | 테스트 | 예상 Red | 상태 |
|---|---|---|---|---|---|---|---|---|
| WQ-01 | 창으로 꺼낸 구간은 직접 조회와 같은 기록을 같은 순서로 준다 | 공통 fixture, 창 = 선택일 기준 전체 범위 | `blocks_between`으로 여러 하위 구간(하루, 주, 달 경계 주, 전달, 12주 전 끝) 조회 | 각 구간의 (날짜, 칸, 태그 id) 목록이 `find_by_date_range`와 같다 | domain | `test_window_returns_the_same_blocks_in_the_same_order_as_direct_reads` | `TypeError`(window 인자 없음) | Green |
| WQ-02 | 창 안의 구간을 여러 번 꺼내도 기록 조회는 한 번이다 | 같음 | 하위 구간 여러 개 조회 | 쿼리 1개 | contract | `test_window_reads_blocks_once_for_any_number_of_ranges` | WQ-01 최소 구현이 매번 조회하면 쿼리 여러 개 | Green |
| WQ-03 | 창 밖 구간도 빠짐없이 돌려준다 | 같음, 창보다 이른 날짜 기록 | 창 밖 구간 조회 | 직접 조회와 같다 | domain | `test_ranges_outside_the_window_still_return_every_block` | WQ-02 구현이 창 안에서만 찾으면 빈 목록 | Green |
| WQ-04 | 카테고리 목록은 요청당 한 번만 읽는다 | 계산기 | `categories()` 두 번 | 쿼리 1개, 같은 목록 | contract | `test_categories_are_read_once_per_calculator` | `AttributeError` | Green |
| WQ-05 | 창으로 만든 통계는 직접 조회로 만든 통계와 같다 | 공통 fixture | 집계를 창 있는 계산기로 한 번, 창 없이 한 번 | 결과가 같다 | domain(parametrize: 집계 × {과거, 달 경계 주, 오늘}) | `test_stats_from_one_read_match_direct_reads[<집계>-<경우>]` | 인자 없는 집계는 `TypeError`, 이미 계산기를 받는 일간·주간·월간은 처음부터 Green(안전망, 돌연변이 검사) | Green |
| WQ-06 | 창이 있으면 일간 통계는 기록을 다시 읽지 않는다 | 창을 미리 읽은 계산기 | `get_daily_stats_data` | `dashboard_timeblock` 조회 0 | contract | `test_daily_stats_reuse_the_window` | `find_by_date` 1회 | Green |
| WQ-07 | 주간 통계는 기록과 카테고리를 다시 읽지 않는다 | 창과 카테고리를 미리 읽은 계산기 | `get_weekly_stats_data` | 쿼리 0 | contract | `test_weekly_stats_reuse_the_window` | 기록 1, 카테고리 1 | Green |
| WQ-08 | 월간 통계와 태그 분석은 기록·날짜별 개수·카테고리를 다시 읽지 않는다 | 같음 | `get_monthly_stats_data`, `get_tag_analysis_data` | 쿼리 0 | contract | `test_monthly_stats_reuse_the_window` | 기록 1, 개수 1, 카테고리 1 | Green |
| WQ-08b | 날짜별 기록 개수는 미분류 칸까지 DB 집계와 같게 센다(구현 중 발견) | 공통 fixture(미분류 칸 포함) | `get_monthly_daily_counts` | `find_daily_counts`와 같다 | domain | `test_monthly_daily_counts_include_untagged_blocks_like_the_database_count` | 처음부터 Green(안전망). 돌연변이 검사: 태그 있는 칸만 세면 실패. WQ-05는 창 유무와 관계없이 같은 계산을 쓰므로 이 결함을 잡지 못했다 | Green |
| WQ-09 | 기간 비교는 기록을 다시 읽지 않는다 | 창을 미리 읽은 계산기 | `get_period_delta` 일(추세 포함)·월 | `dashboard_timeblock` 조회 0 | contract | `test_period_comparison_reuses_the_window` | 일 4회, 월 2회 | Green |
| WQ-10 | 밀도 격자는 기록을 다시 읽지 않는다 | 같음 | `get_density_grid` | 0 | contract | `test_density_grid_reuses_the_window` | 1회 | Green |
| WQ-11 | 태그별 7일 평균 대비는 기록을 다시 읽지 않는다 | 같음 | `get_tag_deltas_vs_week` | 0 | contract | `test_tag_deltas_reuse_the_window` | 1회 | Green |
| WQ-12 | 요약은 기록을 다시 읽지 않는다 | 같음, 목표 있음 | `build_summary` | `dashboard_timeblock` 조회 0(목표 조회 1은 남음) | contract | `test_summary_reuses_the_window` | 기간 비교·밀도·최근 7일·목표 달성일 | Green |
| WQ-13 | 목표 진행은 기록을 다시 읽지 않는다 | 같음, 목표 있음 | `build_goal_progress_rows` | `dashboard_timeblock` 조회 0 | contract | `test_goal_progress_reuses_the_window` | 1회 | Green |
| WQ-14 | 통계 화면 데이터는 쿼리 5개 이하로 만든다 | 목표 없는 기존 fixture / 목표 있는 사용자, 선택일 3가지(달 중간 2026-04-15, 주가 전달에 걸치는 2026-08-02, 주가 다음 달에 걸치는 2026-06-30) | `get_stats_context` | 각각 5개 이하 | contract | 기존 `test_get_stats_context_query_count_within_target`(상한 18→5) + `test_stats_context_query_count_stays_within_target_with_goals[mid_month, week_into_last_month, week_into_next_month]` | 18개, 20개 | Green |

검토 반영 (2026-10-02):

- Backend TDD Coach는 창 범위 공식이 틀려도 WQ-14가 못 잡는다고 보았다. 이 설계에서는 창 밖 구간을 요청하면 저장소를 직접 조회하므로, 범위가 빠지면 쿼리가 하나 늘어 상한 5에 걸린다. 다만 테스트한 날짜에서만 드러난다는 지적은 맞다. 그래서 WQ-14를 날짜 3가지로 돌려 경계 공식의 `min`(전달에 걸친 주)과 `max`(다음 달에 걸친 주)를 모두 지나게 했다. 내부 함수를 고정하는 범위 단언은 두지 않는다.
- 집계마다 "인자 받기"(WQ-05 경우)와 "조회 0회"(WQ-06~WQ-13) 두 테스트가 짝으로 끝났는지 Green 보고에서 확인한다. 하나만 끝나면 쓰이지 않는 인자가 남는다.
- "특정 테이블을 건드린 쿼리 수"를 세는 보조 함수 하나만 테스트 파일에서 공유한다. 핵심 단언은 각 테스트 본문에 둔다.
- `test_full_stats_request_reports_measured_cost`의 `before_render_ms > render_ms`가 실패하면 임계값을 추측으로 늦추지 않는다. 실측값을 기록하고 Coach, Quality Verification Lead와 전제를 다시 판단한다. 전제를 바꾸면 요구사항 변경이므로 사용자 확인을 받는다.
- Domain Architecture Reviewer는 계획을 승인했다. 창 범위가 배경 표의 모든 기간을 덮고, `.only()` 필드가 모든 집계가 쓰는 속성을 덮어 추가 조회가 없음을 확인했다. `read_blocks`에 계산기를 넘기면 `user` 인자 대신 `calculator.user`를 쓴다. 호출부는 같은 사용자를 넘기므로 차단 사유가 아니라는 의견이었다.

기존 테스트 영향:

- `apps/stats/test_stats_perf.py`:
  - `TARGET_MAX_QUERIES`를 18에서 5로 바꾼다. 역사 주석에는 한 항목을 덧붙인다.
  - 이 테스트가 지키던 행동("승인된 예산 이내")은 WQ-14로 이어진다.
- `test_full_stats_request_reports_measured_cost`:
  - 주석의 "쿼리 21개"는 낡게 되므로 갱신한다.
  - 단언 `before_render_ms > render_ms`의 여유가 줄어든다. 실패하면 Coach와 다시 판단한다(위험).
- `test_get_monthly_blocks_caches_repeated_calls`, `test_get_monthly_daily_counts_caches_repeated_calls`: 메모를 유지하므로 그대로 통과해야 한다.
- 집계별 기존 테스트(`apps/stats/aggregation/test_*.py`)는 계산기 없이 부르므로 바뀌지 않는다.

## 파일과 단계

1. `apps/stats/aggregation/calculator.py`, `apps/stats/aggregation/test_stats_window.py`: WQ-01~WQ-04.
2. 집계별로 WQ-05 경우를 추가하고 계약 테스트(WQ-06~WQ-13)를 진행한다. 순서는 일간 → 주간 → 월간 → 기간 비교 → 밀도 → 태그 증감 → 요약 → 목표 진행이다.
   - 대상 파일: `daily.py`, `weekly.py`, `monthly.py`, `comparison.py`, `density.py`, `daily_baseline.py`, `summary.py`, `goal_progress.py`
3. `apps/stats/logic.py`: 창을 계산해 계산기를 만들고, 모든 집계에 넘긴다. 이어 WQ-14와 `test_stats_perf.py` 갱신.
4. 전체 회귀, Django 점검, 운영 배포 점검, 로컬 쿼리 수 측정(임시 테스트, 지움).
5. 작업 로그 `docs/refactoring/2026-10-02-stats-query-consolidation-phase2.md`와 `docs/project-status.md`를 갱신하고 PR을 연다.
6. 배포와 운영 측정.

각 시나리오는 따로 커밋한다.

## 배포와 운영 측정

1. PR 머지(사용자). 이어 배포 PR(main→production)을 사용자가 merge commit으로 머지한다. production 트리가 main과 같은지 확인한다.
2. 운영 브라우저 측정. 스위치는 켠 상태다.
   - 한 번도 열지 않은 과거 날짜 5개 이상. 05-04~08과 06-08~12는 쓰지 않는다.
   - 날짜마다 처음 열어 miss를 재고, 1개는 다시 열어 hit를 확인한다.
   - 매 로드에서 `cache`, TTFB, `ctx`, `db`, `db-count`를 기록한다.
   - 기대는 쿼리 5개다. 기준은 1단계 결과(TTFB 2,291ms, `db` 1,691ms)다.
3. 롤백: 되돌리는 커밋을 배포 PR로 배포한다. 캐시 키를 올렸다면 되돌릴 때도 올려야 한다.

## 검증 명령과 기대 증거

- 대상: `conda run -n knou-life-diary python -m pytest apps/stats/aggregation/test_stats_window.py --tb=short`
- 회귀 범위: `conda run -n knou-life-diary python -m pytest apps/stats --tb=short`
- 전체 회귀: `conda run -n knou-life-diary python -m pytest`
- `conda run -n knou-life-diary python manage.py check`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run`
- `git diff --check`

## Deferred

- `calculator=None` 두 경로 정리. 트리거: 모든 운영 호출이 계산기를 넘기게 된 시점. 그때 집계 테스트도 함께 옮긴다.
- 목표 조회 2번 합치기.
- 캐시 hit 경로의 요청당 쿼리 3개.
- A-9(연결 재수립), A-10(리전), B-10(저장 API).
