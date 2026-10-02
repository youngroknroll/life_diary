# 통계 쿼리 통합 2단계 실행 로그: 요청당 기록 1회 조회 (2026-10-02)

- 계획: `docs/plans/2026-10-02-stats-query-consolidation-phase2-plan.md`
- 1단계: `docs/refactoring/2026-09-30-stats-query-consolidation.md`
- 브랜치: `perf/stats-query-consolidation-phase2`

## 요약

통계 화면 데이터(`get_stats_context`)는 같은 사용자의 기록을 기간만 바꿔 여러 번 읽었다. 이제 한 번만 읽는다. 동작은 다음과 같다.

- `get_stats_context`가 모든 집계의 기간을 덮는 창을 계산한다. 창은 D의 주 시작 12주 전부터 D의 주 끝과 달 끝 중 늦은 날까지다.
- `StatsCalculator`가 그 창을 한 번 읽는다.
- 각 집계는 자기 기간만 그 목록에서 꺼낸다.
- 카테고리 목록도 한 번만 읽는다.

결과 값과 캐시 키(`:v2`)는 바꾸지 않았다.

로컬 `get_stats_context` 쿼리 수(SQLite, 임시 테스트. 파일은 지움):

| 목표 수 | 1단계 전 | 1단계 후 | 2단계 후 |
|---|---|---|---|
| 0 | 18 | 18 | 5 |
| 6 | 25 | 20 | 5 |
| 12 | 31 | 20 | 5 |

남은 5개는 기록 1, 카테고리 1, 목표 2, 메모 1이다. 운영 계정(1단계 후 20개)도 5개가 될 것으로 예상한다. 쿼리당 84.5ms를 적용하면 약 1.3초가 줄어드는데, 이 값은 추정이다.

## 변경 내용

- `apps/stats/aggregation/calculator.py`:
  - `StatsCalculator(user, selected_date, window=None)`
  - `blocks_between(start, end)`: 창 안이면 처음 한 번만 창 전체를 `find_by_date_range`로 읽고 날짜별로 묶어 둔다. 창이 없거나 창 밖이면 직접 읽는다.
  - `categories()`: 카테고리 목록을 한 번만 읽는다.
  - 월간 블록은 `blocks_between`으로 가져오고, 날짜별 개수는 그 목록에서 센다(`Counter`).
  - 모듈 함수 `read_blocks(user, start, end, calculator=None)`: 계산기가 있으면 그 창에서, 없으면 저장소에서 읽는다.
- 집계:
  - `daily.py`, `weekly.py`, `monthly.py`: 계산기에서 읽는다(이미 계산기를 받던 함수).
  - `comparison.get_period_delta`, `density.get_density_grid`, `daily_baseline.get_tag_deltas_vs_week`, `summary.build_summary`, `goal_progress.build_goal_progress_rows`, `goal_progress.goal_hit_dates`: `calculator=None` 선택 인자를 받는다. 계산기 없이 부르면 지금처럼 직접 읽는다.
- `apps/stats/logic.py`: `_stats_window`로 창을 계산하고, 계산기 하나를 모든 집계에 넘긴다.
- 테스트:
  - `apps/stats/aggregation/test_stats_window.py`(신규)
  - `apps/stats/test_stats_perf.py`: `TARGET_MAX_QUERIES` 18→5, 역사 주석 한 항목 추가.

## 역할과 검토

- 계획 단계:
  - Domain Architecture Reviewer: 승인했다. 창 범위가 모든 기간을 덮고, `.only()` 필드가 모든 집계가 쓰는 속성을 덮어 추가 조회가 없음을 확인했다.
  - Backend TDD Coach: Test List를 검토했다. 집계마다 두 테스트를 짝으로 끝낼 것, 보조 함수는 하나만 공유할 것, 렌더 단언이 실패하면 늦추지 말 것을 권고했다.
  - Security & Resilience Reviewer와 Deployment & Operations Reviewer의 조건(2026-09-30)은 인수 기준 3·4·6·7로 반영했다.
- 사용자가 2단계 계획을 승인했다.
- 구현 후 Backend TDD Coach가 WQ-01~WQ-14와 WQ-08b를 모두 Green으로 인정했다.
  - 집계마다 "인자 받기"와 "조회 0회" 짝이 끝났고, 쓰이지 않는 `calculator` 인자는 없다.
  - 처음부터 Green인 안전망과 돌연변이 검사 절차도 타당하다고 보았다.
  - 리팩터링은 동작을 바꾸지 않는 범위에서 허용했지만, 필요한 것이 없어 하지 않았다.
