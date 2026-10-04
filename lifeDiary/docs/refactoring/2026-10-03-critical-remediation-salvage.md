# Critical Remediation 미반영 커밋 선별 재적용 실행 로그 (2026-10-04)

- 계획: `docs/plans/2026-10-03-critical-remediation-salvage-plan.md`
- 원본 설계·계획·로그(이번에 복원): `docs/plans/2026-08-15_critical-remediation-design.md`, `docs/plans/2026-08-15_critical-remediation-plan.md`, `docs/refactoring/2026-08-15_critical-backend-remediation.md`, `docs/frontend/2026-08-15-dashboard-security-interaction.md`
- 브랜치: `fix/critical-remediation-salvage`
- 범위: 1~3단계. 4a(마이그레이션 0007)와 4b(purge 스케줄)는 사용자 결정 대기라 하지 않았다.

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

1단계(SV-01~03)는 옮긴 뒤 구현 파일만 되돌려 4개 실패(21개 통과)를 확인하고 복원했다.

## 검토

- Browser Interaction Reviewer, Web Experience Designer: 사전 검토 뒤 구현, 사후 정적 추적에서 위반 없음. 브라우저 확인은 아래 참조.
- Domain Architecture Reviewer: 지적 사항과 함께 승인. `tags`·`users`의 유스케이스와 신호 모듈은 `stats`를 import하지 않는다. 모든 알림이 `transaction.atomic` 안에서 `on_commit`으로 예약된다.
- Security & Resilience Reviewer: 머지를 막는 결함 없음. 중간 등급 1건은 위 "추가"로 반영했다.

## 검증 (2026-10-04, 통합 브랜치)

- 전체 회귀: `688 passed in 520.33s`. 기준선은 `main` 671.
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
- FileBasedCache에서의 세대 교체. 테스트는 LocMemCache를 쓴다.
- 운영 캐시 적중률 변화. 변경이 있을 때마다 그 사용자의 모든 날짜가 다음 요청에서 미스가 된다(2026-10-02 측정: 미스 1,144ms, 적중 446ms).

## Deferred

- 4a 마이그레이션 0007, 4b purge 스케줄: 사용자 결정 대기.
- **Google 가입 이메일 조작(기존 결함, 중간).** `templates/socialaccount/signup.html`의 이메일이 숨은 입력값이고 `SocialSignupForm.save`가 그 주소를 인증된 것으로 표시한다. allauth가 제공자 주소로 다시 묶는지는 확인하지 않았다. 트리거: 보안 트랙.
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
