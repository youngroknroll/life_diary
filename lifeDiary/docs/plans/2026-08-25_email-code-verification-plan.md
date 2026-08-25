# 이메일 6자리 코드 인증 — 가입 인증 + 비밀번호 재설정 전환 계획

작성 2026-08-25. 브랜치 `feat/email-code-verification`.

## Context

현재 두 흐름 모두 코드 인증이 없다.

- `apps/users/views.py:191` `signup_view` — 폼 저장 직후 `login()`을 호출한다.
  이메일 소유 확인 없이 계정이 활성 상태로 열린다.
- `apps/users/urls.py:12` 이하 — 비밀번호 재설정은 Django 기본 링크 방식
  (`reset/<uidb64>/<token>/`, `PasswordResetConfirmView`)이다.

사용자 요구: **최초 로그인과 비밀번호 재설정 모두 이메일로 6자리 코드를 보내
확인한다.**

## 사용자 결정 (2026-08-25)

| 질문 | 결정 |
|---|---|
| 인증 시점 | **가입 후 1회 이메일 인증.** 계정당 한 번. 새 기기마다 요구하는 2FA는 하지 않는다 |
| 비밀번호 재설정 | **코드 방식으로 교체.** 기존 uidb64/token 링크 경로를 제거한다 |
| 기존 계정 | **인증 완료로 간주.** 마이그레이션에서 backfill |
| 데스크톱 | **코드 인증 비활성화.** `lifeDiary/settings/desktop.py`의 플래그로 끈다 |
| 검증 시도 한도 | **코드당 3회** (2026-08-25 정정) |
| allauth 계정 URL | **`allauth.socialaccount.urls`만 include.** `/accounts/password/reset/` 등 중복 계정 경로를 닫는다 |
| 구글 약관 동의 | **`SOCIALACCOUNT_AUTO_SIGNUP = False`.** 구글 가입도 시안 1a를 거쳐 아이디 선택 + 약관 동의를 받는다 |
| 추가 UI | **시안 `Life Diary allauth 화면.dc.html` 3화면을 함께 구현**하고, 이메일 코드 화면도 같은 디자인 언어를 따른다 |

## 디자인 출처

Claude Design 프로젝트 `a76fc6a6-816e-4865-a42d-d673ab2bca93`,
파일 `Life Diary allauth 화면.dc.html` (etag 1787580566710045)에서 읽었다.

| 시안 | 대상 템플릿 |
|---|---|
| 1a 소셜 가입 완성 | `templates/socialaccount/signup.html` (`/accounts/3rdparty/signup/`) |
| 1a 변형 | 이메일 충돌 시 안내 + 「기존 계정으로 로그인」 |
| 1b 로그인 취소 | `templates/socialaccount/login_cancelled.html` |
| 1c 인증 오류 | `templates/socialaccount/authentication_error.html` |
| 1d 구현 노트 | URL 축소·AUTO_SIGNUP 결정의 근거 |

