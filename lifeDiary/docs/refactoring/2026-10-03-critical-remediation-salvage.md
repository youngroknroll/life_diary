# Critical Remediation 미반영 커밋 선별 재적용 실행 로그 (2026-10-04)

- 계획: `docs/plans/2026-10-03-critical-remediation-salvage-plan.md`
- 원본 설계·계획·로그(이번에 복원): `docs/plans/2026-08-15_critical-remediation-design.md`, `docs/plans/2026-08-15_critical-remediation-plan.md`, `docs/refactoring/2026-08-15_critical-backend-remediation.md`, `docs/frontend/2026-08-15-dashboard-security-interaction.md`
- 브랜치: `fix/critical-remediation-salvage`
- 범위: 1~3단계(PR #83, 2026-10-04 머지). 4a(마이그레이션 0007)는 사용자 승인 뒤 브랜치 `fix/require-timeblock-tag`에서 진행했다(아래 "4a"). 4b(purge 스케줄)는 결정 대기다.

복원한 원본 문서 4개는 2026-08-15~16 시점 기록이다. 거기 적힌 identity key 전환, DOM 노드 조립, 마이그레이션 0007, purge 스케줄은 `main`에 없다.

## 한 일

| 단계 | 내용 | 방식 |
|---|---|---|
| 1 | 옮길 곳 없는 태그 삭제가 기록·메모를 지움, 탈퇴 취소 뒤 재요청, `purge_deleted_accounts --check` | 원본 커밋 `4ba9921`, `aaf46b0`, `1f908be`를 `cherry-pick -x` |
| 2a | 로컬 가입의 사용자 저장과 기본 태그 생성을 한 트랜잭션으로 | 재구현 |
| 2b | Google 가입자 기본 태그, 가입 롤백, 유예기간 내 Google 로그인의 탈퇴 취소 | 재구현 |
| 2c | 통계 캐시 세대 토큰(키 `:v3`), 기록·태그·목표·메모 변경이 커밋된 뒤 세대 교체 | 재구현 |
| 2d | 주간 활동 시간의 수면 제외를 카테고리로 판정 | 재구현 |
| 3 | 기록 삭제 성공 뒤 "삭제 실패"로 되돌아가는 버그 | 재구현 |
| 추가 | 태그 삭제 API가 깨진 본문을 400으로 거절 | 보안 검토 지적 반영 |
| 추가 | Google 가입 이메일을 제공자 주소로 고정, 인증 표시는 제공자가 인증한 주소일 때만 | 사용자 지시(2026-10-04), 보안 검토에서 발견한 기존 결함 |

## 계획에서 달라진 점

- 3단계: 삭제 때 `time-blocks-saved`를 보내지 않는다. 계획은 이벤트에 `filledSlots`를 싣는 것이었다. 유일한 수신자인 온보딩(`onboarding.js:63`)이 이 이벤트를 "저장됨"으로 받아 3단계로 넘어가기 때문에, 두 프런트 검토자가 사전 검토에서 같은 문제를 지적했다.
- 3단계: 삭제 경로에서 스냅샷 복원을 뺐다. 삭제는 화면을 먼저 바꾸지 않으므로 복원할 것이 없다.
- 3단계: 요청 중 두 번째 삭제 요청을 막는 가드와, 서버 삭제 뒤 화면 갱신이 실패했을 때의 안내 문구 1개(ko/en)를 더했다.
- 추가: 1단계로 옮길 곳 없는 태그 삭제가 기록을 실제로 지우게 됐다. 그 결과 `apps/tags/api.py`의 `_parse_move_to`가 깨진 JSON 본문을 "옮길 곳 없음"으로 읽는 동작이 데이터 삭제로 이어진다. Security & Resilience Reviewer가 중간 등급으로 지적했고, 깨진 본문과 객체가 아닌 JSON을 400으로 거절하게 했다.

## TDD 증거

| ID | Red | Green |
|---|---|---|
| SV-01 | 구현을 되돌리면 `IntegrityError: UNIQUE constraint failed: users_accountdeletionrequest.user_id` | 통과 |
| SV-02 | 구현을 되돌리면 `test_deleting_a_used_tag_removes_its_time_blocks_and_memos` 실패 | 통과 |
| SV-03 | 구현을 되돌리면 `--check` 테스트 2개 실패 | 통과 |
| SV-04 | 기본 태그 생성 실패 뒤에도 사용자 행이 남음 | 통과 |
| SV-05 | Google 가입자의 태그 0개(기대 11개) | 통과 |
| SV-06 | 기본 태그 생성 실패 뒤에도 사용자 남음 | 통과 |
| SV-07 | 유예기간 내 로그인 뒤에도 `is_active` False | 통과 |
| SV-08 | 처음부터 통과(기한 판정은 `cancel_account_deletion` 소유). 어댑터가 무조건 재활성화하도록 잠시 바꿔 실패하는 것을 확인 | 통과 |
| SV-09 | 다른 날짜의 기록을 고친 뒤에도 `cache_hit` True | 통과 |
| SV-10 | 목표·메모·태그 변경 뒤에도 `cache_hit` True(각 1건) | 통과 |
| SV-11 | 롤백된 변경이 세대를 바꿔 `cache_hit` False | 통과 |
| SV-12 | 수면 카테고리의 "Sleep" 태그 3칸이 활동 시간에 들어가 `5 == 2` 실패 | 통과 |
| 추가 | 본문 `{bad`에 200과 삭제, 본문 `[1]`에 예외 | 400, 태그 유지 |
| 추가 | 조작한 주소 `victim@example.com`이 계정에 저장됨. 제공자가 인증하지 않은 주소도 인증 표시됨 | 제공자 주소로 저장, 미인증 주소는 인증 표시 없음 |

1단계(SV-01~03)는 옮긴 뒤 구현 파일만 되돌려 4개 실패(21개 통과)를 확인하고 복원했다.

## 검토

- Browser Interaction Reviewer, Web Experience Designer: 사전 검토 뒤 구현, 사후 정적 추적에서 위반 없음. 브라우저 확인은 아래 참조.
- Domain Architecture Reviewer: 지적 사항과 함께 승인. `tags`·`users`의 유스케이스와 신호 모듈은 `stats`를 import하지 않는다. 모든 알림이 `transaction.atomic` 안에서 `on_commit`으로 예약된다.
- Security & Resilience Reviewer: 머지를 막는 결함 없음. 중간 등급 1건은 위 "추가"로 반영했다. 기존 결함으로 보고한 Google 가입 이메일 조작도 고쳤고, 재검토에서 allauth 65.17.0 소스를 읽어 제출된 이메일이 `user.email`과 `EmailAddress` 어디에도 들어가지 않음을 확인했다.

## 검증 (2026-10-04, 통합 브랜치)

- 전체 회귀: `691 passed in 531.41s`. 기준선은 `main` 671.
- `manage.py check`: 이슈 0건. 마이그레이션 drift 없음. prod deploy check exit 0.
- `node --check dashboard.js` 통과. ko/en `djangojs.po` `msgfmt --check-format` 통과.
- 브라우저(Chrome, 임시 SQLite DB로 띄운 로컬 서버, 데스크톱 폭):
  - 요청 실패: "삭제 실패: Failed to fetch" 알림, 기록 4칸 그대로, 선택 유지, 되돌리기 알림 없음.
  - 성공 + 연속 2회 호출: DELETE 요청 1건, 기록 2칸 삭제, 되돌리기 알림만 표시, 포커스가 그리드 칸으로 복귀.
  - 삭제 뒤 화면 갱신 실패(`renderDayStats`가 던지게 함): 경고 알림 "삭제되었지만 화면을 새로고침하지 못했습니다. 페이지를 새로고침해주세요.", "삭제 실패" 없음.
  - 세 경우 모두 `time-blocks-saved` 0건, 콘솔 오류 0건.

## 미검증

- 실제 Google OAuth 왕복. 어댑터와 폼은 allauth 객체를 직접 써서 테스트했다.
- 모바일 폭의 바텀시트 닫힘과 스크롤 잠금 해제, 스크린리더 낭독, 영어 로케일의 새 문구 표시, 온보딩 2단계에서의 삭제, pywebview.
- 운영의 실제 캐시 적중률. 요청 한 건의 비용과 무효화 동작은 아래 "캐시 세대 교체 운영 측정"에서 확인했다.

## 4a — 태그 없는 기록 삭제와 태그 필수 (2026-10-04)

- 원본 커밋 `4978886`을 `cherry-pick -x`로 옮겼다. 마이그레이션 `dashboard/0007`이 `tag_id IS NULL` 행을 지우고 `TimeBlock.tag`를 필수 FK(`CASCADE`)로 바꾼다.
- 운영 DB 확인(사용자, Supabase SQL Editor): 태그 없는 행 190건. 사용자 3번 108건(전부 메모 있음), 1번 82건(메모 5건), 모두 2026-04-12 하루다. 태그 삭제의 잔재라는 전제와 맞지 않아 원인은 확인하지 못했다. 사용자가 삭제해도 된다고 판단했고 190건을 CSV로 받아 두었다.
- 되돌리기는 코드가 아니라 그 CSV(또는 덤프) 복원이다.
- 옮긴 직후 전체 회귀는 `641 passed, 51 errors`였다. 오류는 모두 `apps/stats/aggregation/test_stats_window.py`의 공통 fixture가 태그 없는 기록을 만들어서 났다(2단계 때 추가된 테스트라 원본 커밋이 몰랐다). fixture의 그 한 행에 태그를 주고, `test_monthly_daily_counts_include_untagged_blocks_like_the_database_count`를 `test_monthly_daily_counts_match_the_database_count`로 이름만 바꿨다. 삭제한 테스트는 없다. `apps/dashboard/conftest.py`의 `time_block_factory`는 `tag`를 필수 인자로 바꿨다.
- 검증: 전체 회귀 `692 passed in 515.31s`(테스트 정리 커밋 시점, 서브에이전트 워크트리). 통합 브랜치에서 `test_stats_window.py`, `test_required_tag_migration.py`, `test_tag_migration.py` 60 passed, 마이그레이션 drift 없음, prod deploy check exit 0.
- 미검증: 운영 DB에서의 마이그레이션 실행(배포 때 실행된다).
- Deferred: 태그가 필수가 되어 도달하지 않는 가드 정리. `daily_baseline.py:26`, `summary.py:107`, `calculator.py:79-89`(`process_blocks_without_tag`와 호출처 4곳), `comparison.py:94`, `export.py:91`(`category_id` 부분은 별개일 수 있음), `dashboard/repositories.py:112`.

## 4b — purge 스케줄 (2026-10-06)

- 원본 커밋 `2317031`을 `cherry-pick -x`로 옮겼다. `.github/workflows/purge-deleted-accounts.yml`이 매일 UTC 18:47(KST 03:47)에 `production` 브랜치를 체크아웃해 `purge_deleted_accounts`와 `purge_deleted_accounts --check`를 실행한다. 수동 실행(`workflow_dispatch`)도 된다.
- 사용자가 저장소 시크릿 5개를 등록했다: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `PURGE_DJANGO_SECRET_KEY`. `gh secret list`로 이름을 확인했다.
- 워크플로가 넘기는 환경변수는 현재 `lifeDiary/settings/prod.py`가 읽는 이름과 맞는다. `RESEND_API_KEY`는 더 이상 읽지 않지만 남겨도 영향이 없다.
- 검증: YAML 파싱, `production`의 명령에 `--check`가 있음을 확인했다.
- 미검증: 실제 실행. 머지 뒤 Actions에서 수동으로 한 번 돌려 확인한다.
- 주의: 첫 실행에서 그동안 쌓인 기한 지난 탈퇴 요청이 한꺼번에 영구 삭제된다. GitHub는 저장소에 60일간 활동이 없으면 예약 워크플로를 끈다.

## 캐시 세대 교체 운영 측정 (2026-10-06, 데스크톱 Chrome)

PR #83·#85 배포 뒤, 사용자가 로그인한 운영 페이지에서 `fetch`와 ResourceTiming으로 쟀다. 이전 측정은 페이지 이동으로 쟀다.

| 날짜 | 캐시 | TTFB | ctx | db | 쿼리 |
|---|---|---|---|---|---|
| 06-01 | miss | 1,440 | 394.5 | 382.3 | 5 |
| 06-02 | miss | 969 | 419.9 | 403.9 | 5 |
| 06-03 | miss | 983 | 380.0 | 366.0 | 5 |
| 06-04 | miss | 954 | 380.1 | 366.9 | 5 |
| 06-05 | miss | 964 | 396.6 | 377.2 | 5 |
| 06-01, 06-03, 06-05 재요청 | hit | 475, 488, 485 | 0.4~1.3 | 0 | 0 |

- 미스 TTFB 중앙값 969ms, db 377ms, 쿼리 5개. 적중 TTFB 중앙값 485ms. 2026-10-02는 미스 1,144ms, db 569ms, 적중 446ms였다.
- 쿼리 수는 그대로다. 세대 토큰은 캐시에서만 읽는다.
- db 시간이 줄어든 원인은 확인하지 못했다. 쿼리 수가 같고 날짜(6월 vs 7월)와 측정 방식이 달라, 이번 변경의 효과로 볼 수 없다. 이 계정은 6월에 기록이 없다.

무효화 확인:

1. 06-03과 06-05가 적중인 상태에서(TTFB 463ms, 468ms), 10-04의 메모 없는 칸 하나(슬롯 0)를 같은 태그와 빈 메모로 다시 저장했다. 응답 201, `updated_count` 1.
2. 저장 전후 10-04의 블록 16개(시작 칸, 길이, 태그, 표시 문구)가 같았다.
3. 직후 06-03과 06-05가 모두 `miss`, 쿼리 5개로 바뀌었다(TTFB 820ms, 813ms). 06-03을 다시 열면 `hit`(448ms)였다.

운영의 FileBasedCache에서 다른 날짜의 변경이 그 사용자의 모든 날짜 캐시를 무효화하고, 세대 토큰이 요청 사이에 유지됨을 확인했다. 목표·메모·태그 변경에 의한 무효화는 운영에서 따로 확인하지 않았다(같은 수신기 경로이고 테스트 SV-10이 덮는다).

실제 적중률(전체 요청 중 적중 비율)은 서버가 요청별 적중 여부를 기록하지 않아 재지 못했다. 측정에 쓴 날짜는 05-20, 06-01~05다.

## Deferred

- Google이 미인증이라고 알려 준 주소로도 가입과 로그인은 된다(인증 표시만 빠진다). 그 주소의 실제 주인은 "이미 사용 중"에 막힌다. 트리거: 보안 트랙. 완화안은 `clean_email`에서 거절하거나 6자리 코드 인증을 거치게 하는 것.
- Google이 이메일을 주지 않으면 제출된 값이 그대로 쓰인다(인증 표시는 안 된다). 가입 화면은 재표시 때 제출된 값을 보여 준다(표시만, 저장에는 안 쓰임).
- 캐시 쓰기 실패 시 커밋된 변경이 500으로 응답될 수 있다(`on_commit` 수신기). 트리거: 캐시 백엔드 장애 대응을 다룰 때.
- Django 관리자 화면에서 태그·기록을 직접 고치면 세대가 교체되지 않는다(과거 날짜 최대 24시간).
- purge 때 그 사용자의 캐시된 통계와 세대 키가 남는다.
- 탈퇴 최초 요청이 동시에 두 번 오면 두 번째가 500이다. 상태는 일관된다.
- 삭제 버튼에 요청 중 표시가 없다. 화면 갱신 실패 뒤 선택이 남아 두 번째 삭제 요청이 가능하다(404 알림).
- `TimeBlockRepository.delete_blocks_for_tag`, `move_blocks_to_tag`에 사용자 필터가 없다. 지금은 저장 경로가 소유자 태그만 받아 안전하다.
- `apps/users/views.py`가 `apps.stats.aggregation.goal_progress`를 import한다(기존).
- `apps/core/utils.py`의 `SLEEP_TAG_NAME`은 이제 쓰는 곳이 없다.
- 통계 identity key 전환, 대시보드 정보 패널의 DOM 노드 조립(계획 Deferred와 같음).
- 구현 중 발견했지만 테스트하지 않은 시나리오: 목표·메모 삭제와 태그 생성·삭제 뒤의 세대 교체, Restore·Delete 기록 유스케이스의 교체, 연결되지 않은 Google 계정이 비활성 계정을 되살리지 못한다는 것.
- 살리기가 머지되면 로컬 브랜치 `feat/grid-label-and-hour-axis`를 지운다.
