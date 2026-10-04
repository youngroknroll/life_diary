# Critical Remediation 미반영 커밋 선별 재적용 계획 (2026-10-03)

- 원본 커밋: 로컬 브랜치 `feat/grid-label-and-hour-axis`의 `cd01609`..`328e025` (13개, 2026-08-15~16)
- 원본 설계·계획·로그(그 브랜치에만 있음): `docs/plans/2026-08-15_critical-remediation-design.md`, `docs/plans/2026-08-15_critical-remediation-plan.md`, `docs/refactoring/2026-08-15_critical-backend-remediation.md`, `docs/frontend/2026-08-15-dashboard-security-interaction.md`
- 브랜치: `fix/critical-remediation-salvage`
- 상태: 1~3단계 사용자 승인(2026-10-04), 구현 완료. 4a·4b는 결정 대기
- 실행 로그: `docs/refactoring/2026-10-03-critical-remediation-salvage.md`

## 배경

2026-08-15에 사용자가 승인한 Critical Remediation Lane A·B·C가 구현·커밋됐지만 push되지 않았다. 커밋 13개는 PR #49 머지 뒤 같은 로컬 브랜치에 쌓였고, 원격과 `main` 어디에도 없다. 그 뒤 `main`은 139커밋 앞서 갔다(P0 v2, 목표 관리 통합, 이메일 코드 인증, 통계 쿼리 통합 1·2단계). 브랜치를 통째로 머지하면 16건이 충돌한다.

2026-10-03에 사용자가 "커밋을 검토하고 현재 서비스에 필요한 것은 살린다"고 지시했다. 이 문서는 그 검토 결과와 재적용 범위다.

## 검토 결과

각 커밋이 고치는 문제가 현재 `main`에 남아 있는지 코드로 확인했다. "적용"은 커밋 하나를 현재 `main`에 올렸을 때의 충돌 여부다(`git merge-tree`).

| 커밋 | 내용 | 현재 `main` 상태 | 적용 | 판정 |
|---|---|---|---|---|
| `aaf46b0` | 탈퇴 취소 뒤 재요청 | **버그 재현.** 재요청 시 `IntegrityError`(`AccountDeletionRequest.user` OneToOne 중복). 뷰(`views.py:968`)에 예외 처리 없음 | 충돌 없음 | 살림 |
| `4ba9921` | 옮길 곳 없는 태그 삭제가 기록·메모도 지움 | **문구와 동작 불일치.** 버튼은 "기록까지 함께 삭제"(`tags/index.html:68`)인데 `SET_NULL`이라 행과 메모가 DB에 남는다 | 충돌 없음 | 살림 |
| `1f908be` | `purge_deleted_accounts --check` | 없음. 기한 지난 요청이 남았는지 확인할 수단이 없다 | 충돌 없음 | 살림 |
| `b9e9fd3` | 가입의 사용자 저장과 기본 태그 생성을 한 트랜잭션으로 | 미반영(`views.py:223-224`). 태그 생성이 실패하면 태그 없는 계정이 남는다 | 1건 충돌(2줄) | 살림(재적용) |
| `9879021` | 통계 캐시 세대 교체 | **미반영.** 기록을 고친 날짜의 캐시만 지운다. 그 날짜를 주·월 범위에 포함하는 다른 날짜의 캐시, 목표·태그·메모 변경은 무효화하지 않는다. 과거 날짜는 최대 24시간, 오늘은 최대 5분 동안 옛 값이 보인다 | 1건 충돌 | 살림(재적용) |
| `65e1897` | Google 가입 계약 | 동의 폼은 `main`에 이미 있다(`social_forms.py`). **빠진 것 2가지:** Google 가입자는 기본 태그를 받지 못한다(`create_seed_tags` 호출은 로컬 가입뿐). Google 로그인은 유예기간 안의 탈퇴 요청을 취소하지 못한다(어댑터 없음) | 6건 충돌 | 빠진 2가지만 재구현 |
| `cd01609` | 통계 태그 identity, 수면 제외 판정 | **수면 판정 문제 남음.** 주간 활동 시간이 이름이 "수면"인 태그만 뺀다(`weekly.py:25`). 영어 가입자의 기본 태그는 "Sleep"이고 "낮잠"도 수면 카테고리라 활동 시간에 들어간다. identity 충돌은 사용자가 "미분류"라는 태그를 만든 경우에만 생긴다(태그명은 사용자별 유일) | 4건 충돌 | 수면 판정만 재구현 |
| `56f6200` | 대시보드 DOM 주입 차단, 삭제 상태 | DOM 주입은 `main`이 `escapeHtml`로 이미 막는다. **삭제 버그 남음.** `deleteSlot`이 선언되지 않은 `slotIndexes`를 읽어(`dashboard.js:923`) 서버 삭제 성공 뒤 `ReferenceError`가 나고, 지운 행을 화면에 되살린 뒤 "삭제 실패"를 띄운다. 함수 원본을 node에서 실행해 재현했다(브라우저 미확인). 2026-08-12 PR #41부터 있었다 | 3건 충돌 | 삭제 버그만 재구현 |
| `4978886` | 태그 없는 기록 삭제 + 태그 필수(마이그레이션 0007) | `tag`는 `null=True, SET_NULL`. 저장 경로는 이미 태그를 요구하므로 태그 없는 행은 과거 태그 삭제가 남긴 것뿐이다 | 충돌 없음 | 살림(운영 게이트) |
| `2317031` | purge GitHub Actions 스케줄 | 자동 purge 없음(백로그 A-5). 15일 뒤 영구 삭제가 수동 실행에 달려 있다 | 충돌 없음 | 살림(운영 게이트) |
| `97a4843`, `53ddc12`, `328e025` | 문서 | `project-status.md` 변경은 현재 문서와 충돌한다 | 충돌 | 원본 문서 4개만 복원 |