- Quality Verification Lead: "PR 준비 완료"로 판정했다.
  - 인수 기준 1~6은 새로 돌린 증거로 통과했다. 7(운영 측정)은 배포 뒤 확인할 항목이다.
  - 계산기 없이 부르는 운영 호출은 목표 페이지 하나이고, 지금과 같게 직접 조회한다. `apps/stats/export.py`는 바뀐 함수를 쓰지 않는다.
  - 낡은 주석 1건을 짚어 고쳤다.

## TDD 증거

모든 명령은 `conda run -n knou-life-diary python -m pytest ... -o cache_dir=/tmp/lifediary-pytest-cache`로 실행했다. 시나리오마다 따로 커밋했다.

| 시나리오 | 커밋 | Red 또는 대체 증거 | Green |
|---|---|---|---|
| WQ-01 창 구간 = 직접 조회(순서 포함) | `ba76041` | `TypeError: ... unexpected keyword argument 'window'`(6건) | 최소 구현(매번 직접 조회) |
| WQ-02 창은 한 번만 읽음 | `930464e` | `assert 3 == 1` | 창을 날짜별로 묶어 둠 |
| WQ-03 창 밖 구간도 빠짐없이 | `9575c15` | 창 시작 이전 기록이 빠짐 | 직접 조회로 넘김 |
| WQ-04 카테고리 1회 | `5c76a50` | `AttributeError` | 메모 |
| WQ-05 + WQ-06 일간 | `cfc3c3b` | WQ-05 처음부터 Green(이미 계산기를 받음). WQ-06 `find_by_date` 1건 | 돌연변이: `blocks_between`이 마지막 날을 빼면 일간 3건 실패 |
| WQ-05 + WQ-07 주간 | `5dd02d5` | WQ-07 기록 1, 카테고리 1 | 같은 돌연변이로 주간 3건 실패 |
| WQ-05 + WQ-08 월간·태그 분석 | `6b9f294` | WQ-08 월간 블록, `GROUP BY` 개수, 카테고리 | 같은 돌연변이로 6건 실패 |
| WQ-08b 날짜별 개수가 미분류 칸 포함 | `6b9f294` | 처음부터 Green(안전망). 돌연변이 "태그 있는 칸만 세기"에서 실패 | 아래 "구현 중 발견" |
| WQ-05 + WQ-09 기간 비교 | `be65760` | WQ-05 `TypeError`(6건), WQ-09 기록 6건 | 같은 돌연변이로 6건 실패 |
| WQ-05 + WQ-10 밀도 | `84a25f3` | `TypeError`(3건), 기록 1건 | 3건 실패 |
| WQ-05 + WQ-11 태그 증감 | `3df5e24` | `TypeError`(3건), 기록 1건 | 3건 실패 |
| WQ-05 + WQ-12 요약 | `f110b6f` | `TypeError`(3건), 기록 9건 | 3건 실패 |
| WQ-05 + WQ-13 목표 진행 | `b42993d` | `TypeError`(3건), 기록 1건 | 3건 실패 |
| WQ-14 쿼리 상한 5 | `002b675` | 목표 없음 16, 목표 있음 18 | 돌연변이: 창 끝을 달 끝으로만 두면 다음 달 걸친 경우 7개로 실패, 시작에서 12주 기준선을 빼면 모든 경우 6개로 실패 |

WQ-05의 비교 경우는 과거 날짜, 전달에 걸친 주(2026-08-02), 오늘(`today`를 선택일로 주입) 세 가지다. 공통 fixture에는 다음을 담았다.

- 같은 날짜에 기록한 두 사용자
- 미분류 칸과 빈 날
- 일간·주간·월간 목표
- 2026-01-05~08-31 기록

넣은 결함은 모두 되돌렸고 커밋하지 않았다.

### 구현 중 발견 (WQ-08b)

날짜별 개수를 "태그 있는 칸만" 세는 결함을 넣어 보았다. 이 결함은 WQ-05에서도, 기존 `apps/stats` 테스트 전체에서도 잡히지 않았다.

- WQ-05가 못 잡은 이유: 창이 있든 없든 같은 `Counter` 계산을 쓰므로 양쪽이 똑같이 틀린다.
- 기존 테스트가 못 잡은 이유: 월간 테스트에 미분류 칸이 없다. 이전 구현(`find_daily_counts`)도 이 성질을 지키는 테스트가 없었다.

