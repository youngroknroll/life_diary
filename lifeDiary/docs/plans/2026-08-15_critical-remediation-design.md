# Critical Correctness, Security, and Account Lifecycle Remediation Design

작성일: 2026-08-15

상태: 사용자 승인 완료

후속 구현 계획: `docs/plans/2026-08-15_critical-remediation-plan.md`

## 목적

2026-08-15 전수 감사에서 확인된 웹 P0와 직접 연결된 P1을 하나의 설계로
정리한다. 핵심 목표는 다음 네 가지다.

1. 태그 표시명이 통계 식별자와 충돌하지 않게 한다.
2. 사용자가 명시적으로 삭제한 기록과 화면·통계·DB 상태를 일치시킨다.
3. 저장 메모가 HTML로 재해석되지 않게 하고 삭제 성공 이후 UI가 거짓 실패
   상태로 되돌아가지 않게 한다.
4. 로컬 비밀번호 가입과 Google 가입이 같은 동의·초기화·탈퇴 유예 계약을
   따르게 한다.

이 문서는 설계만 승인한다. 코드, 스키마, 설정, 배포 스케줄러 변경은 후속
구현 계획의 TDD 단계와 별도 운영 승인 게이트를 통과해야 한다.

## 감사 기준선

- 전체 pytest: `501 passed in 300.09s`
- Django 기본 check: 통과
- migration drift: 없음
- prod deploy check: 통과
- JavaScript 10개 `node --check`: 통과
- ko/en 카탈로그 4개 GNU 형식 검사: 통과
- desktop settings check: allauth 앱 불일치로 실패

자동화 기준선이 녹색이어도 다음 경계는 보호되지 않았다.

- 사용자 태그명과 합성 `미분류` 항목의 identity 충돌
- 선택일 이외의 통계 캐시 의존 범위
- `transaction.atomic()` commit 전 cache invalidation 발행
- Google 가입 동의·시드 태그·탈퇴 취소
- 브라우저에서 HTML 속성을 읽어 `innerHTML`로 되넣는 흐름
- 태그 삭제 문구와 `SET_NULL` persistence 의미의 불일치

## 고려한 접근

### A. 통합 상위 계획과 독립 실행 Lane — 채택

통계·프런트 보안·계정 수명주기를 한 설계에 두되 각 Lane은 별도의 Red/Green
증거와 완료 게이트를 가진다. 연결된 의존성을 놓치지 않으면서도 한 Lane의
실패가 다른 Lane의 배포를 강제하지 않는다.

### B. 모든 결함을 한 번에 수정

파일과 테스트 수가 많아 Red 원인과 회귀 원인을 구분하기 어렵다. 프런트
브라우저 검증, 스키마 migration, 인증 adapter가 한 변경 집합에 섞이는 문제도
있어 채택하지 않는다.

### C. 결함마다 별도 계획

작업은 작아지지만 통계 identity·태그 삭제·cache invalidation처럼 같은 데이터
흐름의 문제를 서로 다른 계약으로 고칠 위험이 있다. 데스크톱과 일반 UX는
별도 계획으로 유지하되 이번 웹 핵심 결함에는 적용하지 않는다.

## 승인 범위

### Lane A — 통계와 기록 정합성

- 사용자 태그와 합성 미기록 항목을 표시명이 아닌 안정적인 내부 key로 구분
- 일·주·월·분석 집계와 hourly chart JSON에서 같은 identity 계약 사용
- 수면 제외 정책을 편집 가능한 태그명 대신 `Category.slug == "sleep"`로 판정
- “기록까지 함께 삭제” 경로에서 해당 `TimeBlock`과 memo를 실제 삭제
- 기존 `tag_id IS NULL` 숨은 행을 migration에서 제거하고 이후 tag를 필수 FK로 전환
- 슬롯·태그·목표·메모 변경 후 사용자의 모든 stats cache generation 교체
- cache invalidation은 transaction commit 이후에만 발행

### Lane B — 대시보드 보안과 핵심 상호작용

