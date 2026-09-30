# 통계 쿼리 통합 계획 (2026-09-30)

- 근거: `docs/refactoring/2026-09-30-stats-server-timing.md`(운영 측정, B-6 분해)
- 백로그: B-6(운영 통계 캐시 미스 비용 줄이기), A-8(Server-Timing 스위치 유지 검토)
- 브랜치: `perf/stats-query-consolidation`

## 배경

2026-09-30 운영 측정 결과, 통계 페이지 캐시 미스 TTFB 중앙값은 3,294ms였다. 이 가운데 DB execute가 2,363ms(약 72%)다. 쿼리 29개가 차례로 실행되고, 하나에 81~85ms씩 걸렸다. 같은 쿼리가 로컬 PostgreSQL에서는 약 2.3ms였다.

같은 날 임시 pytest로 쿼리가 어디서 나오는지 확인했다. 테스트 DB만 썼고 파일은 지웠다.

- 목표가 0개면 18개, 6개면 25개, 12개면 31개다. 즉 18 + 1 + 목표 수다. 운영 29개는 목표 약 10개로 역산된다.
- 목표 수에 비례하는 부분은 `apps/stats/aggregation/goal_progress.py:60-65` `_minutes_recorded`다. 목표마다 그 기간의 기록을 따로 조회한다. 이 N+1은 `apps/stats/test_stats_perf.py:34-40`에 "목표가 적을 것으로 보고 허용한다"고 기록돼 있었다.
- 나머지 고정 18개 가운데 13개는 같은 사용자의 기록(`dashboard_timeblock`)을 기간만 바꿔 다시 읽는다.

사용자가 2026-09-30에 개선을 진행하기로 했다. Server-Timing 스위치는 계속 켜 두기로 했다.

## 범위

이 계획은 두 단계로 나누고, 이번 승인 대상은 1단계뿐이다. 2단계는 1단계를 운영에서 측정한 뒤 별도 계획으로 승인받는다(아래 "2단계 방향"). Domain Architecture Reviewer와 Deployment & Operations Reviewer가 두 단계를 따로 배포하라고 권고했다. 합쳐 배포하면 쿼리 수가 달라져도 어느 단계 때문인지 구분하지 못하기 때문이다.

1단계 포함:

- `build_goal_progress_rows`가 목표마다 기록을 조회하지 않게 한다. 모든 목표 기간의 합집합을 한 번 읽고, 목표별로 기간과 태그에 맞는 기록만 더한다.
- 목표가 없으면 기록 조회를 하지 않는다. 지금과 같다.
- 스위치 유지 결정(A-8)과 유지 조건을 문서에 남긴다.
- 배포 후 운영에서 같은 방법으로 측정해 전후를 비교한다.

제외:

- 2단계(기록 13번 조회 통합), 요약 목표 타일(`summary._goal_tile`)의 목표 조회와 달성일 조회.
- 캐시 hit에서도 실행되는 요청당 쿼리 3개(세션, 사용자, 내보내기 달 목록).
- 서버와 DB 리전 이전(인프라, 사용자 확인 대기), `Cache-Control`(A-7), 폰트(C-6).
- 통계 결과의 모양이나 값 변경, 스키마 변경, 새 의존성.

## 인수 기준

1. 목표 진행 행(`build_goal_progress_rows`)의 결과는 지금과 같다. 기존 `apps/stats/aggregation/test_goal_progress.py`와 새 안전망 테스트 두 개가 이를 확인한다.
2. 목표가 1개일 때와 5개일 때 `build_goal_progress_rows`의 쿼리 수가 같다.
3. 목표가 없는 사용자의 `get_stats_context` 쿼리 수는 18개 이하로 유지된다(기존 `TARGET_MAX_QUERIES`).
4. 기록 조회는 요청을 처리하는 함수 안의 지역 값으로만 다룬다. 모듈 수준 객체나 싱글턴 속성에 저장하지 않는다(Security & Resilience Reviewer 조건).
5. 캐시 키(`:v2`)는 바꾸지 않는다. 근거는 인수 기준 1이다.
6. 배포 후 운영 `serverTiming`의 `db-count`가 29에서 20으로 준다. 한 번도 열지 않은 과거 날짜 5개 이상에서 miss의 TTFB, `ctx`, `db`, `db-count`를 기록하고, 2026-09-30 기준값과 비교한다.

## Activated Roles