시안은 색을 하드코딩(#2C6E4A, #14211A, #6C7A70, #E3E6E1, #F5F6F4)했지만
저장소 `apps/core/static/core/css/style.css`의 토큰
(`--color-primary`, `--color-text`, `--color-text-muted`, `--color-border`,
`--color-surface-soft`)과 값이 일치한다. **구현은 토큰만 쓴다.** 시안에는
다크 테마가 없고 저장소에는 있기 때문에, 하드코딩하면 다크에서 깨진다.

레이아웃도 시안의 인라인 `width:340px` 카드가 아니라 기존
`auth-panel`·`auth-card`·`btn-sian`·`form_field`·`_field_errors.html`을
재사용한다. 시안 1d가 "로그인 화면의 auth-panel · auth-card 클래스를 그대로
쓴다"고 지정한 것과 같다.

## 승인 범위

1. 6자리 코드 발급·발송·검증 공통 부품 (모델 2개, 도메인 서비스 1개 모듈)
2. 가입 흐름 변경: 가입 → 코드 발송 → 코드 입력 → 인증 완료 + 로그인 → 온보딩
3. 아이디/비밀번호 로그인 게이트: 미인증 계정은 세션을 열지 않고 인증 화면으로
4. 비밀번호 재설정 3단계 전환: 이메일 입력 → 코드 입력 → 새 비밀번호 설정
5. 기존 링크 기반 재설정 경로·템플릿 제거
6. 설정 플래그와 데스크톱 비활성화
7. allauth 소셜 화면 3종 오버라이드 (시안 1a·1b·1c)
8. `allauth.urls` → `allauth.socialaccount.urls` 축소와 `SOCIALACCOUNT_AUTO_SIGNUP = False`
9. 신규 화면 전용 CSS 추가 (`auth-code-*`, `auth-identity`, `auth-panel--centered`)
10. 신규 문자열 ko/en 번역

## 명시적 제외

- 새 기기·브라우저 단위 2단계 인증(신뢰 기기 쿠키, 기기 테이블)
- SMS·TOTP·백업 코드
- 이메일 주소 변경 시 재인증 (현재 이메일 변경 UI 자체가 없다)
- 기존 `username_recovery` 흐름 변경 (아이디 찾기는 코드가 필요 없다)
- `password_change`(로그인 상태 비밀번호 변경) 변경
- 관리자(admin) 로그인 게이트

## 수락 기준

| # | 기준 |
|---|---|
| A1 | 가입 직후에는 로그인 세션이 열리지 않고, 해당 이메일로 6자리 코드 메일 1통이 발송된다 |
| A2 | 올바른 코드를 입력하면 이메일 인증이 완료되고 로그인되어 `users:welcome`으로 이동한다 |
| A3 | 미인증 계정으로 아이디/비밀번호 로그인을 시도하면 세션이 열리지 않고 코드 입력 화면으로 유도된다 |
| A4 | 코드는 평문으로 저장되지 않는다 |
| A5 | 코드는 10분 후 만료되고, 검증 실패 3회를 넘기면 그 코드는 더 이상 통하지 않는다 |
| A6 | 재발송은 60초 쿨다운, 1시간 5회 상한을 따르며 새 코드 발급 시 이전 코드는 무효화된다 |
| A7 | 비밀번호 재설정은 이메일 입력 → 코드 입력 → 새 비밀번호 3단계로 동작하고, 이메일 등록 여부와 무관하게 동일한 응답을 준다 |
| A8 | 코드 검증 없이 비밀번호 설정 단계에 직접 접근하면 거부된다 |
| A9 | 기존 링크 경로 `/accounts/reset/<uidb64>/<token>/`와 allauth의 `/accounts/password/reset/`가 모두 사라진다 |
| A10 | 마이그레이션 후 기존 계정은 모두 인증 완료 상태이며 로그인이 막히지 않는다 |
| A11 | `EMAIL_VERIFICATION_ENABLED=False`(데스크톱)에서는 가입 즉시 로그인되고 코드 메일이 발송되지 않는다 |
| A12 | 소셜(Google) 가입자는 인증 완료 상태로 생성된다 |
| A13 | 신규 사용자 노출 문자열이 ko/en 양쪽에 존재한다 |
| A14 | `/accounts/3rdparty/signup/`가 시안 1a대로 렌더된다: 읽기 전용 구글 이메일, 아이디 입력(실시간 중복 검사), 약관 동의, 「가입 완료」/「취소하고 로그인으로」 |
| A15 | 구글 이메일이 기존 계정과 충돌하면 아이디 폼 대신 안내 문구와 「기존 계정으로 로그인」이 나온다 |
| A16 | 구글 로그인 취소 시 시안 1b 화면이, OAuth 오류 시 시안 1c 화면이 한국어로 렌더된다 |
| A17 | 신규·기존 인증 화면이 하드코딩 색 대신 `style.css` 토큰을 쓰고 다크 테마에서 읽힌다 |
| A18 | 구글 가입도 약관 동의를 거친다 (`SOCIALACCOUNT_AUTO_SIGNUP = False`) |

## 활성 역할 / 미활성 역할

Risk-Based Routing에서 네 행이 동시에 걸린다: 백엔드 도메인·스키마 변경,
보안 민감 변경, 프런트엔드 변경, 설정·데스크톱 변경. 합집합을 활성화한다.

**Activated Roles**

| 역할 | 이유 |
|---|---|
| Product Scope Owner | 가입 이탈에 직접 영향을 주는 흐름 변경이라 범위·수락 기준 확정이 필요 |
| Domain Architecture Reviewer | 모델 2개 신설과 도메인 서비스 위치, 의존 방향 결정 |
| Backend TDD Coach | 인증·재설정 백엔드 행위 전부가 Red-Green 대상 |
| Backend & Integration Engineer | 모델·서비스·뷰·URL·설정·테스트 구현 |
| Security & Resilience Reviewer | 계정 탈취 최단 경로. 코드 저장·만료·시도 제한·열거 방지 |
| Deployment & Operations Reviewer | 마이그레이션 backfill, 운영 메일 발송, 데스크톱 플래그 |
| Web Experience Designer | 신규 화면 3종과 가입·로그인 진입 경로 변경 |
| Browser Interaction Reviewer | 코드 입력 필드, 재발송 쿨다운 상태, 포커스·라이브 리전 |
| Frontend Implementation Engineer | 템플릿·CSS·브라우저 JS 구현 |
| Quality Verification Lead | 회귀 범위와 완료 증거 판정 |

**Not Activated**

| 역할 | 이유 |
|---|---|
| AI Automation Architect | LLM·모델·프롬프트가 범위에 없다 |

역할 산출물은 이 세션 정책상 서브에이전트를 띄우지 않고 본 문서 안에서
해당 역할 관점으로 직접 작성한다. 서브에이전트 실행이 필요하면 사용자가
지시한다.

## 도메인 경계와 의존 방향

```
views (HTTP)  ->  email_verification.py (도메인 서비스)  ->  models
forms (경계 검증)                       repositories (조회)
```

- 코드 생성·해시·만료·시도 한도 판정은 **모델 메서드**가 소유한다.
- 발급/재발송/검증/인증 완료 처리 orchestration은 `apps/users/email_verification.py`
  가 소유한다. 기존 `apps/users/account_deletion.py`와 같은 층의 도메인 모듈이다.
- 뷰는 HTTP·세션·리다이렉트만 담당한다. 뷰에 인증 규칙을 두지 않는다.
- `apps/users`는 다른 앱에 의존하지 않는다. 역방향 의존도 만들지 않는다.
- 메일 본문 렌더는 `render_to_string`으로 서비스 모듈 안에서 처리한다.
  두 흐름이 같은 발송 경로를 쓰므로 뷰에 중복 배치하지 않는다.

## 결합도·응집도 검토

- 신설 모듈은 "이메일 코드 인증"이라는 한 가지 이유로만 바뀐다. 응집도 확보.
- `signup_view`·`login_view`·재설정 뷰가 같은 서비스 함수를 호출한다. 결합은
  함수 시그니처 하나로 제한된다.
- 기존 `_is_rate_limited`(views.py:81)를 재사용한다. 새 rate limit 프레임워크를
  만들지 않는다.
- `UserAccountRepository`에 이메일로 사용자 조회가 이미 있다
  (`find_active_by_email`). 재설정 흐름은 이를 재사용한다.

## 보안 설계 (Security & Resilience Reviewer)

| 항목 | 결정 | 근거 |
|---|---|---|
| 코드 생성 | `secrets.randbelow(1_000_000)`를 6자리 zero-pad | `random` 모듈은 예측 가능 |
| 저장 | Django 패스워드 해셔로 해시 저장, 평문 컬럼 없음 | DB 유출 시 코드 재사용 차단 |
| 만료 | 10분 (`EMAIL_VERIFICATION_CODE_TTL_SECONDS`) | 6자리는 엔트로피 20비트뿐이라 수명이 방어선 |
| 시도 제한 | 코드당 **3회** 실패 시 폐기 (사용자 지정) | 100만분의 1을 무차별 대입으로 뚫는 경로 차단 |
| 재발송 | 60초 쿨다운 + 1시간 5회 | 메일 폭탄·비용 방어 |
| 코드 회전 | 새 코드 발급 시 같은 사용자·목적의 미사용 코드 전부 consume | 유효 코드 다중 존재 방지 |
| 열거 방지 | 재설정 요청은 이메일 존재 여부와 무관하게 동일 리다이렉트·동일 문구 | 기존 `username_recovery` 정책과 동일 |
| 타이밍 | 미등록 이메일도 동일 경로를 타되 발송만 생략 | 응답 시간 차이는 허용 범위로 판단, 이월 항목에 기록 |
| 세션 | 검증 전 상태는 `signup_verification_user_id` / `password_reset_user_id`로만 보관. 로그인 세션 아님 | 미인증 상태로 인증 페이지 이외 접근 불가 |
| 재설정 승격 | 코드 검증 성공 시 `password_reset_verified_user_id` + 검증 시각 기록, 10분 내에만 비밀번호 설정 허용 | 승격된 세션의 무기한 유효화 차단 |
| 세션 고정 | 비밀번호 저장 직후 `cycle_key()` 및 기존 세션 무효화 | 재설정 전 탈취 세션 유지 방지 |
| 재설정 부수효과 | 재설정 코드 검증 성공은 이메일 인증도 완료 처리 | 이메일 소유를 증명했고, 미인증 사용자가 재설정 후에도 못 들어가는 막다른 길 제거 |
| 기존 baseline | django-axes·로그인 reCAPTCHA·recovery throttling은 그대로 둔다 | 보안 baseline 회귀 금지 |

메일 발송 실패는 `logger.exception` 후 사용자에게 일반 문구를 보여준다.
예외 메시지를 화면에 노출하지 않는다.

## Pythonic 설계

- 불변식은 모델 메서드(`is_usable`, `register_failure`, `consume`)가 소유한다.
- 폼(`VerificationCodeForm`, `PasswordResetEmailForm`)이 경계 검증을 맡는다.
- 코드 발급과 폐기는 `transaction.atomic`으로 묶는다.
- 반환값은 명시적 `dataclass` 결과 객체 또는 예외로 표현하고, `None`으로
  실패 사유를 뭉개지 않는다.
- 설정 플래그는 `getattr(settings, ...)` 기본값 패턴으로 기존 뷰 관례를 따른다.

## 파일 목록과 구현 단계

### 1단계 — 공통 부품 (Backend TDD Cycle)

| 파일 | 작업 |
|---|---|
| `apps/users/models.py` | `EmailVerification`(user OneToOne, verified_at), `EmailVerificationCode`(user, purpose, code_hash, created_at, expires_at, attempt_count, consumed_at + 인덱스) 추가 |
| `apps/users/migrations/0004_email_verification.py` | 스키마 + 기존 사용자 verified backfill(reverse 포함) |
| `apps/users/email_verification.py` | 신규. `issue_code`, `send_verification_email`, `verify_code`, `mark_email_verified`, `is_email_verified`, `is_verification_enabled` |
| `lifeDiary/settings/dev.py` | `EMAIL_VERIFICATION_*` 기본값 |
| `lifeDiary/settings/desktop.py` | `EMAIL_VERIFICATION_ENABLED = False` |
| `apps/users/test_email_verification.py` | 신규 테스트 |

### 2단계 — 가입 인증 흐름 (Backend TDD Cycle)

| 파일 | 작업 |
|---|---|
| `apps/users/views.py` | `signup_view` 자동 로그인 제거·코드 발송, `signup_verify_view`, `signup_verify_resend_view`, `login_view` 미인증 게이트 |
| `apps/users/forms.py` | `VerificationCodeForm` |
| `apps/users/urls.py` | `signup/verify/`, `signup/verify/resend/` |
| `apps/users/signals.py` | 신규. allauth `user_signed_up`에서 소셜 가입 시 인증 완료 처리 |
| `apps/users/apps.py` | `ready()`에서 시그널 로드 |
| `apps/users/test_signup_email.py` | 자동 로그인 전제 테스트 수정 |

### 3단계 — 비밀번호 재설정 전환 (Backend TDD Cycle)

| 파일 | 작업 |
|---|---|
| `apps/users/views.py` | `password_reset_request_view`, `password_reset_verify_view`, `password_reset_resend_view`, `password_reset_set_view`. `RateLimitedPasswordResetView` 제거 |
| `apps/users/forms.py` | `PasswordResetEmailForm` |
| `apps/users/urls.py` | 링크 경로 2개 제거, 코드 경로 3개 추가 |
| `apps/users/test_password_reset.py` | 링크 기반 테스트를 코드 기반으로 재작성 |

### 4단계 — 프런트엔드 (Frontend Dual Review Gate)

| 파일 | 작업 |
|---|---|
| `apps/users/templates/users/verification/verify_code.html` | 신규. 가입 코드 입력 |
| `apps/users/templates/users/verification/verification_code_email.txt` | 신규 |
| `apps/users/templates/users/verification/verification_code_subject.txt` | 신규 |
| `apps/users/templates/users/password/password_reset_form.html` | 문구를 코드 방식으로 수정 |
| `apps/users/templates/users/password/password_reset_verify.html` | 신규 |
| `apps/users/templates/users/password/password_reset_set.html` | 신규 |
| `apps/users/templates/users/password/password_reset_confirm.html` | 삭제 |
| `apps/users/templates/users/password/password_reset_done.html` | 삭제 |
| `apps/users/templates/users/password/password_reset_email.txt` | 삭제 |
| `apps/users/static/users/js/verification_resend.js` | 신규. 재발송 쿨다운 카운트다운 |

### 5단계 — i18n·마감

| 파일 | 작업 |
|---|---|
| `locale/ko/LC_MESSAGES/django.po`, `locale/en/...` | 신규 문자열 추가, ko msgstr 채움, fuzzy 제거 |
| `docs/refactoring/2026-08-25_email-code-verification.md` | 작업 로그 |
| `docs/project-status.md` | 상태·증거·링크 갱신 |

### 6단계 — allauth 소셜 화면 (Frontend Dual Review Gate)

| 파일 | 작업 |
|---|---|
| `lifeDiary/urls.py` | `allauth.urls` → `allauth.socialaccount.urls` |
| `lifeDiary/settings/dev.py` | `SOCIALACCOUNT_AUTO_SIGNUP = False` |
| `apps/users/forms.py` | `SocialSignupExtraForm` — 약관 동의 필드 추가 |
| `lifeDiary/settings/dev.py` | `SOCIALACCOUNT_FORMS = {"signup": ...}` |
| `templates/socialaccount/signup.html` | 신규. 시안 1a + 이메일 충돌 변형 |
| `templates/socialaccount/login_cancelled.html` | 신규. 시안 1b |
| `templates/socialaccount/authentication_error.html` | 신규. 시안 1c |
| `apps/core/static/core/css/style.css` | `auth-identity`, `auth-panel--centered`, `auth-panel__actions` 추가 |
| `apps/users/test_social_signup.py` | 신규 테스트 |

## Test List (TDD 체크포인트)

한 번에 하나씩 Red → Green.

**공통 부품**

1. 발급된 코드는 6자리 숫자다
2. 코드는 평문으로 저장되지 않는다
3. 올바른 코드 검증은 성공한다
4. 틀린 코드 검증은 실패하고 `attempt_count`가 1 증가한다
5. 실패 3회를 넘긴 코드는 올바른 코드여도 거부된다
6. 만료 시각을 넘긴 코드는 거부된다
7. 새 코드를 발급하면 같은 사용자·목적의 이전 미사용 코드가 consume된다
8. 쿨다운 60초 내 재발급 요청은 새 코드를 만들지 않는다
9. 1시간 5회 상한을 넘긴 재발급은 거부된다

**가입 인증**

10. 가입 후 응답에 로그인 세션이 없다
11. 가입하면 해당 주소로 메일 1통이 발송된다
12. 올바른 코드 입력 시 인증 완료 + 로그인 + `users:welcome` 리다이렉트
13. 틀린 코드 입력 시 로그인되지 않고 폼이 오류와 함께 다시 렌더된다
14. 미인증 계정의 정상 아이디/비밀번호 로그인은 세션을 열지 않고 인증 화면으로 보낸다
15. 인증 완료 계정의 로그인은 기존과 동일하다
16. `EMAIL_VERIFICATION_ENABLED=False`면 가입 즉시 로그인되고 메일이 없다
17. allauth 소셜 가입은 인증 완료 상태로 생성된다
18. 마이그레이션 backfill 후 기존 사용자는 인증 완료 상태다

**비밀번호 재설정**

19. 등록 이메일 요청 시 코드 메일 1통 + verify 페이지 리다이렉트
20. 미등록 이메일 요청도 같은 리다이렉트이며 메일은 0통
21. 올바른 코드 검증 후 비밀번호 설정 페이지 접근 가능
22. 코드 검증 없이 설정 페이지 직접 접근은 거부된다
23. 새 비밀번호 저장 후 그 비밀번호로 로그인된다
24. 완료 후 같은 코드를 재사용할 수 없다
25. 승격 세션은 10분 뒤 만료되어 설정 페이지가 거부된다
26. 재설정 코드 검증 성공은 이메일 인증도 완료시킨다
27. 기존 recovery rate limit 초과 시 메일이 발송되지 않는다
28. `/accounts/reset/<uidb64>/<token>/`와 `/accounts/password/reset/`는 404다

**allauth 소셜**

29. `SOCIALACCOUNT_AUTO_SIGNUP`이 False다
30. 소셜 가입 폼은 약관 동의 없이는 통과하지 않는다
31. 약관 동의와 아이디를 채우면 계정이 만들어지고 이메일 인증 완료 상태다
32. allauth 계정 URL(`account_reset_password`)이 더 이상 reverse되지 않는다
33. 소셜 프로바이더 URL(`google_login`)은 그대로 reverse된다

## Frontend Review Evidence

**리뷰 깊이: High.** 신규 화면 3종, 가입·로그인 진입 경로 변경, 재발송이라는
비동기 상태, 인증 실패 시 회복 경로가 모두 걸린다.

### Web Experience Designer — 사전 명세

- 세 화면 모두 기존 `auth-card` 패턴(`username_recovery_form.html`)을 그대로
  쓴다. 새 시각 언어를 만들지 않는다.
- 각 화면 상단에 **어느 주소로 보냈는지**를 마스킹해 보여준다
  (`al***@example.com`). 사용자가 오타를 즉시 알아채는 유일한 단서다.
- 코드 입력은 단일 `input` 하나. 6칸 분리 입력은 붙여넣기·스크린리더에서
  더 나쁘다.
- 만료까지 남은 시간과 재발송 버튼을 입력 아래 한 줄에 둔다.
- 실패 문구는 남은 시도 횟수를 포함한다(3회 기준). 기존 로그인 화면의
  `field-error__count`(`n회 남음`) 표현을 그대로 쓴다.
- 가입 화면의 "가입" 버튼 문구는 그대로 두되, 가입 직후 화면에서 지금 무슨
  일이 일어났는지 한 문장으로 설명한다.
- 재설정 흐름의 각 단계에 "로그인으로 돌아가기" 이탈구를 유지한다.

**화면별 명세**

`코드 입력` (가입 인증 · 재설정 검증 공용 구조)

```
auth-panel > card auth-card > card-body
  auth-panel__brand   "라이프 다이어리"
  auth-panel__title   "메일로 보낸 코드를 입력하세요"
  auth-panel__lead    "al***@example.com 으로 6자리 코드를 보냈습니다"
  form-label          "인증 코드"
  input.form-control.auth-code-input   (mono, letter-spacing, 가운데 정렬)
  field-error + field-error__count     "코드가 맞지 않습니다  2회 남음"
  auth-code__meta     "5분 20초 후 만료"   [코드 다시 받기]
  btn-sian--primary.auth-panel__submit "확인"
  auth-panel__foot    "로그인으로 돌아가기"
```

`1a 소셜 가입 완성`

- 이메일은 입력이 아니라 **읽기 전용 신원 행** `auth-identity`: 좌측 `G` 마크
  (`auth-google__mark` 재사용), 주소, 우측 `GOOGLE` 라벨(mono, meta 색).
- 아이디 입력은 `users/signup.html`의 `signup-validate.js` 실시간 중복 검사를
  그대로 재사용한다(`data-check-username-url`). 새 JS를 만들지 않는다.
- 약관 동의는 `consent-check` 블록을 그대로 쓴다.
- 주 CTA "가입 완료", 보조 이탈구 "취소하고 로그인으로"(`auth-panel__foot-minor`).
- 이메일 충돌 시: 아이디·동의 폼을 렌더하지 않고 안내 문단 +
  「기존 계정으로 로그인」 하나만 남긴다. 계정 자동 병합은 범위 밖.

`1b 로그인 취소` · `1c 인증 오류`

- 본문 가운데 정렬(`auth-panel--centered`), 입력 없음.
- 제목 / 두 줄 설명 / 버튼 2개(`auth-panel__actions`).
- 1b: "Google 로그인을 취소했습니다" — 계정에 변화가 없다는 사실을 먼저 말한다.
- 1c: "로그인이 완료되지 않았습니다" — 원인을 사용자 탓으로 돌리지 않고
  다음 행동 두 개를 준다.
- 두 화면 모두 1순위는 아웃라인 「Google로 다시 시도」, 2순위는 실린 
  「아이디로 로그인」. 시안의 버튼 순서와 위계를 그대로 따른다.

### Browser Interaction Reviewer — 사전 기준

- 코드 입력 필드: `inputmode="numeric"`, `autocomplete="one-time-code"`,
  `maxlength="6"`, `pattern="[0-9]*"`. iOS/안드로이드 자동완성이 걸린다.
- 화면 진입 시 코드 입력 필드에 포커스가 간다.
- 검증 실패 후 포커스는 입력 필드로 돌아가고 값은 비운다.
- 오류·성공 문구는 `role="status"` 또는 `aria-live="polite"` 영역에 넣는다.
- 재발송 버튼은 쿨다운 동안 `disabled` + 남은 초 표시. JS 없이도 서버가
  쿨다운을 강제해야 한다(진행 상태 표시만 JS 담당).
- 터치 타깃 최소 44px.
- `prefers-reduced-motion` 존중. 카운트다운에 애니메이션을 넣지 않는다.
- JS 실패 시에도 폼 제출과 재발송 POST가 동작한다(점진적 향상).

### 계획된 브라우저 증거

- 뷰포트 360 / 768 / 1280에서 세 화면 스크린샷
- 정상 입력, 오답 입력, 만료 코드, 재발송 쿨다운 클릭스루
- 콘솔 오류 0건 확인
- `node --check apps/users/static/users/js/verification_resend.js`

### 사후 검증 (구현 후 채움)

- Web Experience Designer 판정: (미실시)
- Browser Interaction Reviewer 판정: (미실시)
- Quality Verification Lead 완료 판정: (미실시)

## 운영·배포 검토 (Deployment & Operations Reviewer)

- 마이그레이션은 스키마 추가 + 데이터 backfill 두 operation. 기존 행을
  수정하지 않고 신규 테이블에 insert만 하므로 롤백은 테이블 drop이다.
- 운영 DB 사용자 수 규모에서 backfill은 단일 `bulk_create`로 충분하다.
- prod 메일 경로는 Gmail SMTP(`lifeDiary/settings/prod.py:99`). 가입·재설정
  메일량이 늘어난다. Gmail 발송 한도는 배포 전 확인 대상으로 남긴다.
- 메일 발송이 죽으면 **가입 자체가 막힌다.** 이 위험은 배포 체크리스트에
  명시하고, 발송 실패 시 사용자에게 재발송 안내를 노출한다.
- 데스크톱 빌드는 `EMAIL_VERIFICATION_ENABLED = False`로 기존 동작을 유지한다.

## 검증 명령과 기대 증거

```bash
conda run -n knou-life-diary pytest apps/users --tb=short
conda run -n knou-life-diary pytest
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
node --check apps/users/static/users/js/verification_resend.js
```

기대 증거: `apps/users` 타깃 테스트 전건 통과, 전체 회귀 통과(기존 실패
항목은 변화 없음), 마이그레이션 드리프트 없음, prod deploy check ERROR 0건,
브라우저 스크린샷과 콘솔 무오류.

`docs/project-status.md`에 기록된 desktop check 기존 실패는 이번 범위 밖이며
상태 변화 여부만 보고한다.

## Deferred

```text
Deferred Refactoring Note

- Topic: 새 기기·브라우저 단위 2단계 인증
- Why it is not part of the current scope: 사용자가 가입 1회 인증으로 범위를 확정했다
- Why it may be needed later: 계정 탈취 방어 수준을 올리려면 기기 단위 확인이 필요하다
- Trigger condition: 실사용자 계정 탈취 신고 또는 결제 기능 도입
- Expected change location: apps/users/email_verification.py, login_view, 신규 기기 모델
- Related tests: apps/users/test_email_verification.py
```

```text
Deferred Refactoring Note

- Topic: 재설정 요청의 응답 시간 균일화
- Why it is not part of the current scope: 현재도 username_recovery가 같은 특성을 갖고, 실측 위험이 확인되지 않았다
- Why it may be needed later: 미등록 이메일과 등록 이메일의 응답 시간 차이로 계정 존재를 추론할 수 있다
- Trigger condition: 타이밍 측정에서 유의미한 차이가 확인될 때
- Expected change location: apps/users/views.py 재설정 요청 뷰
- Related tests: apps/users/test_password_reset.py
```

- 이메일 주소 변경 기능과 변경 시 재인증
- 미인증 계정 자동 정리(예: 7일 경과 시 삭제) 관리 명령
- 인증 메일 다국어 본문 선택 (현재는 요청 시점 활성 언어를 따른다)
