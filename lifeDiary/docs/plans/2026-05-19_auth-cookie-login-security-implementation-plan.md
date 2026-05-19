# 인증 · 쿠키 · 로그인 보안 1차 통합 구현 계획

- 작성일: 2026-05-19
- 상태: 구현 계획 확정
- 기반 문서: `docs/plans/2026-05-19_auth-cookie-login-security-plan.md`

## 1. 승인 범위

이번 구현은 웹 인증 보안 1차 범위만 다룬다.

포함:
- `remember_me` 기간 14일 반영
- 일반 로그인 브라우저 종료 시 세션 만료 유지
- prod 쿠키/세션 보안 속성 명시화
- `password reset` / `username recovery` / `check-email` / `check-username` rate limit 추가
- `PASSWORD_RESET_TIMEOUT` 명시
- invalid / expired / reused reset token UX 검증
- `django-axes` lockout / cooloff / reset-on-success 검증
- 관련 focused 테스트 추가
- refactoring 문서 및 `docs/project-status.md` 업데이트

## 2. 비범위

- 데스크톱 인증 정책 변경
- 이메일 인증 신규 도입
- 소셜 로그인
- MFA / 2FA
- Redis 기반 세션 구조 변경
- CSP 전면 도입
- 로그인 실패 알림 / 보안 알림
- 쿠키 배너
- 사용자 모델 구조 변경
- 새 인증 추상화 계층 도입

## 3. 구현 원칙

1. 기존 로그인/회원가입/복구 흐름을 가능한 한 유지한다.
2. 프론트와 이미 연결된 endpoint는 응답 계약을 깨지 않는다.
3. 새로운 인증 프레임워크나 대규모 구조 변경을 하지 않는다.
4. 공개 공격면 보호는 별도 얇은 계층으로 추가한다.
5. 운영 환경 결합 설정은 쿠키 정책 명시화와 분리해 단계적으로 다룬다.

## 4. 구현 단계

### Phase 1 — 순수 저간섭 변경
목표:
- 현재 기능 간섭이 가장 적은 정책성 변경 먼저 반영

대상:
- `remember_me` 기간 14일
- `PASSWORD_RESET_TIMEOUT` 명시
- `SESSION_COOKIE_HTTPONLY`
- `SESSION_COOKIE_SAMESITE`
- `CSRF_COOKIE_SAMESITE`

예상 수정 위치:
- `apps/users/views.py`
- `lifeDiary/settings/prod.py`
- 관련 테스트 파일

### Phase 2 — 공개 endpoint 보호
목표:
- 기존 응답 계약을 유지하면서 공개 공격면에 rate limit 추가

대상:
- `password reset`
- `username recovery`
- `check-email`
- `check-username`

주의:
- known/unknown email 동일 응답 유지
- realtime validation UX 파손 금지
- rate limit 초과 시 payload/상태코드 정책을 테스트로 먼저 고정

예상 수정 위치:
- `apps/users/views.py`
- `apps/users/urls.py`
- 필요 시 rate limit 설정 위치
- 관련 테스트 파일

### Phase 3 — 운영 환경 결합 설정 검토
목표:
- 배포 환경과 직접 결합되는 보안 설정 검토

대상:
- `SECURE_PROXY_SSL_HEADER`
- `CSRF_TRUSTED_ORIGINS`
- `ALLOWED_HOSTS`

주의:
- 이 단계는 배포 환경 가정과 함께 검토
- 기능 간섭이 적은 쿠키 정책 명시화와 동일 수준으로 취급하지 않음

예상 수정 위치:
- `lifeDiary/settings/prod.py`
- 배포 문서/관련 설정 문서

## 5. TDD 체크포인트

### RED 1
테스트:
- 로그인 유지 체크 시 세션 만료가 14일인지 검증
- 미체크 시 browser-close expiry 유지 검증

기대 실패:
- 현재 30일 정책과 불일치

GREEN 최소 구현:
- `remember_me` expiry 상수만 14일로 조정

### RED 2
테스트:
- prod settings에 아래 값이 명시돼 있는지 검증
  - `SESSION_COOKIE_SECURE`
  - `CSRF_COOKIE_SECURE`
  - `SESSION_COOKIE_HTTPONLY`
  - `SESSION_COOKIE_SAMESITE`
  - `CSRF_COOKIE_SAMESITE`

기대 실패:
- 일부 값 미명시

