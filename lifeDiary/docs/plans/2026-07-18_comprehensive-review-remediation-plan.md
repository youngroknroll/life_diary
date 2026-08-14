# 2026-07-18 전수 검토 지적사항 수정 계획

> 근거: `docs/2026-07-18_comprehensive-project-review.md`
> 사용자 승인: 아래 7개 항목 진행. **타임슬롯 그리드 키보드 접근, aria-live
> 알림은 명시적으로 제외** (사용자 지시: "키보드 접근과 aria는 불필요").

## Approved Scope

1. ko 번역 카탈로그 빈 msgstr 회귀 수정 (`django.po` 265건 + 조사 중 발견된
   `djangojs.po` 112건 — 동일 결함 클래스)
2. `TestLoginAxesBehavior` 2건 실패 원인 규명 및 정합화
3. `SECURE_PROXY_SSL_HEADER` 설정 (prod)
4. `CSRF_TRUSTED_ORIGINS` 결정 및 설정 (prod)
5. CSP 헤더 도입 (의존성 추가 없는 자체 미들웨어, prod 전용)
6. `dashboard` ↔ `stats` 양방향 의존 해소 (시그널 역전)
7. `apps/users/views.py` 인증/계정 조회 로직의 repository 계층 추출
8. 모바일 퀵인풋 바텀시트 Escape 닫기 + 포커스 트랩

### Exclusions

- 타임슬롯 그리드 키보드 조작(tabindex/keydown) — 사용자 제외 지시
- `showNotification`/`showOverlay` aria-live — 사용자 제외 지시
- 데스크톱 패키징(항목 11), 우선순위 드리프트(12), 광고 격리(13) — 미승인
- CSP nonce 기반 엄격 정책, Alpine CSP 빌드 전환 — Deferred (아래 노트)
- 로그인 실패 알림/로깅, 비밀번호 정책 강화 — 미승인 (검토 문서의 관측성 항목)

## Activated Roles

- Backend & Integration Engineer — 항목 1-7 구현 (필수)
- Backend TDD Coach — 항목 3-7의 백엔드 행동 변경 TDD 순서 (필수)
- Security & Resilience Reviewer — 항목 3-5 보안 설정 근거 (필수)
- Domain Architecture Reviewer — 항목 6-7 의존 방향/레이어링 결정 (필수)
- Web Experience Designer + Browser Interaction Reviewer — 항목 8 사전/사후
  이중 리뷰 게이트 (필수)
- Frontend Implementation Engineer — 항목 8 구현 (필수)
- Quality Verification Lead — 최종 증거 매트릭스 (필수)

### Not Activated

- Product Scope Owner — 범위는 검토 문서 + 사용자 승인으로 이미 확정
- Deployment & Operations Reviewer — 설정 변경은 있으나 배포 파이프라인/인프라
  변경 없음; prod deploy check로 대체
- AI Automation Architect — AI/LLM 범위 없음

## Design Decisions

### 1. ko 카탈로그

- GNU `msgen`으로 빈 msgstr를 msgid 항등 번역으로 채운다 (소스 문자열이
  한국어이므로 항등 번역이 올바른 번역이다).
- `django.po`, `djangojs.po` 모두 처리. en 카탈로그는 건드리지 않는다.
- 검증: pytest 전체 스위트 (startup에서 `conftest.py`가 재컴파일).

### 2. axes 테스트

- 단독 실행 시 3건 통과를 확인했다 (`3 passed in 10.29s`). 전체 스위트
  실행 순서/상태 오염 여부를 ko 수정 후 전체 실행으로 재규명한다.
- 전체 실행에서 재현되면 오염원을 격리 수정, 재현 불가면 원인 후보와 함께
  상태를 기록한다. 테스트 의미(락아웃 429 계약)는 변경하지 않는다.

### 3-5. prod 보안 설정 (`lifeDiary/settings/prod.py`)

- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` — Render는
  TLS를 프록시에서 종료하고 `X-Forwarded-Proto`를 전달한다.
- `CSRF_TRUSTED_ORIGINS = ["https://lifediary.onrender.com"]` — 결정: 단일
  프로덕션 호스트만 신뢰. 교차 출처 POST 요구 없음.
- CSP: 새 의존성 없이 `apps/core/middleware.py`의
  `ContentSecurityPolicyMiddleware`가 settings의 `CONTENT_SECURITY_POLICY`
  문자열을 응답 헤더로 부착. 설정이 비어 있으면 no-op → dev/desktop 무영향.
- 정책은 현재 실사용 리소스 기준 허용 목록: self + jsdelivr/cdnjs/unpkg CDN,
  reCAPTCHA(www.google.com, www.gstatic.com), 인라인 스크립트/스타일 및
  Alpine.js 요구사항(`'unsafe-inline'`, `'unsafe-eval'`) 허용.
  `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'` 로 심층방어.
- 검증 보경계: `contract` (`lifeDiary/test_prod_settings.py`).

### 6. dashboard ↔ stats

