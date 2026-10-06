# Critical Backend Remediation — Lane A·C 실행 로그

작성일: 2026-08-15 (Lane A), 2026-08-16 (Lane C 추가)

- 계획: `docs/plans/2026-08-15_critical-remediation-plan.md` (Lane A, Task 0~9)
- 설계: `docs/plans/2026-08-15_critical-remediation-design.md`
- 담당 역할: Backend & Integration Engineer (Backend TDD Coach 계약에 따라 한
  Scenario씩 Red/Green), Domain Architecture Reviewer 결정은 설계 문서를 따름
- 브랜치: `feat/grid-label-and-hour-axis` (커밋·push·PR 없음 — 사용자 몫)

## 승인 범위 (Lane A만)

1. 통계 real-tag / synthetic-unclassified identity 분리
2. 수면 통계를 tag name이 아닌 `Category.slug == "sleep"` 기준으로 판정
3. 이동 없는 태그 삭제 시 연결된 TimeBlock·memo 실제 삭제
4. 기존 tagless TimeBlock 정리 migration과 tag 필수 invariant
5. 슬롯·태그·목표·메모 변경의 post-commit stats cache invalidation

Lane B(대시보드 프런트 보안·상호작용), Lane C(계정 수명주기), desktop,
scheduler, SMTP/reCAPTCHA, 일반 UX 결함은 이번 실행에서 수정하지 않았다.

## Task 0 — 기준선 (2026-08-15 신선한 실행)

- `git status -sb`: 브랜치 `feat/grid-label-and-hour-axis`, 사용자 소유 변경
  (`docs/project-status.md` 수정, 미추적 계획서 2건, `월간_소비시간_기록_시트.xlsx`)
  보존. xlsx는 수정·이동·stage하지 않았다.
- 전체 pytest: `501 passed in 291.28s (0:04:51)`
- `manage.py check`: 이슈 없음
- `makemigrations --check --dry-run`: No changes detected
- `node --check` dashboard.js / stats.js: exit 0
- `msgfmt --check-format` ko/en × django/djangojs 4건: 통과

## Scenario별 Red/Green 기록

각 Scenario의 정확한 Red 명령·이유와 Green 증거는 계획서 Backend Test List의
Status/Evidence 열에 실행 시점에 기록했다. 요약:

| Scenario | Red (예상 이유) | Green 증거 |
|---|---|---|
| STAT-ID-01 | entry에 `key` 부재, ko는 표시명 dict key로 병합 | targeted + `apps/stats/tests.py` 12 passed, `node --check` exit 0 |
| STAT-ID-02 | 월간 entry `key` 부재, ko 병합 | targeted + tests.py + test_weekly_summary 25 passed |
| STAT-ID-03 | `tag_weekly_stats` entry `key` 부재 | targeted + tests.py 12 passed |
| STAT-ID-04 | analysis entry `key` 부재, ko는 빈 시간 병합 | targeted 2 passed, 집계 회귀 124 passed(쿼리 예산 유지) |
| STAT-WEEK-01 | `수면`만 제외되고 `Sleep`/커스텀명은 active로 계산 | targeted 3 passed, 집계 회귀 127 passed |
| TAG-DEL-01 | SET_NULL로 tagless 행 3개 잔존 | tag_migration + personal_tags 17 passed |
| TAG-MIG-01 | `NodeNotFoundError: dashboard 0007` | migration 테스트 + tag_migration 9 passed, drift 없음 |
| CACHE-SLOT-01 | 8/1 커밋 후 8/15 캐시 잔존 (`0 != 0.2`) | targeted + receivers + dashboard use case 11 passed |
| CACHE-TX-01 | — **discovered Green** (Task 6이 on_commit으로 이동한 결과, 가짜 Red 미생성) | 1 passed, 회귀 20 passed |
| CACHE-TAG-01 | 캐시가 옛 태그명 서빙 | targeted 1 passed, tags+cache 회귀 99 passed |
| CACHE-GOAL-01 | 캐시된 `summary.goal=None` 잔존 | targeted 1 passed |
| CACHE-NOTE-01 | 캐시가 옛 메모 서빙 | targeted 1 passed, 회귀 19 passed |

## 구현 내용

### 통계 identity (Task 1~3)

- `apps/stats/aggregation/identity.py` 신설: `UNCLASSIFIED_KEY = "unclassified"`,
  `real_tag_key(tag_id) -> "tag:<id>"`. 이 모듈이 key 계약을 소유한다.
