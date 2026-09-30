# 통계 쿼리 통합 1단계 실행 로그: 목표별 조회 제거 (2026-09-30)

- 계획: `docs/plans/2026-09-30-stats-query-consolidation-plan.md`
- 근거: `docs/refactoring/2026-09-30-stats-server-timing.md`(운영 측정, B-6 분해)
- 브랜치: `perf/stats-query-consolidation`

## 요약

통계 목표 진행 바(`build_goal_progress_rows`)는 목표마다 기록을 따로 조회했다. 이제 모든 목표 기간을 덮는 범위를 한 번 읽고, 목표별로 기간과 태그에 맞는 기록만 더한다. 목표가 없으면 지금처럼 기록을 조회하지 않는다. 결과 값과 공개 함수 시그니처, 캐시 키(`:v2`)는 바꾸지 않았다.

로컬 `get_stats_context` 쿼리 수를 임시 pytest로 쟀다(SQLite, 테스트 DB. 파일은 지움).

| 목표 수 | 이전 | 이후 |
|---|---|---|
| 0 | 18 | 18 |
| 6 | 25 | 20 |
| 12 | 31 | 20 |

운영 계정(목표 약 10개, 쿼리 29개)은 20개가 될 것으로 예상한다. 쿼리 9개가 줄어든다. 쿼리당 81~85ms를 적용하면 약 0.7초가 줄어드는데, 이 값은 추정이다.

## 변경 내용

- `apps/stats/aggregation/goal_progress.py`:
  - `build_goal_progress_rows`는 목표를 일간 → 주간 → 월간 순으로 모은다. 목표가 없으면 빈 목록을 돌려준다.
  - 목표 기간들의 가장 이른 시작일부터 가장 늦은 종료일까지 `TimeBlockRepository.find_by_date_range`를 한 번 호출해 지역 목록으로 만든다.
  - `_minutes_recorded`는 그 목록에서 기간(`start <= date <= end`)과 `tag_id`로 걸러 더한다.
  - `_goal_progress_row`는 사용자 대신 블록 목록을 받는다(비공개 함수).
- `apps/stats/aggregation/test_goal_progress.py`: GQ-01~GQ-03을 추가했다.
- `apps/stats/test_stats_perf.py`: `TARGET_MAX_QUERIES` 위 역사 주석에 이번 항목을 덧붙였다. 값(18)은 그대로다. 이 fixture에는 목표가 없다.
- 백로그 B-3(목표 개수에 비례하는 조회)은 이번 변경으로 해소됐다. `docs/project-status.md`에 표시했다.
- 같은 함수를 목표 페이지(`apps/users/views.py:795`)도 쓴다. 시그니처가 그대로라 호출부는 바뀌지 않았고, 이 페이지도 목표별 조회가 사라진다. 이 페이지의 효과는 재지 않았다.

## 역할과 검토

- 계획 단계:
  - Domain Architecture Reviewer: 한 번 읽기는 `goal_progress.py` 안에 두고, 기존 `find_by_date_range`를 쓴다. `StatsCalculator`와 새 저장소 메서드는 기각했다.
  - Security & Resilience Reviewer: A-8 유지 조건 4가지를 냈다. 조회 결과는 요청 지역 값으로 둘 것을 조건으로 걸었다.
  - Deployment & Operations Reviewer: 단계별로 따로 배포하고, 측정할 때마다 새 날짜를 쓰라고 했다. 캐시 버전 판단 기준도 냈다.
  - Backend TDD Coach: Test List GQ-01~GQ-03을 냈다.
- 사용자가 1단계 계획을 승인했다.
- 구현 후: Backend TDD Coach가 Green을 확정했다.
  - 최소 구현이고 계획 범위 안이다. 공개 시그니처가 그대로이고, 블록은 함수 지역 목록이며, 목표가 없으면 조회하지 않는다.
  - GQ-03은 쿼리 수라는 관찰 가능한 계약만 검증하고 내부를 고정하지 않는다.
  - 추가한 이유 주석은 허용했다.
  - 리팩터링은 허용했지만 필요한 것이 없어 하지 않았다.
  - 새로 추가할 시나리오는 없다.
- Quality Verification Lead: "PR 가능"으로 판정했다.
  - 인수 기준 1~5는 새로 돌린 증거로 통과했다. 6(운영 `db-count`)은 배포 뒤 측정할 항목이다.
  - `build_goal_progress_rows`의 호출처는 통계 화면과 목표 페이지 둘이다. 비공개 함수 `_minutes_recorded`와 `_goal_progress_row`를 부르는 곳은 이 파일 밖에 없다. 둘 다 grep으로 확인했다.
  - 0.7초 절감이 추정이라고 적혀 있어 과장이 아니라고 보았다.

## TDD 증거

모든 명령은 `conda run -n knou-life-diary python -m pytest ... -o cache_dir=/tmp/lifediary-pytest-cache`로 실행했다.