- Backend TDD Coach: Test List와 Red/Green 판정(2026-09-30 Test List 제안 완료).
- Backend & Integration Engineer: 구현, 증거 기록, 문서 갱신.
- Quality Verification Lead: 회귀 위험과 최종 증거 평가.
- Domain Architecture Reviewer: 한 번 읽기를 어디에 둘지 결정(2026-09-30 검토 완료).
- Security & Resilience Reviewer: A-8 유지 조건, 통합 조회의 소유권·동시성 조건(2026-09-30 검토 완료).
- Deployment & Operations Reviewer: 단계별 배포, 측정 방법, 캐시 버전, 롤백(2026-09-30 검토 완료).

## Not Activated

- Product Scope Owner: 사용자가 개선 진행과 스위치 유지를 직접 결정했다.
- Web Experience Designer, Browser Interaction Reviewer, Frontend Implementation Engineer: 템플릿, CSS, 브라우저 JS를 바꾸지 않는다.
- AI Automation Architect: 해당 없음.

## Domain Boundary and Dependency Direction

- 목표 기간 계산(`_period_bounds`, `DAYS_PER_PERIOD`)과 목표별 합산은 지금처럼 `apps/stats/aggregation/goal_progress.py`가 소유한다. 합집합 범위도 이 파일이 계산한다.
- 기록 조회는 기존 `TimeBlockRepository.find_by_date_range`(`apps/dashboard/repositories.py:53-72`)를 그대로 쓴다. 새 저장소 메서드는 만들지 않는다. 목표 기간 3종과 태그 매칭 지식이 dashboard 저장소로 새어 나가기 때문이다.
- `StatsCalculator`에는 두지 않는다. 계산기는 달력 월 범위만 알고, 목표 기간(주·월)은 그와 어긋날 수 있다.
- 의존 방향은 `stats.aggregation -> dashboard.repositories`, `stats.aggregation -> users.repositories` 그대로다. 새 의존은 없다.

## Coupling and Cohesion Review

1. 결합도는 늘지 않는다. 공개 함수 `build_goal_progress_rows(user, selected_date, today=None, now=None)`의 시그니처는 그대로다.
2. 응집도는 유지된다. 목표 합산 로직이 `goal_progress.py` 안에 그대로 있다. 바뀌는 것은 "언제 조회하느냐"뿐이다.

## Pythonic Code Design

- `build_goal_progress_rows`:
  - 목표를 일간 → 주간 → 월간 순으로 한 목록으로 모은다.
  - 목표가 없으면 빈 목록을 돌려준다.
  - 목표 기간들의 가장 이른 시작일과 가장 늦은 종료일로 `find_by_date_range`를 한 번 호출해 목록으로 만든다.
- `_minutes_recorded`는 DB 대신 넘겨받은 블록 목록에서 기간(`start <= date <= end`)과 `tag_id`로 걸러 더한다.
- `_goal_progress_row`는 사용자 대신 블록 목록을 받는다. 비공개 함수라 시그니처를 바꿔도 된다.
- 블록 목록은 함수의 지역 값이고, 읽기만 한다.

## Test List and TDD checkpoints

새 테스트는 `apps/stats/aggregation/test_goal_progress.py`의 `TestGoalProgressRows`에 둔다. 기존 상수 `MONDAY`(2026-07-27 월요일)와 `SUNDAY`(2026-08-02 일요일)를 쓴다. 요일은 `date` 명령으로 확인했다.

순서는 GQ-01 → GQ-02 → GQ-03이다.

- GQ-01과 GQ-02는 리팩터링 전 안전망이라 처음부터 Green이다. 새 동작을 증명하는 테스트가 아니므로, 결함을 일부러 넣어 실패하는지로 효력을 확인한다.
- GQ-03이 이 단계의 Red다.