- `StatsCalculator.get_tag_info()`가 `key`, `tag_id`, `category_slug`를 추가로
  반환. daily/monthly/weekly/analysis 4개 집계와 hourly_stats가 표시명 대신
  이 key로 색인한다. 표시 문자열(`name`)은 그대로 유지되어 사용자에게 내부
  key가 노출되지 않는다.
- 합성 미기록 entry 빌더 4종(`apps/stats/services.py`)에 `key`/`tag_id=None`
  추가. `미분류`/`Unclassified` 이름 예약·거부는 하지 않았다.
- `renderHourlyBarChart()`(stats.js)가 `tag.key`로 분 값을 찾고 `tag.name`을
  label로만 쓴다.
- 주간 active 제외를 `excluded_tags = {수면, 미분류}` 이름 비교에서
  `tag_info["category_slug"] != "sleep"`으로 교체. `SLEEP_TAG_NAME` 상수 제거.
- N+1 방지: `find_by_date`/`find_by_month`에 `tag__category` join 확장
  (쿼리 수 불변 — `test_stats_perf.py` 17쿼리 예산으로 검증).

### 태그 삭제와 migration (Task 4~5)

- `TimeBlockRepository.delete_blocks_for_tag(tag)` 신설.
  `DeleteTagUseCase`가 이동 목적지 없으면 같은 transaction에서 기록·메모를
  먼저 삭제한 뒤 태그를 지운다.
- 구 테스트 `test_deleting_a_used_tag_turns_its_blocks_unlogged`(SET_NULL 잔존
  assertion)는 확인된 결함이므로 TAG-DEL-01로 교체했다.
- `dashboard/migrations/0007_delete_tagless_blocks_and_require_tag.py`:
  ① RunPython으로 `tag_id IS NULL` 행 삭제, ② `AlterField`로
  `null=False, on_delete=CASCADE`. 모델 필드도 CASCADE 필수로 변경.
- migration 테스트는 MigrationExecutor로 0006 상태에 레거시 행을 만들고 0007
  적용 후 삭제·필드 계약을 검증하며, teardown에서 leaf로 복원한다.

### Cache invalidation (Task 6~9)

- `apps/stats/use_cases.py`: 사용자별 무작위 generation token
  (`stats-generation:<user id>`, `secrets.token_urlsafe(12)`, `incr()` 미사용).
  cache key는 `stats:<user>:<token>:<date>:<lang>:v3`. 날짜별 삭제 함수
  `invalidate_stats_cache`는 제거했고 receiver는 세대 회전만 한다.
- 신규 signal: `apps/tags/signals.py`(`tags_changed`),
  `apps/users/signals.py`(`goals_changed`, `notes_changed`). payload는
  `user_id`만. 소유 앱은 stats를 import하지 않는다(stats -> 소유 앱 방향 유지).
- 대시보드 Upsert/Restore/Delete use case의 `time_blocks_changed` 발행을
  `transaction.on_commit()`으로 이동(값은 lambda 기본 인자로 캡처).
- tags Create/Update/Delete, users SaveGoal/DeleteGoal/SaveNote/DeleteNote가
  atomic 경계에서 `on_commit`으로 발행. Delete 발행은 계획서 Task 8 Step 3
  지시(미발행 시 기록 삭제 후 stale 캐시 결함이 남는다).
- `apps/stats/test_receivers.py`를 DummyCache에서 LocMemCache 기반 세대 회전
  관찰로 교체(구 테스트는 DummyCache라 항상 통과하던 무효 검증이었다).
- `apps/stats/test_cache_invalidation.py` 신설 — 모듈 로컬 LocMemCache
  fixture만 사용, 전역 DummyCache fixture는 유지.

### 기존 테스트 변경 (Scenario 매핑)

- `apps/stats/tests.py` 빌더 exact-equality 4건에 `key`/`tag_id` 필드 추가
  (STAT-ID-01~04의 계약 확장).
- `apps/tags/test_tag_migration.py`의 결함 고정 테스트 1건을 TAG-DEL-01로 교체.
- `apps/stats/test_receivers.py` 재작성(CACHE-SLOT-01 receiver 계약).

## 비가역 migration 경고 (AC-TAG-2)

`dashboard.0007`의 tagless 행 삭제는 **비가역**이다.

- reverse는 `RunPython.noop` — 코드 rollback으로 데이터가 돌아오지 않는다.
- **rollback 수단은 배포 전 DB backup 복원뿐이다.**
- production 적용 전 필수: ① 현재 backup 시각·복원 경로 기록,
  ② `tag_id IS NULL` 행 수 read-only 확인, ③ 행 수가 유의미하면 대표 사본에서
  소요 시간 측정.