| 시나리오 | 커밋 | Red 또는 대체 증거 | Green |
|---|---|---|---|
| GQ-01 같은 기간 두 목표는 각자 태그만 더함 | `4e6187f` | 처음부터 Green(안전망). 돌연변이: 태그 필터 제거 시 `assert {'독서': 4.0, '집중': 4.0} == {'독서': 1.0, '집중': 3.0}`. 되돌림(diff 0) | 통과 |
| GQ-02 기간이 다른 목표는 자기 기간만 더함 | `ed52ce7` | 처음부터 Green(안전망). 돌연변이 (a) 주 범위를 달 시작으로 자름 → 주간 1.5 ≠ 3.5, (b) 모든 목표를 합집합 범위로 합산 → 일간 3.5 ≠ 0.5. 되돌림(diff 0) | 통과 |
| GQ-03 목표 수와 관계없이 조회 수 동일 | `502dbcd` | `assert 6 == 2`(목표 5개가 1개보다 쿼리 4개 많음) | 목표 진행 테스트 23 passed. `apps/stats` 195 passed, 0 failed |

GQ-01과 GQ-02는 리팩터링 전 안전망이라 처음부터 Green이다. 새 동작을 증명하지 않으므로 돌연변이 검사로 효력을 확인했다. 넣은 결함은 모두 되돌렸고 커밋하지 않았다.

## 검증

코드 HEAD `502dbcd`에서 실행했다.

- 전체 회귀 `python -m pytest -q`: 620 passed, 0 failed, exit 0.
  - 진행 표시 620개가 모두 `.`이었다. 기존 617개에 새 테스트 3개가 더해진 수다.
  - 경고는 221건이고 모두 WhiteNoise `No directory at`이다.
- `apps/stats` 회귀: 195 passed, 0 failed.
- `python manage.py check`: `System check identified no issues (0 silenced).`
- `python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`: exit 0. 경고는 기존 W009 1건이다.
- `python manage.py makemigrations --check --dry-run`: `No changes detected`
- `git diff --check`: exit 0

## 배포와 운영 측정 (아직 하지 않음)

1. PR 머지(사용자).
2. main push로 `deploy-pr.yml`이 main→production 배포 PR을 갱신한다. 사용자가 merge commit으로 머지하면 Render에 배포된다. 머지 뒤 production 트리가 main과 같은지 확인한다.
3. 운영 브라우저 측정. 사용자가 로그인하고, 스위치는 켠 상태다.
   - 한 번도 열지 않은 과거 날짜 5개 이상. 2026-05-04~08은 이미 캐시됐으므로 쓰지 않는다.
   - 날짜마다 처음 열어 miss를 재고, 1개는 다시 열어 hit를 확인한다.
   - 매 로드에서 `cache`, TTFB, `ctx`, `db`, `db-count`를 기록한다. 페이지 내용과 쿠키는 읽지 않는다.
   - 기준은 2026-09-30 miss(TTFB 중앙값 3,294ms, `db` 2,363ms, 쿼리 29개)다. 기대는 쿼리 20개다.
4. 롤백: 되돌리는 커밋을 main에 올려 배포 PR로 배포한다. 결과가 같다는 것을 테스트로 보였으므로 남은 캐시는 문제가 되지 않는다.

## 스위치 유지 (A-8)

사용자가 2026-09-30에 `STATS_SERVER_TIMING_ENABLED=true`를 계속 켜 두기로 했다. 유지 조건(Security & Resilience Reviewer)은 다음과 같다.

1. 헤더는 스위치가 켜져 있고, 로그인한 사용자의 `render()` 200 응답일 때만 붙는다(ST-05, ST-11).
2. 헤더에 사용자명, 쿼리 내용, 다른 사람 데이터가 없다(ST-06).
3. 헤더 내용을 서버에 기록하지 않는다.
4. 엣지 캐시 정책이 바뀌면 A-7(`Cache-Control`)의 우선순위를 올린다.

Deployment & Operations Reviewer는 운영 비용이 요청당 `execute_wrapper` 오버헤드뿐이라 작다고 판단했다.

1단계 뒤에는 헤더의 `db-count`가 목표 수를 반영하지 않는다.

## 미검증 항목

- 운영 효과. 배포 뒤 위 절차로 측정한다.
- 한 번에 읽는 범위는 목표 기간의 합집합이다. 일간·주간·월간 목표가 섞이면 한 달 남짓이다. 목표마다 읽던 때보다 전송하는 행 수는 줄어야 한다. 다만 행 수를 따로 재지는 않았다.

## Deferred

- 2단계 기록 조회 통합. 1단계 운영 측정 뒤 사용자가 정한다.
- 요약 목표 타일의 목표 조회와 목표 진행의 목표 조회 합치기(2단계 후보).
- 캐시 hit 경로의 요청당 쿼리 3개.
- 서버·DB 리전 확인과 이전(인프라 트랙).
- A-7 `Cache-Control`.