- `apps/dashboard/signals.py`에 `time_blocks_changed = Signal()` 정의.
- `apps/dashboard/use_cases.py`는 `apps.stats` import를 제거하고 시그널 send.
- `apps/stats/apps.py` `ready()`에서 리시버 연결 → 기존
  `invalidate_stats_cache` 호출. 의존 방향: stats → dashboard (허용 방향).
- 트랜잭션 소유: 기존과 동일하게 use case 내부에서 동기 발신 (기존 동작 보존).
- 계약 테스트: `apps.dashboard`의 어떤 모듈도 `apps.stats`를 import하지
  않는다 (forbidden import contract).

### 7. users/views.py 레이어링

- `apps/users/repositories.py`에 `UserAccountRepository` 추가:
  - `find_inactive_with_pending_deletion(username)`
  - `find_active_by_email(email)` (아이디 찾기용, 리스트 반환)
  - `username_exists(username)` / `email_exists(email)` (대소문자 무시)
- 뷰의 직접 ORM 4개 지점(`views.py:271-281`, `:292-293`, `:374-375`,
  `:401-402`)을 repository 호출로 치환. 비밀번호 검증 등 나머지 로직은 뷰에
  유지 (행동 보존, 최소 변경). 568줄 파일 분할·use_case 전면 이관은 Deferred.
- 기존 테스트(`test_password_reset.py`, `test_realtime_validation.py`,
  `tests.py` 등)가 행동을 보호한다. 리팩터링 전후 Green 유지가 증거.

### 8. 바텀시트 (frontend, Review Depth: Standard)

- `dashboard.js`: 시트 열림 상태에서 `Escape` keydown → `closeQuickInputSheet`,
  `Tab`/`Shift+Tab` 포커스 트랩 (시트 내 포커스 가능한 요소 순환).
- 리스너는 열림/닫힘 시 등록/해제. 기존 열림/닫힘/포커스 복원 로직 보존.
- 자동 테스트 없음 (Frontend Work Policy). `node --check` + 코드 리뷰 근거.

## Test List (backend)

| Scenario ID | Business behavior | Boundary | Test name | Status |
|---|---|---|---|---|
| SEC-01 | 프로덕션 설정은 프록시의 X-Forwarded-Proto를 HTTPS 판정에 사용한다 | contract | `test_prod_settings_trust_render_proxy_ssl_header` | Pending |
| SEC-02 | 프로덕션 설정은 프로덕션 오리진만 CSRF 신뢰 오리진으로 등록한다 | contract | `test_prod_settings_trust_only_production_origin_for_csrf` | Pending |
| SEC-03 | 프로덕션 응답에 CSP 헤더가 부착된다 | contract | `test_prod_csp_policy_covers_required_sources` (+ 미들웨어 web 테스트) | Pending |
| SEC-04 | CSP 설정이 비어 있으면 헤더를 부착하지 않는다 (dev/desktop 무영향) | web | `test_csp_header_absent_when_policy_not_configured` | Pending |
| ARCH-01 | dashboard 앱은 stats 앱을 import하지 않는다 | contract | `test_dashboard_does_not_import_stats` | Pending |
| ARCH-02 | 슬롯 저장/삭제 시 stats 캐시가 무효화된다 (기존 동작 보존) | domain | 기존 dashboard/stats 테스트 Green 유지 + 시그널 리시버 테스트 `test_time_block_change_invalidates_stats_cache` | Pending |
| USR-01 | 기존 인증/복구/검증 행동 보존 | web | 기존 `apps/users` 스위트 Green 유지 (리팩터링, 신규 행동 없음) | Pending |
| I18N-01 | ko 기본 화면 문자열이 비어 있지 않다 | 기존 스위트 | 기존 28건 실패 테스트가 Green으로 복귀 | Pending |

리팩터링(USR-01, 항목 6의 기존 동작)은 신규 행동이 아니므로 신규 Red 없이
기존 Green 유지가 계약이다. 신규 행동(SEC-01~04, ARCH-01/02 시그널 리시버)은
Red → Green 순서를 따른다.

## Frontend Review Evidence (항목 8)

- Review depth: Standard — 모달 상호작용 변경이나 단일 컴포넌트 범위.
- 사전: Web Experience Designer 경험 사양 + Browser Interaction Reviewer
  상호작용 기준 (구현 전 산출 필수, 본 문서 하단 실행 로그에 기록).
- 사후: 두 리뷰어의 Conforms/Deviates/Unverified 판정 + QVL 완료 결정.
- 계획된 브라우저 증거: `node --check`, 코드 기준 검토. 실기기 모바일 브라우저
  검증은 Unverified로 보고 (기존 바텀시트 작업들과 동일한 한계).

### 사전 리뷰 실행 기록 (구현 착수 전 완료)

**Web Experience Designer 경험 사양 요지** (전문은 세션 기록):
- Escape는 기존 `closeQuickInputSheet()`의 추가 트리거일 뿐, 새 닫힘 경로를
  만들지 않는다. X 버튼·백드롭·Escape 세 경로 모두 동일 결과(클래스 제거,
  aria-hidden 복원, body 스크롤락 해제, `lastSelectedSlotElement` 포커스 복원).