- 이 세션에서는 **production/dev DB에 migration을 적용하지 않았다**
  (pytest의 테스트 DB에서만 MigrationExecutor로 검증). Deployment hold 유지.

## Lane C — 계정 수명주기 (2026-08-16, Task 12~15)

| Scenario | Red (예상 이유) | Green 증거 |
|---|---|---|
| ACC-REQ-01 | `UNIQUE constraint failed: users_accountdeletionrequest.user_id` | `apps/users/test_account_deletion.py` 15 passed |
| ACC-LOCAL-01 | seed 예외 후 User 잔존 | `test_signup_consent.py` + seed 성공 가드 5 passed |
| ACC-SOC-CONFIG-01 | `SOCIALACCOUNT_AUTO_SIGNUP is True` | settings 모듈 5 passed |
| ACC-SOC-01 | `ImportError: SocialSignupForm` | social+local consent 5 passed |
| ACC-SOC-02 | User/SocialAccount 저장, seed 0/11 | 모듈 2 passed |
| ACC-SOC-03 | — discovered Green (ACC-SOC-02의 atomic override) | 1 passed |
| ACC-SOC-CONFIG-02 | `AttributeError: SOCIALACCOUNT_ADAPTER` | settings 6 passed |
| ACC-SOC-04 | — discovered Green (adapter hook이 CONFIG-02와 한 변경) | 2 passed |
| ACC-SOC-05 | — discovered Green (계획서 예상: cancel이 기한 거부) | 수명주기 4모듈 30 passed |
| ACC-OPS-01 | — Deferred → 공급자 승인됨(GitHub Actions, 2026-08-16). secrets 등록·첫 예약 실행 관찰 전까지 운영 완료 미주장 | workflow 파일·--check 준비 완료 |
| ACC-OPS-02 | `--check` 옵션 부재 TypeError | targeted 1 passed, 모듈 17 passed |
| ACC-OPS-03 | — discovered Green (OPS-02 최소 구현의 0 분기) | 1 passed |

구현 요약:

- `request_account_deletion()`: `select_for_update()`로 사용자 행을 잠근 뒤
  취소된 행이면 requested/scheduled/cancelled/purged 4개 필드를 새 요청
  상태로 재설정. 활성 요청 idempotency와 purge cascade·masked audit 계약은
  기존 테스트로 유지.
- `signup_view`: form.save + create_seed_tags를 하나의
  `transaction.atomic()`으로. 실패 시 사용자도 rollback.
- `apps/users/forms.py`: 동의 라벨·오류를 공유 상수로 추출,
  `SocialSignupForm`(allauth SignupForm 서브클래스, 같은 동의 필드,
  atomic `save(request)`에서 seed 생성).
- `lifeDiary/settings/dev.py`(prod가 상속): `SOCIALACCOUNT_AUTO_SIGNUP=False`,
  `SOCIALACCOUNT_FORMS`, `SOCIALACCOUNT_ADAPTER` 등록.
- `apps/users/adapters.py`: `pre_social_login`에서 `is_existing`이고
  비활성인 연결 계정만 `cancel_account_deletion()` — 기한 판정은 기존
  서비스가 소유, email 기반 재활성화 없음.
- `templates/socialaccount/signup.html`: 프로젝트 동의 화면(provider 문맥,
  약관·개인정보 링크, CSRF, 돌아가기). `apps/users/templates/`에 두면
  INSTALLED_APPS 순서로 allauth 기본 템플릿이 이기므로 프로젝트
  `templates/`에 배치. 신규 문자열 1건 ko/en `django.po` 등재.
- FE-SOC-01 브라우저 증거는
  `docs/frontend/2026-08-15-dashboard-security-interaction.md` 참조.

### Scheduler (Task 16 수정안, 사용자 승인 2026-08-16)

- 공급자: **GitHub Actions schedule** (무료; Render Cron은 유료라 제외).
- `.github/workflows/purge-deleted-accounts.yml`(저장소 루트): 매일 UTC
  18:47(KST 03:47), `workflow_dispatch` 수동 복구, concurrency로 중복 방지,
  production 브랜치 체크아웃, purge 후 `--check`로 잔량 0 확인(잔량 시
  실패 → GitHub 실패 알림).
- `purge_deleted_accounts --check`: `count_overdue_deletion_requests()`
  (기한 경과·미취소·미purge)를 보고, 잔량이 있으면 `CommandError`.
