# 통계 캐시 무효화: 날짜 단위 삭제에서 사용자별 세대 토큰으로

- 적용: 2026-10-04 (PR #83, 2026-08-15 로컬 브랜치의 설계를 main에 재구현), 운영 측정 2026-10-06 (PR #88)
- 코드: `apps/stats/use_cases.py`, `apps/stats/receivers.py`, `apps/dashboard/signals.py`, `apps/tags/signals.py`, `apps/users/signals.py`, 각 앱의 `use_cases.py`
- 테스트: `apps/stats/test_cache_invalidation.py`(6건), `apps/stats/test_receivers.py`
- 관련 문서: `2026-04-21_business-logic-and-architecture-guide.md` §6.4 통계 조회 플로우

## 문제

통계 컨텍스트는 `stats:{user}:{date}:{lang}` 키로 캐시됐고(과거 날짜 24시간, 오늘 5분), 무효화는 슬롯이 바뀐 날짜의 키만 지우는 방식이었다. 세 가지가 어긋났다.

1. 바뀐 날짜를 포함하는 주간·월간·12주 기준선은 다른 날짜의 캐시에도 들어 있다. 그 키는 지워지지 않아 TTL이 끝날 때까지 옛 값이 보였다.
2. 태그 이름·색, 목표, 메모는 슬롯이 아니라서 무효화 자체가 없었다.
3. 집계 결과의 모양이 바뀌어도 키에 버전이 없어 배포 뒤 옛 모양의 캐시가 그대로 읽혔다.

원인은 무효화 단위(날짜 하나)와 캐시가 담는 범위(주·월·목표·메모)가 다른 것이다.

## 대안

- 바뀐 날짜가 영향을 주는 모든 키를 계산해 지운다: 12주 기준선 때문에 최대 84개 키를 지워야 하고, 태그·목표·메모 변경은 날짜가 없어 전 키를 지워야 한다.
- `cache.delete_pattern`: Django 기본 백엔드에 없다. 파일 캐시(prod)에서는 디렉터리를 훑어야 한다.
- 사용자별 세대 토큰을 키에 넣는다: 변경 한 번에 그 사용자의 키 전부가 닿을 수 없게 되고, 옛 키는 TTL로 사라진다. 지우는 비용이 0이다.

세 번째를 골랐다. 1인 데이터라 "변경 하나가 그 사용자의 전체 통계 캐시를 버린다"는 비용을 수용했다.

## 구현

키: `stats:{user}:{generation}:{date}:{lang}:v5` (`apps/stats/use_cases.py` `_cache_key`).

- `generation`은 `secrets.token_urlsafe(12)`로 만든 무작위 값이고 `stats-generation:{user}` 키에 TTL 없이 둔다. 숫자 증가가 아니라 무작위인 이유는 두 가지다. `FileBasedCache.incr()`가 원자적이지 않다. 토큰이 캐시에서 밀려났다 돌아올 때 0부터 다시 세면 옛 세대의 키가 되살아난다.
- 기록(`dashboard`), 태그(`tags`), 목표·메모(`users`)를 바꾸는 유스케이스는 `@transaction.atomic` 안에서 쓰고, `transaction.on_commit()`으로 `time_blocks_changed`·`tags_changed`·`goals_changed`·`notes_changed`를 보낸다. `stats/receivers.py`가 받아 `rotate_stats_generation(user_id)`로 토큰을 새 값으로 바꾼다.
- 시그널을 커밋 뒤에만 보내는 이유: 트랜잭션 안에서 토큰을 바꾸면, 커밋 전에 들어온 다른 요청이 아직 반영되지 않은 데이터로 새 세대의 캐시를 채운다. 롤백되면 캐시만 새 세대로 바뀌어 있다.
- 끝의 `v5`는 집계 결과 모양이 바뀔 때 올리는 스키마 버전이다. v3 → v4는 목표 기한(2026-10-06), v4 → v5는 entry의 `key`·`tag_id` 필드(2026-10-28).
- `stats`는 네 시그널을 구독만 한다. `dashboard`가 `stats`를 import하지 않는 방향은 `apps/dashboard/test_domain_boundaries.py`가 고정한다.

## 검증

`apps/stats/test_cache_invalidation.py`는 `django_capture_on_commit_callbacks(execute=True)`로 커밋 콜백을 실제로 실행한다.

| 테스트 | 확인하는 것 |
|---|---|
| `test_committed_slot_change_on_another_date_refreshes_cached_week` | 같은 주의 다른 날짜 저장이 선택 날짜의 주간 합계를 갱신 |
| `test_committed_goal_change_refreshes_cached_statistics` | 목표 저장 뒤 캐시 미스 |
| `test_committed_note_change_refreshes_cached_statistics` | 메모 저장 뒤 캐시 미스 |
| `test_committed_tag_change_refreshes_cached_statistics` | 태그 이름 변경이 일간 표에 반영 |
| `test_rolled_back_slot_change_keeps_serving_cached_statistics` | 롤백된 저장은 세대를 바꾸지 않아 캐시 적중 유지 |
| `test_cached_goal_rows_keep_the_due_date_but_not_its_daily_state` | 기한 상태는 캐시하지 않고 요청한 날 기준으로 붙임 |

운영(2026-10-06): 다른 날짜의 기록을 저장하면 적중이던 날짜가 미스로 바뀌는 것을 `Server-Timing`으로 확인. 미스 969ms, 적중 485ms.

## 한계

- 변경 하나가 그 사용자의 날짜 전체 캐시를 버린다. 하루에 수십 번 기록하는 사용자는 통계를 열 때마다 미스일 수 있다. TTL은 과거 24시간, 오늘 5분 그대로다.
- 관리자 화면(`/admin/`)에서 고친 데이터는 유스케이스를 거치지 않아 세대가 바뀌지 않는다.
- 캐시 쓰기가 실패하면 통계 요청이 500으로 끝난다. 운영 파일 캐시(`/tmp`)는 인스턴스 하나를 전제한다.
- 탈퇴 계정 purge 때 그 사용자의 캐시 항목은 TTL이 끝날 때까지 남는다.