그래서 계산기의 날짜별 개수를 DB `Count` 집계와 직접 비교하는 안전망 WQ-08b를 더했고, 계획 Test List에도 기록했다.

## 검증

코드 HEAD `002b675`에서 실행했다.

- 전체 회귀 `python -m pytest -q`: 671 passed, 0 failed, exit 0.
  - 진행 표시 671개가 모두 `.`이었다. 1단계 뒤 620개에 새 테스트 51개가 더해진 수다.
  - 새 테스트 51개 내역: WQ-01 6, WQ-02~WQ-04 3, WQ-05 30(집계 10 × 경우 3), WQ-06~WQ-13 8, WQ-08b 1, WQ-14 목표 있는 경우 3.
  - 경고 221건은 모두 WhiteNoise `No directory at`이다.
- `apps/stats` 회귀: 246 passed, 0 failed.
- `test_full_stats_request_reports_measured_cost`의 `before_render_ms > render_ms`는 그대로 통과했다(계획에서 위험으로 적은 항목).
  - 같은 fixture로 다시 재 보니 요청 전체 쿼리는 8개, 렌더 전은 119.7~230.9ms, 렌더는 8.1~27.9ms(3회)였다. 이 값으로 테스트 주석의 "쿼리 21개, 수십 배"를 고쳤다. Quality Verification Lead가 이 낡은 주석을 짚었다.
- `python manage.py check`: `System check identified no issues (0 silenced).`
- `python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`: exit 0. 경고는 기존 W009 1건이다.
- `python manage.py makemigrations --check --dry-run`: `No changes detected`
- `git diff --check origin/main..HEAD`: exit 0

## 배포와 운영 측정 (아직 하지 않음)

1. PR 머지(사용자). 이어 배포 PR(main→production)을 사용자가 merge commit으로 머지한다. production 트리가 main과 같은지 확인한다.
2. 운영 브라우저 측정. 스위치는 켠 상태다.
   - 한 번도 열지 않은 과거 날짜 5개 이상. 05-04~08과 06-08~12는 쓰지 않는다.
   - 날짜마다 처음 열어 miss를 재고, 1개는 다시 열어 hit를 확인한다.
   - `cache`, TTFB, `ctx`, `db`, `db-count`를 기록한다.
   - 기대는 쿼리 5개다. 기준은 1단계 결과(TTFB 중앙값 2,291ms, `db` 1,691ms, 쿼리 20개)다.
3. 롤백: 되돌리는 커밋을 배포 PR로 배포한다. 결과가 같다는 것을 WQ-05로 보였으므로 캐시 키는 그대로다.

## 미검증 항목

- 운영 효과. 배포 뒤 위 절차로 측정한다.
- 창 하나에 담는 행 수와 메모리. 창은 최대 약 17주이고, 매일 144칸을 다 채운 사용자라면 약 1만 7천 행이다. 이전에도 기준선 조회 하나가 12주를 읽었으므로 요청이 읽는 행의 총합은 줄어든다고 본다. 행 수와 메모리를 따로 재지는 않았다.

## Deferred

- `calculator=None` 두 경로 정리. 트리거: 모든 운영 호출이 계산기를 넘기게 된 시점.
  - 지금 계산기 없이 부르는 운영 호출은 목표 페이지의 `build_goal_progress_rows`(`apps/users/views.py:795`)다.
- `read_blocks`에 계산기를 넘기면 `user` 인자 대신 계산기의 사용자를 쓴다. 호출부는 같은 사용자를 넘기므로 지금은 문제가 없다(Domain Architecture Reviewer, 비차단).
- `TimeBlockRepository.find_daily_counts`는 이제 운영 코드에서 부르는 곳이 없다. WQ-08b의 비교 기준으로 쓰이고, dashboard 포트 정의(`apps/dashboard/ports.py:15`)에도 남아 있다. 정리 여부는 dashboard 쪽 작업에서 정한다.
- `_stats_window`의 `min()` 세 항 가운데 "전달 1일"과 "D−6일"은 지금 상수로는 결과에 영향을 주지 않는다. 12주 기준선(84일)이 항상 더 이르기 때문이다. 계획이 정한 방어적 공식이라 그대로 두고, 이 항이 선택되는 경우를 따로 시험하지 않는다. 트리거: `BASELINE_MAX_WEEKS`나 `ROLLING_DAYS`를 바꿀 때 이 `min()`을 다시 검증한다(Backend TDD Coach).
- 목표 조회 2번 합치기, 캐시 hit 경로 쿼리 3개, A-9, A-10, B-10.