## 범위

### 1단계 — 충돌 없는 백엔드 커밋 재적용

`4ba9921`, `aaf46b0`, `1f908be`를 `cherry-pick -x`로 옮긴다. 커밋마다 구현을 잠시 되돌려 테스트가 실패하는지 확인한다(Red-Green 재검증).

### 2단계 — 백엔드 재구현 (Backend TDD)

- 2a. 가입 트랜잭션: `signup_view`의 `form.save()`와 `create_seed_tags()`를 `transaction.atomic()`으로 묶는다.
- 2b. Google 가입 계약: `SocialSignupForm.save()`가 같은 트랜잭션에서 기본 태그를 만든다. `SOCIALACCOUNT_ADAPTER`의 `pre_social_login`이 이미 연결된 비활성 계정의 유효한 탈퇴 요청을 취소한다. 기한이 지난 요청은 취소하지 않는다.
- 2c. 통계 캐시 세대: 사용자별 무작위 세대 토큰을 캐시 키에 넣는다. 기록·태그·목표·메모 변경은 `transaction.on_commit`에서 신호를 보내고, stats 수신기가 세대를 교체한다. 키 버전은 `:v3`로 올린다. `StatsContextResult`(cache_hit)와 Server-Timing은 그대로 둔다.
- 2d. 수면 제외 판정: 주간 활동 시간에서 태그명이 아니라 `category_key == "sleep"`으로 뺀다.

### 3단계 — 프런트엔드 (Frontend Work Policy)

`deleteSlot`의 성공 뒤 경로를 고친다. HTTP 실패일 때만 "삭제 실패"를 띄운다. 서버가 삭제를 확정한 뒤의 화면 갱신 오류는 실패로 알리지 않는다.

2026-10-04 사전 검토 반영: 삭제 때는 `time-blocks-saved`를 보내지 않는다. 온보딩이 이 이벤트를 저장으로 받아 다음 단계로 넘어가기 때문이다. 삭제 경로의 스냅샷 복원도 뺀다.

### 4단계 — 운영 게이트가 있는 항목 (PR 분리)

