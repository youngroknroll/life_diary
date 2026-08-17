# P0 v2 2단계 — `category_stats` 집계 + 기간 라벨 규칙

계획: `docs/plans/2026-08-16_p0-v2-handoff-plan.md` 2단계 (§2, 목업 4g).
브랜치: `feat/p0-v2-handoff`.

## 승인된 범위

- `weekly.py`·`monthly.py`에 `category_stats`(5개 카테고리 × `daily_hours`·`total_hours`)
  추가. `weekly.py`에 `week_start`(항상 월요일) 추가.
- `daily.py`의 `hourly_stats` 키를 태그명 → 카테고리 key(work/move/care/life/sleep)로 전환.
  미분류(빈 슬롯) 시간은 `hourly_stats`에 더는 넣지 않는다(표 `tag_stats`에는 계속 남음).
- 기간 라벨 규칙(지난 7일=rolling, 이번 주=calendar) 자체는 이미 `summary.py`/
  `weekly_summary.py`가 구분해 만들고 있음을 확인 — 이 단계에서 새 코드 불필요, 프런트
  카피(6단계 이후)에서 범위 병기만 붙이면 된다.

## Activated Roles

- Domain Architecture Reviewer(스키마 확장이 `stats` 앱 경계 안인지) — `apps/stats/
  aggregation/category_keys.py`에 slug→key 매핑을 신설해 `apps.tags`의 `Category.slug`를
  그대로 프런트에 노출하지 않도록 분리. `stats`는 `apps.tags.repositories.
  CategoryRepository`를 통해서만 읽고 쓰지 않는다 — 경계 위반 없음.
- Backend TDD Coach, Backend & Integration Engineer — 아래 Test List.
- Quality Verification Lead — 완료 판정.
- Not activated: 프런트·보안·배포 역할(JSON 응답 키 추가/개명만, HTML·JS·인증·배포 영향 없음).

## Test List

| Scenario ID | Business behavior | Given | When | Then | Boundary | Test name |
|---|---|---|---|---|---|---|
| WK-1 | 카테고리 daily_hours 합이 그 카테고리 태그들의 시간 합과 같다 | investment 카테고리 태그로 월요일 6칸(60분) 기록 | 주간 집계 조회 | work 카테고리 daily_hours[0]=1.0, total_hours=1.0 | domain | test_category_daily_hours_sum_matches_its_tags_time |
| WK-2 | category_stats는 항상 5개 카테고리를 다 나열한다 | 태그 1개만 기록 | 주간 집계 조회 | key 집합={work,move,care,life,sleep} | domain | test_category_stats_always_lists_all_five_categories |
| WK-3 | 기록 없는 카테고리는 0시간으로 보고된다 | work만 기록 | 주간 집계 조회 | sleep의 daily_hours 전부 0, total_hours=0 | domain | test_unrecorded_category_reports_zero_hours |
| WK-4 | 미분류 시간은 category_stats 어디에도 안 들어간다 | work 1칸만 기록(나머지 143칸 자동 미분류) | 주간 집계 조회 | category_stats 전체 daily_hours 합=0.2(work 몫만) | domain | test_unclassified_time_is_excluded_from_category_stats |
| WK-5 | 같은 카테고리 태그 둘은 한 항목으로 합산된다 | investment 카테고리 태그 2개로 5칸 기록 | 주간 집계 조회 | work daily_hours[0]=0.8 | domain | test_two_tags_in_same_category_sum_into_one_entry |
| WK-6 | 서로 다른 카테고리는 섞이지 않는다 | investment 3칸 + proactive 2칸 | 주간 집계 조회 | work=0.5, move=0.3 | domain | test_two_categories_stay_independent |
| WK-7 | week_start는 항상 월요일이다 | 임의 조회일 | 주간 집계 조회 | week_start==그 주 월요일, weekday()==0 | domain | test_week_start_is_always_monday |
| MO-1~4 | WK-1/2/3/6과 동일 구조, 월간 daily_hours 길이=그 달 일수 | 8월 기준 | 월간 집계 조회 | 대응 assert (월별 total_days=31) | domain | `test_*`(monthly) 4건 |
| DA-1 | hourly_stats 키가 태그명이 아니라 카테고리 key다 | investment 태그로 00:00-00:30(3칸) 기록 | 일간 집계 조회 | hourly_stats[0]=={"work":30} | domain | test_hourly_stats_key_by_category_not_tag_name |
| DA-2 | 같은 카테고리 두 태그가 같은 시간대 항목으로 합쳐진다 | investment 태그 2개로 00:00-00:30 나눠 기록 | 일간 집계 조회 | hourly_stats[0]=={"work":30} | domain | test_two_tags_in_same_category_sum_into_one_hourly_entry |
| DA-3 | 빈 슬롯은 hourly_stats에 키로 나타나지 않는다 | investment 20분만 기록 | 일간 집계 조회 | hourly_stats[0]=={"work":20}, "미분류" 키 없음 | domain | test_unrecorded_time_is_absent_from_hourly_stats_not_a_key |
| DA-4(회귀 확인) | 태그 상세 표는 여전히 미분류 시간을 보고한다 | investment 1칸만 기록 | 일간 집계 조회 | tag_stats의 "미분류" minutes>0 | domain | test_tag_level_table_still_reports_unclassified_time |