- secrets 최소권한: 진짜 값은 DB 4개뿐. `PURGE_DJANGO_SECRET_KEY`는 웹
  키와 다른 무작위 값, RESEND/FROM은 더미(메일 미발송).
- **사용자 남은 일**: GitHub 저장소 secrets 등록
  (`PURGE_DJANGO_SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
  `DB_HOST`), 워크플로가 main에 머지된 뒤 `workflow_dispatch` 1회
  dry-run으로 `Purged N` + `Overdue: 0` 확인. 그 전까지 ACC-OPS-01의
  운영 완료를 주장하지 않는다.

## Lane B 참조

Lane B(대시보드 DOM-XSS·삭제 상태·태그 선택)는 프런트 소유라
`docs/frontend/2026-08-15-dashboard-security-interaction.md`가 실행 로그다.
백엔드 파일 변경은 없고, `apps/dashboard/tests.py`의 JS 소스 문자열 검사
테스트 2건(중복 정의 1쌍)을 Frontend Work Policy에 따라 삭제했다
(protected behavior는 FE 브라우저 매트릭스가 대체).

## 최종 검증 (2026-08-15, Lane A 완료 시점)

- 전체 pytest: `518 passed in 320.32s (0:05:20)` (기준선 501 + 신규 17:
  identity 11, migration 1, cache invalidation 5; receiver·TAG-DEL 테스트는
  1:1 교체)
- `manage.py check`: `System check identified no issues (0 silenced).`
- `makemigrations --check --dry-run`: `No changes detected`
- `node --check` dashboard.js / stats.js: exit 0
- `msgfmt --check-format` ko/en × django/djangojs 4개 카탈로그: 통과
- `git diff --check`: 클린 (`apps/stats/use_cases.py` EOF 빈 줄 1건을 잡아
  수정 후 재확인)

## 최종 검증 갱신 (2026-08-16, Lane B·C 완료 시점)

- 집중 Lane 회귀(계획서 Task 17 Step 1 명령): `158 passed in 107.20s`
- 전체 pytest: `526 passed in 309.91s (0:05:09)`; scheduler 수정안
  (ACC-OPS-02/03) 반영 후 재실행 `528 passed in 308.99s (0:05:08)`
- `manage.py check`: 이슈 없음 / `makemigrations --check`: 드리프트 없음
- prod deploy check(`--settings=prod --deploy --fail-level ERROR`, 더미 env):
  `System check identified no issues (0 silenced).`
- `node --check` 2건, `msgfmt --check-format` 4건, `git diff --check` 클린

## Unverified

- production migration 적용과 production backup/행 수 확인(위 Deployment
  hold). 로컬 dev DB read-only 수치: `tag_id IS NULL` 163건 / 전체 1,227건
  (2026-08-16, dev DB에는 0007 미적용).
- 실제 Google OAuth 왕복(provider 자격증명 필요).
- ko/en `djangojs.po` 각 1건, en `django.po` 1건의 기존 미번역
  (HEAD에서 재현, 이번 변경 이전부터) — 후속 정리 대상.
- 운영 purge scheduler — 공급자 승인 전 `Deferred` 유지(ACC-OPS-01).

## 새로 발견한 Scenario (Test List 후보 — 이번 범위에서 수정하지 않음)

1. `daily.py`의 active_hours가 여전히 이름 비교
   (`tag_info["name"] != UNCLASSIFIED_TAG_NAME`)라 `미분류` 이름의 실제 태그가
   일간 active 시간에서 제외된다.
2. `logic.py`의 `delta_vs_week`가 태그명으로 매핑되어, 합성 미기록 entry와
   같은 이름의 실제 태그가 있으면 합성 entry에 그 delta가 붙을 수 있다.
3. `apps/stats/services.py`의 `UNCLASSIFIED_TAG_NAME` import는 이번 변경 전부터
   미사용이었다(surgical 원칙에 따라 제거하지 않음).

## Deferred Refactoring Note

```text
- Topic: daily active 판정과 delta 매핑의 name 의존 제거
- Why it is not part of the current scope: STAT-ID-01~04와 STAT-WEEK-01의
  승인된 Then에 포함되지 않은 별도 관찰 결과다.
- Why it may be needed later: identity 분리 원칙과 일관되지 않는다.
- Trigger condition: 위 신규 Scenario를 Test List에 채택할 때.
- Expected change location: apps/stats/aggregation/daily.py, apps/stats/logic.py,
  apps/stats/aggregation/daily_baseline.py
- Related tests: apps/stats/aggregation/test_tag_identity.py
```