- 4a. `4978886` 마이그레이션 0007. 되돌릴 수 없는 데이터 삭제다. 배포 전에 운영 DB 백업과 `tag_id IS NULL` 행 수 확인이 필요하다.
- 4b. `2317031` purge 스케줄. GitHub 저장소 시크릿(`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `PURGE_DJANGO_SECRET_KEY`) 등록이 먼저다. 2026-10-03 `gh secret list` 결과는 비어 있다. 시크릿 없이 머지하면 매일 실패한다.

### 문서

원본 설계·계획·로그 4개를 그대로 복원하고, 이 계획과 실행 로그에서 참조한다.

### 명시적 제외

- 브랜치 통째 머지.
- `56f6200`의 `innerHTML` → DOM 노드 조립 전환, `title` 재파싱 제거, 전역 `event` 제거. `main`은 이스케이프로 주입을 막고 있다.
- `cd01609`의 identity key 전환(`tag:<id>`, `unclassified`). 통계 집계가 그 뒤 두 번 다시 쓰였다.
- `65e1897`의 동의 폼, `forms.py` 정리, `signup.html`, 설정 변경. `main`에 다른 구현이 있다.
- 데스크톱 설정 check 실패, 죽은 CSS, 그 밖의 백로그.

## 인수 기준

1. 탈퇴를 취소한 뒤 다시 요청하면 같은 요청 행이 새 15일 기한으로 갱신되고 예외가 없다.
2. 옮길 곳 없이 태그를 지우면 그 태그의 기록과 메모가 0건이고, 다른 태그의 기록은 그대로다.
3. `purge_deleted_accounts --check`는 기한 지난 미처리 요청이 있으면 0이 아닌 코드로 끝난다.
4. 가입 중 기본 태그 생성이 실패하면 사용자도 남지 않는다.
5. Google로 가입한 사용자도 로컬 가입과 같은 기본 태그를 받는다.
6. 연결된 Google 계정으로 유예기간 안에 로그인하면 탈퇴가 취소된다. 기한이 지났으면 비활성으로 남는다.
7. 커밋된 기록·태그·목표·메모 변경은 날짜와 관계없이 그 사용자의 다음 통계 요청에 반영된다. 롤백된 변경은 캐시를 무효화하지 않는다.
8. 수면 카테고리 태그는 이름과 관계없이 주간 활동 시간에서 빠진다.
9. 기록 삭제가 성공하면 화면이 삭제 상태로 남고 "삭제 실패"가 뜨지 않는다. HTTP 실패일 때만 행이 복원된다.
10. 0007 적용 뒤 `tag` 없는 기록이 0건이고 FK가 필수다(4a).
11. purge 워크플로를 수동으로 한 번 실행해 성공한다(4b).
12. 전체 회귀, `manage.py check`, 마이그레이션 drift, prod deploy check가 통과한다.

## Activated Roles

- Backend TDD Coach — 2단계 Test List를 하나씩 Red/Green으로 이끈다. 1단계의 Red-Green 재검증을 판정한다.
- Backend & Integration Engineer — 1·2·4단계 구현과 문서.
- Domain Architecture Reviewer — 2c의 신호 방향(`tags`, `users` → `stats` 구독)과 트랜잭션 경계.
- Security & Resilience Reviewer — 탈퇴 재요청, Google 로그인 재활성화 조건, purge 시크릿 최소권한.
- Deployment & Operations Reviewer — 4a 비가역 마이그레이션과 4b 스케줄러.
- Web Experience Designer, Browser Interaction Reviewer — 3단계 사전 검토와 사후 판정.
- Frontend Implementation Engineer — 3단계 구현.
- Quality Verification Lead — 인수 기준과 증거 대응.

## Not Activated

- Product Scope Owner — 범위와 동작 의미("기록까지 함께 삭제", 수면 카테고리 판정)는 2026-08-15 설계에서 승인됐다. 이번에는 새 제품 결정이 없다.
- AI Automation Architect — AI 동작이 없다.

## Domain Boundary and Dependency Direction

- `tags`와 `users`는 자기 변경 신호만 보낸다. `stats`가 구독한다. `stats`를 import하지 않는다.
- 기록 삭제는 `tags` 유스케이스가 `dashboard` 저장소를 통해 한다(기존 `move_blocks_to_tag`와 같은 방향).
- Google 어댑터는 `users` 안에서 `account_deletion` 서비스만 호출한다.

## Coupling and Cohesion Review

- 새 결합은 신호 3개(`tags_changed`, `goals_changed`, `notes_changed`)뿐이고 방향은 기존 `time_blocks_changed`와 같다.
- 세대 토큰 함수는 캐시 키를 소유한 `apps/stats/use_cases.py`에 둔다.

## Pythonic Code Design

- 세대 토큰은 `secrets.token_urlsafe`로 만든다. FileBasedCache의 비원자적 `incr()`를 쓰지 않는다.
- `on_commit` 콜백은 값을 기본 인자로 묶는다.
- 새 클래스·서비스 계층을 만들지 않는다.

## Test List and TDD checkpoints

1단계는 원본 커밋의 테스트를 그대로 가져오고 Red-Green으로 다시 확인한다.

| ID | 동작 | 경계 | 출처 |
|---|---|---|---|
| SV-01 | 취소 뒤 재요청은 같은 행을 새 15일로 갱신한다 | 서비스 | `aaf46b0` |
| SV-02 | 옮길 곳 없는 태그 삭제는 기록과 메모를 지운다 | 유스케이스 | `4ba9921` |
| SV-03 | `--check`는 기한 지난 요청이 있으면 실패한다 | 명령 | `1f908be` |
| SV-04 | 기본 태그 생성이 실패하면 가입한 사용자도 롤백된다 | 뷰 | `b9e9fd3` |
| SV-05 | Google 가입은 기본 태그를 만든다 | 폼 | `65e1897` |
| SV-06 | Google 가입의 태그 생성이 실패하면 사용자도 롤백된다 | 폼 | `65e1897` |
| SV-07 | 연결된 계정의 유예기간 내 Google 로그인은 탈퇴를 취소한다 | 어댑터 | `65e1897` |
| SV-08 | 기한이 지난 계정의 Google 로그인은 비활성으로 남는다 | 어댑터 | `65e1897` |
| SV-09 | 다른 날짜의 기록 변경이 캐시된 통계에 반영된다 | 유스케이스 | `9879021` |
| SV-10 | 목표·메모·태그 변경이 캐시된 통계에 반영된다 | 유스케이스 | `9879021` |
| SV-11 | 롤백된 변경은 세대를 바꾸지 않는다 | 유스케이스 | `9879021` |
| SV-12 | 수면 카테고리 태그는 이름과 관계없이 주간 활동 시간에서 빠진다 | 집계 | `cd01609` |

구현 중 발견한 시나리오는 이 표에 추가한다.

## 파일과 단계

| 단계 | 파일 |
|---|---|
| 1 | `apps/tags/use_cases.py`, `apps/dashboard/repositories.py`, `apps/tags/test_tag_migration.py`, `apps/users/account_deletion.py`, `apps/users/test_account_deletion.py`, `apps/users/management/commands/purge_deleted_accounts.py` |
| 2a | `apps/users/views.py`, `apps/users/test_signup_consent.py` |
| 2b | `apps/users/social_forms.py`, `apps/users/adapters.py`(신규), `lifeDiary/settings/dev.py`, `apps/users/test_social_signup.py` |
| 2c | `apps/stats/use_cases.py`, `apps/stats/receivers.py`, `apps/tags/signals.py`(신규), `apps/users/signals.py`(신규), `apps/tags/use_cases.py`, `apps/users/use_cases.py`, `apps/dashboard/use_cases.py`, 관련 테스트 |
| 2d | `apps/stats/aggregation/weekly.py`, `apps/stats/aggregation/test_weekly.py` |
| 3 | `apps/dashboard/static/dashboard/js/dashboard.js`, 필요하면 `locale/*/djangojs.po` |
| 4a | `apps/dashboard/migrations/0007_*.py`, `apps/dashboard/models.py`, `apps/dashboard/test_required_tag_migration.py` |
| 4b | `.github/workflows/purge-deleted-accounts.yml` |
| 문서 | 원본 문서 4개, `docs/refactoring/2026-10-03-critical-remediation-salvage.md`, `docs/project-status.md` |

PR은 셋으로 나눈다. PR A는 1~3단계, PR B는 4a, PR C는 4b다. 머지는 사용자가 한다.

2c는 캐시 적중률을 낮춘다. 지금은 기록을 고친 날짜만 미스가 되지만, 적용 뒤에는 변경이 있을 때마다 그 사용자의 모든 날짜가 다음 요청에서 미스가 된다. 2026-10-02 운영 측정은 미스 1,144ms, 적중 446ms다.

## 검증 명령과 기대 증거

```bash
conda run -n knou-life-diary pytest <대상 테스트> --tb=short
conda run -n knou-life-diary pytest
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
node --check apps/dashboard/static/dashboard/js/dashboard.js
```

- 기준선(2026-10-03 `main`): 671 passed, check 이슈 0건, 마이그레이션 변경 없음, prod deploy check exit 0.
- 3단계는 브라우저에서 확인한다. 기록 삭제 뒤 화면 상태와 알림, 네트워크 차단 시 복원.
- 2b의 실제 Google OAuth 왕복은 로컬에서 확인할 수 없다. 미검증으로 보고한다.

## 사용자 결정 필요

1. 1~3단계 범위 승인.
2. 4a를 진행할지. 진행하면 배포 전에 운영 DB 백업과 태그 없는 행 수 확인이 필요하다.
3. 4b를 진행할지. 진행하면 GitHub 시크릿 5개를 직접 등록해야 한다.

## Deferred

- 통계 identity key 전환(`cd01609`의 나머지). 트리거: 예약어 태그명 충돌 보고 또는 통계 entry를 id로 참조해야 할 때.
- 대시보드 정보 패널의 DOM 노드 조립, `title` 재파싱 제거, 전역 `event` 제거(`56f6200`의 나머지). 트리거: CSP에서 inline handler를 막을 때.
- 살리기가 끝나면 로컬 브랜치 `feat/grid-label-and-hour-axis`를 지운다.