- 저장된 태그명·메모를 HTML 문자열에 보간하지 않고 DOM `textContent`로 렌더
- SSR과 부분 렌더 모두 `data-tag-name`, `data-memo`를 상태 원천으로 사용
- 태그 선택 시 클릭 대상을 명시적으로 전달하고 전역 `event` 의존 제거
- DELETE 요청 실패에서만 이전 행을 복원
- 서버 DELETE 성공 뒤 렌더 또는 event listener가 실패해도 “삭제 실패”로 되돌리지 않음
- 성공 event에는 실제 삭제한 `filledSlots`를 전달

### Lane C — 계정 수명주기

- 취소된 OneToOne 삭제 요청 행을 새 15일 요청 상태로 재사용
- 로컬 가입의 사용자 저장과 seed tag 생성을 한 transaction으로 묶음
- Google 자동가입을 끄고 동의 필드가 있는 social signup form을 반드시 통과
- Google 가입 성공도 같은 transaction에서 seed tag 생성
- 이미 연결된 Google identity가 유예기간 내 로그인하면 삭제 요청 취소
- 유예기간이 지난 Google 로그인은 계정을 재활성화하지 않음
- purge 본체의 기존 cascade·masked audit·순차 idempotency 계약 유지
- 실제 scheduler 파일은 공급자 선택 승인 전에는 구현하지 않음

## 명시적 제외

- desktop settings/allauth 부팅 실패와 단일 로컬 사용자 인증
- PyInstaller spec, desktop README, release workflow, CDN 오프라인 번들
- 통계 차트 대체 표, 모바일 768~991px 레이아웃, bottom sheet focus 등 일반 UX
- SMTP/reCAPTCHA fail-fast, axes/cache backend 교체
- 중복 slot payload, 태그 API 길이 제한 등 감사 P2
- 서비스 분리, 새 framework, event bus, Celery 도입
- CSP 전체 nonce 전환과 `unsafe-inline`/`unsafe-eval` 제거

제외 항목은 `docs/project-status.md`의 후속 작업으로 남기며 이번 구현이 조용히
수정하지 않는다.

## 핵심 설계

### 1. 통계 identity는 표시명과 분리한다

새 순수 모듈 `apps/stats/aggregation/identity.py`가 다음 key 계약을 소유한다.

```text
실제 태그:       tag:<database id>
합성 미기록 항목: unclassified
```

실제 태그 entry는 `key`, `tag_id`, `name`, `color`를 갖고, 합성 항목은 `key`,
`tag_id=None`, 번역된 `name`, 회색 `color`, `is_unclassified=True`를 갖는다.
사용자가 `미분류` 또는 `Unclassified`를 태그명으로 사용해도 key가 다르므로 합계가
섞이지 않는다.

`hourly_stats`도 표시명을 dict key로 쓰지 않고 위 key를 사용한다. Chart.js는
`tag.key`로 값을 찾고 `tag.name`만 label에 표시한다. 서버 템플릿과 JSON의 외부
표시 문자열은 그대로 유지하므로 사용자에게 불필요한 내부 key가 노출되지 않는다.

### 2. 태그 없는 TimeBlock은 유효한 기록 상태가 아니다

현재 UI는 이동하지 않는 삭제를 “기록까지 함께 삭제”라고 명시한다. 따라서
유효한 `TimeBlock`은 항상 사용자 소유 `Tag`를 가진다는 invariant를 채택한다.

구현은 두 단계다.

1. `DeleteTagUseCase`가 이동 목적지가 없으면 source tag의 `TimeBlock`을 먼저
   삭제한다. 같은 transaction 안에서 tag를 삭제하고 cache 변경 event를 예약한다.
2. dashboard migration `0007`이 기존 `tag_id IS NULL` 행을 삭제한 뒤 FK를
   `null=False, on_delete=CASCADE`로 바꾼다. admin·script 등 use case 밖 삭제도 같은
   invariant를 따른다.

기존 tagless 행의 memo도 함께 삭제된다. 이는 과거 UI에서 사용자가 선택한
“기록까지 함께 삭제”를 persistence에 반영하는 데이터 정리다. migration은
비가역적이므로 배포 전 DB backup과 tagless 행 수 확인이 필수이며, rollback은
코드 migration이 아니라 backup 복원으로 수행한다.