전부 `Status: Green`, `Refactoring allowed: No`(추가 리팩터 없이 그대로 통과).

## Red → Green

- Red: `apps/stats/aggregation/test_weekly.py`·`test_monthly.py`·`test_daily.py` 신설,
  각 파일에서 `KeyError: 'category_stats'` / `KeyError: 'week_start'` / 잘못된
  `hourly_stats` 키 구성으로 예상대로 실패 확인.
- Green 구현:
  - `apps/stats/aggregation/category_keys.py`(신설) — `Category.slug` → 짧은 key
    (investment→work, proactive→move, passive→care, basic_life→life, sleep→sleep) 매핑.
    스펙의 `CATEGORY_LINE`/`CATEGORY_FILL`이 이미 이 다섯 키를 쓰므로 그대로 맞춘다.
  - `apps/stats/aggregation/calculator.py`의 `get_tag_info`에 `category_key`·
    `category_name` 추가. `fill_empty_slots_daily`에서 `add_unclassified_to_hourly_stats`
    호출(및 이제 쓰이지 않는 메서드 자체)을 제거 — 내가 만든 고아 코드라 함께 지운다.
  - `apps/stats/aggregation/weekly.py`·`monthly.py`에 category 롤업 딕셔너리를 기존
    태그 롤업과 같은 패턴(주 루프 안에서 daily_minutes 누적 → 루프 밖에서 hours 변환)으로
    추가. `CategoryRepository.find_all()`로 5개 카테고리를 항상 시드해 빈 카테고리도
    0시간으로 나온다.
  - `apps/stats/aggregation/daily.py`의 `hourly_stats[hour][tag_name]` →
    `hourly_stats[hour][category_key]`.
- **회귀(발견 후 즉시 수정)**: `get_tag_info`가 `block.tag.category`를 읽게 되면서
  `apps/stats/test_stats_perf.py::test_get_stats_context_query_count_within_target`이
  4408쿼리로 폭발(예산 17). 원인은 `TimeBlockRepository.find_by_date`·`find_by_month`가
  `tag__category`를 select_related하지 않았기 때문(`find_by_date_range`만 이미
  했었다 — 동일한 이유의 주석이 이미 있었음). 두 메서드에 `tag__category`를 추가했다.
  `find_by_date`는 dashboard 화면·API가 공유하므로 `.only()`로 필드를 제한하지 않고
  select_related만 추가(안전한 additive 변경). `find_by_month`는 stats 전용이라
  `find_by_date_range`와 같은 `.only()` 패턴을 그대로 맞췄다.

## 검증

- `conda run -n knou-life-diary pytest apps/stats/aggregation/ apps/stats/test_stats_perf.py -q`
  — 전부 통과.
- `conda run -n knou-life-diary pytest apps/stats apps/tags apps/dashboard apps/users -q`
  — 전부 통과(회귀 없음).
- `conda run -n knou-life-diary pytest -q`(전체) — 523개 수집, exit 0, 실패 0건.
- `conda run -n knou-life-diary python manage.py check` — 이슈 없음.
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run` —
  변경 없음(모델 필드 변경 없음, 예상대로).

## 알려진 비일관 상태 (브랜치 내부, 의도됨)

`daily.py`의 `hourly_stats`가 이제 카테고리 key로 나오므로, 아직 재작성 전인
`apps/stats/static/stats/js/stats.js`의 `renderHourlyBarChart`(태그명·`tag.color` 기준)는
이 브랜치에서 당장 실행하면 깨진 채로 렌더된다. 3단계(stats.js 전면 재작성)가 소비자
쪽을 맞춘다 — 계획대로 같은 브랜치 안에서만 존재하는 과도기이며, 이 상태로 배포하지
않는다.

## Deferred

없음(이 단계 범위 안에서 미룬 항목 없음). 기간 라벨 규칙의 "범위 병기" 문구는 6단계
이후 템플릿 작업에서 실제로 붙는다.
