# 통계 집계의 태그 식별자와 표시명 분리

- 적용: 2026-10-28
- 코드: `apps/stats/aggregation/identity.py`(신규), `calculator.py`, `daily.py`, `weekly.py`, `monthly.py`, `analysis.py`, `apps/stats/services.py`, `apps/stats/use_cases.py`
- 테스트: `apps/stats/aggregation/test_tag_identity.py`(8건), `apps/stats/tests.py::TestStatsServices`

## 증상

사용자가 태그 이름을 `미분류`로 지으면 통계 화면이 깨졌다.

| 집계 | 사용자 태그 `미분류`에 10분 기록 | 
|---|---|
| 일간 | 그 태그가 1,440분(24시간)으로 표시 |
| 주간 | `TypeError: 'int' object is not subscriptable` → `/stats/` 500 |
| 월간 | 그 태그가 744시간(31일 × 24시간)으로 표시 |
| 분석 | 같은 744시간 |

## 원인

집계 4종이 태그의 표시명을 dict key로 썼다(`tag_stats[tag_info["name"]]`). 빈 시간을 채우는 합성 항목은 `apps/core/utils.py`의 상수 `UNCLASSIFIED_TAG_NAME = "미분류"`를 key로 쓴다(`calculator.add_unclassified_data`). 두 key가 같으면 합성 항목의 분이 실제 태그 entry에 더해진다.

주간은 더 나빴다. `weekly.py`의 하루별 `daily_tag_stats`는 `{이름: 분}`(int)인데, 같은 dict에 합성 entry(dict)를 더하는 `calculator.py:105`가 int에 `["minutes"]`를 호출했다.

근본 원인은 사용자가 바꿀 수 있는 값을 식별자로 쓴 것이다. `daily.py`·`weekly.py`가 `tag_name != UNCLASSIFIED_TAG_NAME`으로 활동 시간 제외를 판정하던 것도 같은 뿌리다. 실제 태그 `미분류`의 시간은 `active_hours`에서 빠졌다.

영어 UI에서는 합성 항목의 표시명만 `Unclassified`로 번역되고 key는 여전히 `"미분류"`라, `Unclassified` 태그는 병합되지 않았다. 번역 때문에 결함이 가려진 셈이다.

## 이력

이 결함은 2026-08-15 로컬 브랜치의 커밋 `cd01609`가 고쳤으나, 그 브랜치는 `main`에 병합되지 않았다. 2026-10-04 "미반영 커밋 선별 재적용"(PR #83)에서 수면 제외 판정만 옮겨졌고 식별자 분리는 빠졌다. README는 "해결"이라 적고 있었다. 2026-10-28 README 재작성 중 코드와 대조하다 발견했고, 같은 날 재현 테스트로 확인한 뒤 고쳤다.

## 대안

- 태그 이름에 `미분류`·`Unclassified`를 예약어로 막는다: 폼 검증 한 줄이지만, 다른 언어를 더할 때마다 예약어가 늘고, 이미 그 이름을 쓰는 데이터는 남으며, 표시명을 식별자로 쓰는 구조는 그대로다.
- 집계 key를 식별자로 바꾼다: 실제 태그는 `tag:<id>`, 합성 항목은 `unclassified`. 표시명은 entry의 `name` 필드에 남아 템플릿·JS는 바뀌지 않는다.

두 번째를 골랐다. `cd01609`의 설계를 현재 코드에 다시 적용했다. 당시 함께 바꿨던 `stats.js`(hourly 차트)와 리포지토리 join은 이미 카테고리 key 전환(2026-08-16)으로 필요 없어졌다.

## 구현

- `apps/stats/aggregation/identity.py`가 key 계약을 소유한다: `UNCLASSIFIED_KEY = "unclassified"`, `real_tag_key(tag_id) -> "tag:<id>"`.
- `StatsCalculator.get_tag_info`가 `key`·`tag_id`를 담고, 집계 4종이 `tag_info["key"]`로 색인한다. entry에 `key`·`tag_id`가 들어가고 `name`은 표시 전용이 됐다.
- `add_unclassified_data`·`fill_empty_slots_monthly`가 `UNCLASSIFIED_KEY`로 색인한다. 합성 entry 빌더 4종(`services.py`)에 `key`·`tag_id: None`을 더했다.
- `daily.py`·`weekly.py`의 이름 비교를 지웠다. `process_block`은 실제 태그만 받으므로 비교가 필요 없다. 주간의 수면 제외는 카테고리 key로 판정한다.
- '7일 평균 대비' 열(`daily_baseline.get_tag_deltas_vs_week`)이 `{태그명: delta}`를 돌려주고 `logic.py`가 `tag["name"]`으로 찾던 것을 `{tag_id: delta}`와 `tag["tag_id"]`로 바꿨다. 합성 항목은 `tag_id`가 `None`이라 같은 이름의 실제 태그 값을 빌리지 않는다. 기존 테스트 6건은 `deltas[focus.id]`로 조회 키만 바꿨다.
- 캐시 키 버전 `:v4` → `:v5`. 배포 뒤 옛 모양의 캐시가 읽히지 않는다.

## 검증

Red (2026-10-28, 구현 전): `test_tag_identity.py` 8건 전부 실패. 주간 ko는 `calculator.py:105`의 `TypeError`로, 나머지 7건은 entry에 `key`가 없어 `real_entry is not None` 단언에서 실패했다. 그 단언 메시지에 찍힌 entry가 ko의 병합을 보여 줬다. 일간 `minutes: 1440, blocks: 144`, 월간 `total_hours: 744.0`, 분석 `total_blocks: 4464`. Backend TDD Coach 검토: 경계와 ko/en parametrize, 기존 4개 테스트 보강은 승인, Red 사유 서술은 위와 같이 교정. `TestStatsServices` 4건은 `key`·`tag_id` 등식 불일치로 실패했다.

Green: `conda run -n knou-life-diary pytest apps/stats` 265 passed, 전체 724 passed in 33.91s, `ruff check .` 0건, `manage.py check` 0건.

이어서 STAT-ID-06 `test_synthetic_unclassified_row_does_not_borrow_the_delta_of_a_tag_with_that_name`: 사용자 태그 `미분류`로 7일을 기록하면 `get_stats_context`의 일간 표에서 합성 행의 `delta_vs_week`가 실제 태그의 `0.0`을 빌려 `assert 0.0 is None`으로 Red → `tag_id` 키 전환 뒤 Green. 전체 725 passed.

웹 경계: 테스트 클라이언트로 `미분류` 태그 기록 1개를 가진 계정의 `GET /stats/?date=2026-08-05`가 200을 돌려주고, 일간 표가 `("unclassified", 1430)`·`("tag:<id>", 10)` 두 행으로 나뉘는 것을 일회성 프로브로 확인했다(저장소에 두지 않음).

## 한계

- `comparison.py`·`summary.py`의 기간 비교와 요약 관찰은 여전히 태그 이름으로 합산한다. 사용자 안에서는 `UniqueConstraint(user, name)`으로 이름이 유일하고 합성 항목을 섞지 않으므로 병합은 없다. 결과가 템플릿에 이름으로 노출되는 구조라 그대로 두었다.
- 이미 캐시된 통계는 `v5`로 키가 바뀌어 다음 요청에서 다시 계산된다. 별도 마이그레이션은 없다.