### 3. 통계 캐시는 사용자 generation으로 무효화한다

날짜별 key를 모두 계산해 삭제하는 대신 사용자별 무작위 generation token을
cache에 둔다.

```text
stats-generation:<user id> = 무작위 token
stats:<user id>:<token>:<date>:<language>:v3
```

generation entry가 eviction되더라도 새 무작위 token을 만들므로 오래된 `v1` key가
다시 활성화되지 않는다. 숫자 increment를 사용하지 않아 현재 FileBasedCache의
비원자적 `incr()`에도 의존하지 않는다.

소유 앱은 자신의 변경 signal만 발행한다.

```text
dashboard time_blocks_changed ─┐
tags      tags_changed         ├─> stats receivers -> rotate user generation
users     goals_changed        │
users     notes_changed        ┘
```

각 use case는 `transaction.on_commit()`에서 signal을 발행한다. rollback된 변경은
generation을 바꾸지 않고, commit 전 구데이터로 cache가 다시 채워지는 경합도 오래된
token 아래에 격리된다.

### 4. 브라우저 정보 패널은 DOM node로 조립한다

`slotTagInfo()`는 tooltip인 `title`을 다시 파싱하지 않는다. SSR 템플릿과
`buildBlock()`이 동일한 `data-tag-name`·`data-memo`를 만들고, 정보 패널은
`replaceChildren()`, `createElement()`, `textContent`로 조립한다.

정적 아이콘도 element로 만들며 삭제 버튼은 inline `onclick` 대신 event listener를
사용한다. memo와 tag name은 어느 단계에서도 `innerHTML`에 들어가지 않는다.

DELETE 함수는 다음 상태 경계를 가진다.

```text
request pending -> HTTP 실패: snapshot 복원 + 삭제 실패
request pending -> HTTP 성공: 서버 commit 확정
server committed -> UI 적용 실패: 삭제됨/화면 갱신 실패 안내, snapshot 복원 금지
server committed -> consumer event 실패: console 기록, 성공 UI 유지
```

### 5. 로컬과 Google 가입은 같은 계약을 공유한다

`SOCIALACCOUNT_AUTO_SIGNUP=False`로 두고
`SOCIALACCOUNT_FORMS["signup"]`에 프로젝트 `SocialSignupForm`을 등록한다. form은
로컬 `SignupForm`과 같은 필수 consent 문구를 제공한다.

로컬 view와 social form의 save는 각각 명확한 `transaction.atomic()` 경계 안에서
사용자 저장과 `create_seed_tags(user)`를 수행한다. seed 생성이 실패하면 사용자도
남지 않는다. 두 경로가 allauth 내부 save 구현을 억지로 공유하지는 않지만 결과
계약은 동일하다.

`LifeDiarySocialAccountAdapter.pre_social_login()`은 provider 인증을 마친 뒤 실행된다.
`sociallogin.is_existing`인 연결된 계정만 대상으로 하고, inactive 사용자의 유효한
pending deletion을 `cancel_account_deletion()`으로 취소한다. 새 계정이나 단순 email
충돌은 이 경로로 재활성화하지 않는다. 기한이 지난 요청은 기존 서비스가 `False`를
반환하므로 inactive 상태를 유지한다.

### 6. 탈퇴 재요청과 purge 운영 경계

취소된 `AccountDeletionRequest`는 새 행을 만들지 않고 row lock 후 다음 값을
초기화한다.

- `requested_at = now`
- `scheduled_delete_at = now + 15 days`
- `cancelled_at = None`
- `purged_at = None`
- `user.is_active = False`

활성 요청의 기존 idempotency는 유지한다. purge는 due request를 transaction 안에서
잠그고, 기존 owner cascade와 masked audit를 유지한다.

실제 scheduler는 구현 전 아래 중 하나를 사용자가 승인해야 한다.

1. 배포 provider의 managed cron/cron job
2. GitHub Actions schedule과 production DB secrets
3. 운영자가 관리하는 별도 cron