| ID | 동작 | Given | When | Then | 경계 | 경계 근거 | 테스트 | 예상 Red | 상태 |
|---|---|---|---|---|---|---|---|---|---|
| GQ-01 | 같은 기간의 두 목표는 각자 자기 태그 기록만 더한다 | 일간 목표 2개(태그 다름), 두 태그 모두 선택일에 기록(시간 다름) | `build_goal_progress_rows` | 두 행의 `current_hours`가 각자 태그의 기록 시간 | domain | 한 번 읽은 목록을 여러 목표가 나눠 쓰면 태그 필터가 새기 쉽다 | `test_two_goals_in_the_same_period_sum_their_own_tags_independently` | 처음부터 Green. 돌연변이 검사: 태그 필터 제거 시 실패 | Green |
| GQ-02 | 기간이 다른 목표는 각자 자기 기간 기록만 더한다 | 선택일 `SUNDAY`(주는 7/27~8/2로 지난달에 걸침). 같은 태그로 7/28 2시간, 8/1 1시간, 8/2 0.5시간 기록. 일간·주간·월간 목표 각 1개 | 같음 | 일간 0.5, 주간 3.5, 월간 1.5시간 | domain | 합집합 범위가 주의 지난달 부분을 빠뜨리거나 월간 목표가 지난달 기록을 더하면 틀린다 | `test_goals_of_different_periods_each_sum_only_their_own_period` | 처음부터 Green. 돌연변이 검사: 합집합을 월 범위로만 잡거나 목표별 기간 필터를 빼면 실패 | Green |
| GQ-03 | 목표가 늘어도 목표 진행 계산의 조회 수는 늘지 않는다 | 기록이 있는 사용자. 목표 1개인 경우와 기간이 섞인 목표 5개인 경우 | `build_goal_progress_rows`를 `CaptureQueriesContext`로 감싸 호출 | 두 경우의 쿼리 수가 같다 | contract | 승인된 쿼리 예산 계약(AGENTS.md Result-Oriented Verification) | `test_goal_progress_query_count_does_not_grow_with_goal_count` | 목표 5개가 1개보다 쿼리 4개 많음 | Green |

기존 테스트 영향:

- `apps/stats/aggregation/test_goal_progress.py`의 기존 테스트 20개(목표 달성일 8개, 목표 진행 행 12개)는 공개 함수 시그니처가 그대로라 바꾸지 않는다.
- `apps/stats/test_stats_perf.py`의 `TARGET_MAX_QUERIES = 18`은 목표 없는 fixture 기준이라 값이 그대로다. 위 역사 주석에는 형식(날짜와 이유)에 맞춰 한 항목을 덧붙인다. 목표 N+1을 없앴고, 목표가 있으면 목표 수와 관계없이 기록 조회 1회라는 내용이다. 값은 바꾸지 않는다.

소유권 테스트: Security & Resilience Reviewer는 통합 조회에 "다른 사용자 기록이 섞이지 않음" 테스트를 요구했다.

- 1단계에서는 목표 합산이 사용자 소유 태그의 `tag_id`로 걸러지므로, 사용자 필터를 빼는 결함을 이 테스트로 잡을 수 없다(태그가 사용자마다 따로다).
- 조회 자체는 지금처럼 `find_by_date_range(user, ...)`로 사용자를 거른다.
- 모든 블록을 세는 합계가 생기는 2단계에서 이 테스트를 둔다. 그때는 사용자 필터가 빠지면 합계가 틀려지므로 테스트가 결함을 잡는다.

## 파일과 단계

1. `apps/stats/aggregation/test_goal_progress.py`: GQ-01, GQ-02를 추가한다(Green 확인, 돌연변이 검사, 되돌림).
2. GQ-03을 추가해 Red를 확인한다.
3. `apps/stats/aggregation/goal_progress.py`를 최소 구현으로 고쳐 Green을 만든다. 이어 회귀 범위(`apps/stats/`)를 돌린다.
4. `apps/stats/test_stats_perf.py`: 역사 주석에 한 항목을 덧붙인다(값 그대로).
5. 전체 회귀, Django 점검, 운영 배포 점검을 돌린다.
6. 작업 로그 `docs/refactoring/2026-09-30-stats-query-consolidation.md`를 쓰고 `docs/project-status.md`를 갱신한다(B-6, A-8). 이어 PR을 연다.
7. 배포와 운영 측정(아래).

각 시나리오는 따로 커밋한다.

## 배포와 운영 측정

1. PR 머지(사용자).
2. main push로 `deploy-pr.yml`이 main→production 배포 PR을 갱신한다. 사용자가 merge commit으로 머지하면 Render에 배포된다. 머지 뒤 production 트리가 main과 같은지 확인한다.
3. 운영 브라우저 측정. 사용자가 로그인하고, 스위치는 켠 상태다.
   - 한 번도 열지 않은 과거 날짜 5개 이상. 2026-05-04~08은 이미 캐시됐으므로 쓰지 않는다.
   - 날짜마다 처음 열어 miss를 재고, 1개는 다시 열어 hit 경로도 확인한다.
   - 매 로드에서 `cache`, TTFB, `ctx`, `db`, `db-count`를 기록한다. 페이지 내용과 쿠키는 읽지 않는다.
   - 비교는 miss끼리만 한다. 기준은 2026-09-30의 miss TTFB 중앙값 3,294ms, `db` 2,363ms, 쿼리 29개다. 기대는 쿼리 20개와 `db` 약 0.7초 감소(추정)다.