- Bootstrap 모달(새 태그, 카테고리 설명)이 시트 위에 열려 있으면 Escape는
  모달만 닫고(`.modal.show` 존재 검사) 시트 상태는 유지한다.
- 트랩 멤버는 시트 내 가시·활성 요소를 DOM 순서로: 닫기 버튼 → 새 태그 →
  관리 → 도움말 토글 → (펼침 시) 카테고리 설명 버튼 → 태그 버튼들 →
  메모 textarea → (활성 시) 저장 버튼. 매 Tab마다 재계산 필수(캐시 금지).
- 데스크톱(≥768px) 레이아웃에서는 Escape·트랩 모두 비활성. 수용 기준 11개 명시.

**Browser Interaction Reviewer 상호작용 기준 요지** (전문은 세션 기록):
- High 리스크 3건: (1) `openQuickInputSheet` 반복 호출로 인한 리스너 중복 등록
  → 열림 전이당 1회 등록 가드 필수. (2) `syncQuickInputSheetForLayout`
  데스크톱 강제 닫힘 경로의 리스너 누수 → 해당 분기에서도 해제 필수.
  (3) 중첩 Bootstrap 모달과의 Escape 충돌 → 모달 열림 시 시트 유지.
- Medium 리스크 2건: 포커스 가능 집합의 동적 드리프트(saveBtn disabled,
  usageHelp collapse) → 매 Tab 재계산; IME 조합 중 Escape 오발동 →
  `event.isComposing` 가드.
- `apps/dashboard/tests.py:251-268`이 focus→aria-hidden 순서를 고정하므로
  Escape 경로는 `closeQuickInputSheet()`를 그대로 재사용해야 한다.
- 리포지토리 전체 grep 결과 기존 document 레벨 Escape 핸들러 없음(충돌 없음).

### 사후 판정 (구현·검증 후)

**Web Experience Designer**: 수용 기준 11개 전건 정적 소스 추적상 일치, 코드
편차 0건. 단 `node --check`/pytest는 브라우저 keydown 경로를 실행하지 않으므로
종합 판정 **Unverified** — 실기기 모바일 브라우저 상호작용 증거가 나올 때까지
Conforms 불가. AC6(collapse 전환 애니메이션 프레임 중 트랩 타이밍)과 AC8의
잔여 리스크(Tab이 아닌 배경 클릭은 이 핸들러가 가로채지 않음 — 백드롭 CSS가
차단)를 명시.

**Browser Interaction Reviewer**: 사전 기준 10건(Escape 5 + 트랩 5) 전건
**소스 수준 Conforms** (file:line 근거 포함). 사전 지적한 High 리스크 3건
(리스너 중복 등록, 리사이즈 강제 닫힘 누수, 중첩 모달 Escape 충돌) 및 Medium
2건(동적 포커스 집합, IME) 모두 해소 확인. `tests.py:251-268`의
focus→aria-hidden 순서 계약 보존 확인. 실기기 Tab 순환/VoiceOver·TalkBack/
중첩 모달 Escape의 런타임 레이스는 Unverified로 명시. 잠재 갭 1건 기록:
`getClientRects()` 필터는 `visibility:hidden`을 제외하지 못함(현재 시트 내
해당 요소 없음 — 결함 아님, 향후 조건부).

**Quality Verification Lead 완료 결정**: 코드 수준 증거(양 리뷰어 소스 추적
일치, `node --check` exit 0, `pytest apps/dashboard` EXIT=0)는 충족. 게이트
규칙상 실기기 브라우저 검증이 Unverified이므로 사용자가 잔여 리스크를 수용해야
완료 처리 가능. 잔여 리스크: 실기기에서 Escape/Tab 순환/중첩 모달 레이스가
정적 추적과 다르게 동작할 가능성. 이는 기존 바텀시트 작업들(2026-05-15,
2026-05-23)이 남긴 "manual mobile browser checks remain unverified"와 동일한
성격의 한계다.

## Verification Commands

```bash
conda run -n knou-life-diary pytest --tb=short                     # 전체 회귀
conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py apps/core/test_csp_middleware.py --tb=short
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
node --check apps/dashboard/static/dashboard/js/dashboard.js
```

## Deferred Refactoring Notes

```text
- Topic: users/views.py 568줄 분할 및 인증 로직 use_case 전면 이관
- Why not now: 승인 범위는 직접 ORM 지점의 repository 추출까지
- Trigger: 인증 흐름에 다음 기능 추가 시
- Location: apps/users/views.py, apps/users/use_cases.py

- Topic: CSP nonce 기반 엄격화 (unsafe-inline/unsafe-eval 제거)
- Why not now: 인라인 스크립트/핸들러 및 Alpine.js가 현재 구조에 존재
- Trigger: 인라인 스크립트 제거 작업 착수 시 또는 django-csp 도입 승인 시
- Location: apps/core/middleware.py, templates/

- Topic: 로그인 실패/락아웃 시그널 로깅 (관측성)
- Why not now: 미승인 항목
- Trigger: 운영 관측성 단계 승인 시
```