승인 기준은 하루 최소 1회 실행, 중복 실행 방지, 실패 알림, overdue 수치, missed-run
복구 명령, secret 최소권한이다. desktop 계정 삭제 정책은 별도 desktop 계획에서
결정한다.

## 오류 처리

- 통계 entry에 알 수 없는 key가 들어오면 조용히 표시명으로 fallback하지 않고
  테스트에서 실패하게 한다.
- cache backend 장애 시 통계 계산 자체는 계속 가능해야 하며 generation 조회/회전
  실패는 기존 cache failure 정책과 함께 명시적으로 검토한다. 이번 범위에서 새
  cache service나 네트워크 backend는 도입하지 않는다.
- social signup seed 실패는 전체 transaction을 rollback하고 allauth form 오류 또는
  서버 오류로 끝낸다. 반쪽 계정은 허용하지 않는다.
- social pre-login은 provider 인증이 완료된 기존 연결 계정에만 적용한다.
- tag cleanup migration은 backup 없는 production 적용을 금지한다.

## 역할

### Activated Roles

- Product Scope Owner — “기록까지 함께 삭제”와 tagless 데이터 제거 의미 승인
- Domain Architecture Reviewer — stats identity, app signal 방향, transaction 경계
- Backend TDD Coach — 각 backend Scenario를 하나씩 Red/Green으로 진행
- Backend & Integration Engineer — Python, migration, settings, tests, 문서 구현
- Security & Resilience Reviewer — DOM XSS, social identity, 삭제·purge 경합
- Deployment & Operations Reviewer — 비가역 migration과 scheduler 승인 게이트
- Web Experience Designer — social consent 화면과 상태 안내 conformance
- Browser Interaction Reviewer — DOM sink, tag selection, delete success/failure 상태
- Frontend Implementation Engineer — 승인된 dashboard JS/template/social template 변경
- Quality Verification Lead — acceptance-evidence matrix와 최종 판정

### Not Activated

- AI Automation Architect — AI/LLM 동작이 없다.

## 수용 기준

1. `미분류`/`Unclassified` 사용자 태그 10분과 합성 미기록 시간이 모든 통계에서
   별도 entry로 유지된다.
2. 이름만 바뀐 sleep-category 태그는 같은 주간 active-time 정책을 따른다.
3. 이동 없는 태그 삭제 후 source tag의 TimeBlock과 memo가 0건이고 통계·dashboard
   기록률이 일치한다.
4. rollback된 mutation은 stats cache를 무효화하지 않으며 commit된 슬롯·태그·목표·
   메모 mutation은 선택 날짜와 무관하게 다음 stats 요청에 반영된다.
5. HTML 같은 memo/tag name은 정보 패널에서 문자로만 보이고 새 element 또는 event
   handler를 만들지 않는다.
6. `window.event`가 없는 브라우저에서도 태그를 선택하고 저장할 수 있다.
7. DELETE HTTP 성공 뒤 후속 UI/event 오류가 나도 삭제된 행을 복원하거나 “삭제 실패”로
   표시하지 않는다.
8. 취소 후 재탈퇴 요청이 새 15일 deadline으로 정상 갱신된다.
9. 로컬/Google 신규 가입 모두 명시적 동의를 요구하고 seed tag를 받으며 bootstrap
   실패 시 사용자도 rollback된다.
10. 연결된 Google 사용자는 유예기간 안에서만 탈퇴를 취소할 수 있다.
11. scheduler 공급자 승인 전 운영 자동삭제 완료를 주장하지 않는다.

## 문서 관계

- 이 설계와 후속 계획은 `docs/plans/2026-08-10_comprehensive-review-follow-up-plan.md`의
  이미 해결된 TAG-OWN/I18N 항목을 대체한다.
- desktop, 일반 접근성, 운영 설정 결함은 기존 계획 또는 새 후속 계획으로 남는다.
- 구현 완료 시 각 파일 소유자가 `docs/refactoring/` 또는 `docs/frontend/` 작업 로그와
  `docs/project-status.md`를 갱신한다.