4. 롤백:
   - 되돌리는 커밋을 main에 올려 배포 PR로 배포한다.
   - 스위치는 이 변경과 무관하다.
   - 롤백 뒤에도 새 코드가 만든 캐시가 최대 24시간 남을 수 있다. 인수 기준 1로 결과가 같다는 것을 보였으므로 영향은 없다.

## 스위치 유지 (A-8)

사용자가 2026-09-30에 `STATS_SERVER_TIMING_ENABLED=true`를 계속 켜 두기로 했다.

Security & Resilience Reviewer는 지금 바꿀 것이 없다고 판단했다. 유지 조건은 다음과 같다.

1. 헤더는 스위치가 켜져 있고, 로그인한 사용자의 `render()` 200 응답일 때만 붙는다(ST-05, ST-11 회귀 유지).
2. 헤더에 사용자명, 쿼리 내용, 다른 사람 데이터가 없다(ST-06 회귀 유지).
3. 헤더 내용을 서버에 기록하지 않는다. 새 로깅을 추가하지 않는다.
4. A-7(`Cache-Control`)은 별도 백로그로 남긴다. 엣지 캐시 정책이 바뀌면 헤더 노출도 함께 커지므로, 그때 A-7의 우선순위를 올린다.

Deployment & Operations Reviewer는 운영 비용이 요청당 `execute_wrapper` 오버헤드뿐이라 작다고 판단했다.

1단계 뒤에는 `db-count`가 목표 수를 반영하지 않는다. 헤더로 드러나는 정보가 줄어드는 방향이다.

## 2단계 방향 (이번 승인 대상 아님)

1단계 운영 측정 뒤 필요성을 다시 판단하고, 별도 계획과 Test List로 승인받는다. 검토자 권고를 기록해 둔다.

- 구조(Domain Architecture Reviewer):
  - `StatsCalculator`에 합집합 범위를 한 번 읽는 `blocks_between(start, end)`를 둔다.
  - 합집합 범위는 `logic.get_stats_context`가 계산해 넘긴다.
  - 집계 함수들은 `calculator=None` 선택 인자를 받아, 없으면 지금처럼 조회한다.
  - 범용 캐시나 전략 객체로 일반화하지 않는다.
  - 두 경로가 계속 남는 것은 Deferred로 관리한다.
- 테스트(Backend TDD Coach): 착수 전에 `get_stats_context` 결과를 고정하는 특성 테스트를 둔다. 풍부한 fixture에 다음을 담고, 실제 값을 확인하며, 돌연변이 검사로 효력을 확인한다. 이어 쿼리 예산 상한을 낮춘다.
  - 목표 기간 3종
  - 달 경계를 넘는 주, 전월 데이터
  - 12주 기준선
  - 미분류 블록
  - 오늘 호출과 과거 날짜 호출
  - 다른 사용자의 같은 날짜 기록
- 보안(Security & Resilience Reviewer): 읽은 기록은 요청마다 새로 만든다. 원본 블록을 따로 캐시하지 않는다. `.only()`와 `select_related`를 유지한다.
- 운영(Deployment & Operations Reviewer): 특성 테스트로 결과가 같다는 것을 보이지 못하면 캐시 키를 `:v3`으로 올린다.

## 검증 명령과 기대 증거

- 대상: `conda run -n knou-life-diary python -m pytest apps/stats/aggregation/test_goal_progress.py --tb=short`
- 회귀 범위: `conda run -n knou-life-diary python -m pytest apps/stats --tb=short`
- 전체 회귀: `conda run -n knou-life-diary python -m pytest`
- `conda run -n knou-life-diary python manage.py check`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run`
- `git diff --check`

## Deferred

- 2단계 기록 조회 통합. 트리거: 1단계 운영 측정 결과를 본 사용자 결정.
- 요약 목표 타일의 목표 조회(`summary.py:138`)와 목표 진행의 목표 조회(`users/repositories.py:51`) 합치기. 2단계 후보다.
- 캐시 hit 경로의 요청당 쿼리 3개. 트리거: hit TTFB 개선이 필요할 때.
- 서버·DB 리전 확인과 이전. 사용자가 Render 서비스 리전과 Supabase 프로젝트 리전을 확인한 뒤 별도 인프라 트랙으로 판단한다.
- A-7 `Cache-Control`. 엣지 캐시 정책이 바뀌면 우선순위를 올린다.