GREEN 최소 구현:
- `prod.py`에 필요한 설정만 추가

### RED 3
테스트:
- `password reset`
- `username recovery`
반복 요청 시 제한 동작 검증

기대 실패:
- 현재 rate limit 부재

GREEN 최소 구현:
- 최소 rate limit 적용
- 응답 중립성 유지

### RED 4
테스트:
- `check-email`
- `check-username`
반복 호출 제한 검증

기대 실패:
- 현재 rate limit 부재

GREEN 최소 구현:
- 최소 rate limit 적용
- 기존 프론트 응답 계약 유지

### RED 5
테스트:
- invalid token
- expired token
- reused token
에서 invalid-link 상태 렌더링 검증

기대 실패:
- 커버리지 부재 또는 동작 미확정

GREEN 최소 구현:
- 기존 Django reset 흐름에 맞춘 최소 보정

### RED 6
테스트:
- `django-axes` lockout
- cooloff 후 재시도 허용
- 성공 로그인 후 failure count reset

기대 실패:
- 현재 행위 수준 검증 부족

GREEN 최소 구현:
- 필요한 fixture/settings 보정 범위 내 최소 수정

## 6. 검증 명령

최소 검증:

- `conda run -n knou-life-diary pytest apps/users/test_remember_me.py --tb=short`
- `conda run -n knou-life-diary pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py --tb=short`
- `conda run -n knou-life-diary pytest apps/users/test_realtime_validation.py --tb=short`
- `conda run -n knou-life-diary pytest apps/users/tests.py --tb=short`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy`

권장 추가 검증:
- 새로 추가되는 rate limit / reset-token 테스트 파일 전체 실행
- 필요 시 users 앱 focused regression 재실행

## 7. 완료 판단 기준

다음이 모두 충족되어야 완료로 본다.

- 승인 범위를 벗어난 변경이 없다
- RED → GREEN 순서를 지켰다
- `remember_me` 14일 정책이 테스트와 코드에서 일치한다
- prod 쿠키 보안 설정이 명시화되어 있다
- recovery / validation endpoint에 남용 방어가 적용되어 있다
- invalid / expired / reused token UX가 검증되었다
- `django-axes` 실동작 검증이 있다
- fresh verification 결과가 남아 있다
- refactoring 문서가 작성되었다
- `docs/project-status.md`가 업데이트되었다

## 8. Deferred Refactoring Notes

Deferred Refactoring Note

- Topic: 이메일 인증 도입 여부
- Why it is not part of the current scope: 가입 전환율 저하와 구현 범위 확대
- Why it may be needed later: 복구 채널 신뢰성 강화
- Trigger condition: 사용자 수 증가, 계정 보안 요구 상승
- Expected change location: `apps/users/`, auth templates, email flow
- Related tests: signup, login, recovery, email delivery tests

Deferred Refactoring Note

- Topic: 데스크톱 인증/세션 정책 분리 문서화
- Why it is not part of the current scope: 이번 범위는 웹 보안 우선
- Why it may be needed later: 로컬 단일 사용자 모드 위협 모델 정리 필요
- Trigger condition: 데스크톱 배포 안정화
- Expected change location: `lifeDiary/settings/desktop.py`, `desktop/`, docs
- Related tests: desktop smoke tests

Deferred Refactoring Note

- Topic: 운영 환경 결합 보안 설정 정리
- Why it is not part of the current scope: 기능 간섭이 적은 쿠키 정책 명시화와 성격이 다름
- Why it may be needed later: HTTPS 감지, reset 링크 품질, 배포 도메인 안전성 확보
- Trigger condition: 운영 도메인 변경, 프록시 구성 확정, `check --deploy` 보강 필요
- Expected change location: `lifeDiary/settings/prod.py`, 배포 환경 변수, 호스팅 설정
- Related tests: prod settings checks, deploy validation

## 9. 현재 검증 근거

기존 QA 확인:
- `conda run -n knou-life-diary pytest apps/users/test_signup_email.py apps/users/test_welcome.py apps/users/test_remember_me.py apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_realtime_validation.py apps/users/test_auth_enhance_render.py apps/users/test_jsi18n_auth.py apps/users/test_i18n_phase4.py apps/users/tests.py --tb=short`
- 결과: `52 passed in 33.25s`

주의:
- 이는 현재 인증 기능 회귀 안정성 근거다
- 이번 보안 범위 완료 근거는 구현 후 새 검증으로 다시 확보해야 한다
