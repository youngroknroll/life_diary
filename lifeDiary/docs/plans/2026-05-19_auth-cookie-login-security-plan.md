# 인증 · 쿠키 · 로그인 보안 1차 승인 계획

- 작성일: 2026-05-19
- 상태: 승인 대기
- 역할: PO / General Manager
- 범위: 웹 인증, 웹 세션/쿠키 정책, 계정 복구 보호, 운영 보안 설정
- 설계 원칙: 현재 사용자 흐름과 응답 계약을 최대한 유지하고, 대규모 구조 변경 없이 공개 공격면과 보안 정책만 좁게 강화한다

## 1. 배경

현재 LifeDiary 웹 서비스는 다음 인증 기능을 이미 제공한다.

- 회원가입 시 이메일 필수
- 이메일 중복 방지
- 가입 직후 자동 로그인
- 로그인 brute-force 방어 `django-axes`
- 비밀번호 재설정
- 아이디 찾기
- `remember_me` 기반 장기 세션
- 운영 메일 백엔드 `Resend`

현재 확인된 실제 동작:

- 일반 로그인: 브라우저 종료 시 세션 만료
- 로그인 유지 체크 시: 장기 세션 유지
- 운영 설정: HTTPS redirect, HSTS, secure cookie 일부 적용
- 데스크톱은 웹과 별도 settings 및 별도 보안 모델 사용

현재 문제:

- recovery endpoint 자체에는 rate limit이 없다
- 공개 validation endpoint가 계정 존재 여부를 노출한다
- 세션/쿠키 보안 속성이 일부 Django 기본값에 암묵적으로 의존한다
- `remember_me` 장기 세션 정책이 보안 기준으로 명문화되어 있지 않다
- password reset timeout이 명시 설정으로 확정되어 있지 않다
- 웹과 데스크톱의 인증 보안 정책 차이가 문서 기준으로 충분히 정리되지 않았다

## 2. 설계 원칙

이번 1차 계획은 다음 원칙을 따른다.

1. 기존 로그인, 회원가입, 복구 흐름은 가능한 한 유지한다.
2. 새로운 인증 프레임워크, 사용자 모델, 세션 저장소 구조는 도입하지 않는다.
3. 보안 강화는 공개 공격면과 운영 정책에 한정한다.
4. 응답 형식이 이미 프론트엔드나 테스트에 연결된 endpoint는 응답 계약을 바꾸지 않는다.
5. 운영 환경 의존성이 큰 설정은 쿠키 정책 명시화와 분리해서 다룬다.
6. 데스크톱 앱은 이번 범위에서 직접 수정하지 않는다.

## 3. 승인 범위

이번 1차 범위는 웹 인증 보안만 다룬다.

### 3.1 회원가입 정책
- 이메일 필수 유지
- 중복 이메일 금지 유지
- 가입 직후 자동 로그인 유지
- 이메일 인증은 이번 1차 범위에 넣지 않는다
- 다만 "미검증 이메일을 복구 채널로 사용 중"이라는 리스크는 문서에 명시한다

### 3.2 로그인 세션 정책
- 일반 로그인: 브라우저 종료 시 세션 만료 유지
- 로그인 유지 체크 시 장기 세션 허용
- 장기 세션 기간은 **14일**로 확정한다
- 기존 30일 정책은 1차 범위에서 축소한다
- 이 변경은 기술 구조 변경이 아니라 제품 정책 변경으로 기록한다

### 3.3 쿠키/세션 보안 정책
운영 설정에 다음 정책을 명시적으로 둔다.

- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = "Lax"`
- `CSRF_COOKIE_SAMESITE = "Lax"`

주의:
- 위 항목은 현재 기능 간섭이 적은 "순수 보안 정책 명시화" 범위다
- 아래 운영 환경 결합 항목은 이번 1차 승인 문서에서는 별도 후순위 단계로 분리한다
  - `SECURE_PROXY_SSL_HEADER`
  - `CSRF_TRUSTED_ORIGINS`
  - `ALLOWED_HOSTS`

### 3.4 계정 복구 및 공개 endpoint 보호
다음 endpoint를 공개 공격면으로 간주하고 보호 범위에 포함한다.

- password reset
- username recovery
- `check-email`
- `check-username`

정책:

- 각 endpoint에 독립적인 rate limit 적용
- known/unknown email에 대해 동일한 사용자 응답 유지
- 메일 전송 실패 시 내부 상태를 사용자에게 노출하지 않는 현재 정책 유지
- `check-email`, `check-username`는 프론트 실시간 검증 흐름을 깨지 않도록 응답 계약을 최대한 유지한다
- rate limit 초과 시에도 불필요한 payload 변경이나 화면 전체 흐름 파손이 없도록 설계한다

### 3.5 password reset 정책
- password reset timeout을 명시 설정으로 고정
- 권장 기본값: **3시간**
- invalid / expired / reused token UX를 검증 범위에 포함한다
- Django 기본 reset 흐름은 유지한다

## 4. 비범위

다음은 이번 승인 범위에 포함하지 않는다.

- 데스크톱 인증 정책 변경
- 이메일 인증 신규 도입
- 소셜 로그인
- MFA / 2FA
- Redis 기반 세션 구조 변경
- CSP 전면 도입
- 로그인 실패 알림 / 보안 알림
- 쿠키 배너
- 실운영 메일 도메인 검증 완료 판단
- 새 인증 추상화 계층 도입
- 사용자 모델 구조 변경

## 5. 단계별 구현 전략

### Phase 1 — 순수 저간섭 변경
현재 기능 간섭이 가장 적고, 의존성 증가가 거의 없는 변경만 먼저 적용한다.

- `remember_me` 기간 14일로 조정
- `PASSWORD_RESET_TIMEOUT` 명시
- `SESSION_COOKIE_HTTPONLY` 명시
- `SESSION_COOKIE_SAMESITE` 명시
- `CSRF_COOKIE_SAMESITE` 명시
- 관련 focused 테스트 추가

### Phase 2 — 공개 endpoint 보호
공개 공격면을 보호하되 기존 응답 계약을 유지하는 방식으로 적용한다.

- `password reset` rate limit
- `username recovery` rate limit
- `check-email` rate limit
- `check-username` rate limit
- 프론트 실시간 검증 UX를 깨지 않는 응답 처리
- 관련 abuse/rate limit 테스트 추가

### Phase 3 — 운영 환경 결합 설정 검토
배포 환경에 직접 결합되는 항목은 별도 묶음으로 다룬다.

- `SECURE_PROXY_SSL_HEADER`
- `CSRF_TRUSTED_ORIGINS`
- `ALLOWED_HOSTS`

이 단계는 운영 플랫폼 설정과 함께 확인해야 하므로, 쿠키 정책 명시화와 같은 수준의 저간섭 변경으로 취급하지 않는다.

## 6. PO 결정

이번 1차 제품 판단은 다음으로 고정한다.

- 보안 범위는 웹만 우선 처리한다
- 가입 마찰을 늘리지 않기 위해 이메일 인증은 지금 도입하지 않는다
- 대신 복구/세션/쿠키 보안 기준을 먼저 강화한다
- `remember_me`는 유지하되 기간은 14일로 축소한다
- recovery endpoint와 공개 validation endpoint는 모두 이번 1차 보안 범위에 포함한다
- validation endpoint 보호는 기존 프론트 UX 계약을 해치지 않는 방식으로만 허용한다
- 데스크톱 보안 모델은 웹과 분리해서 후속 계획으로 다룬다
- 운영 환경 결합 설정은 쿠키 정책 명시화와 분리해 후순위 단계로 다룬다

## 7. 수용 기준

다음이 충족되어야 이번 범위 완료로 본다.

- 웹 로그인/복구/회원가입 보안 정책이 문서로 명확하다
- 일반 로그인과 로그인 유지의 세션 만료 정책이 코드/문서/테스트에서 일치한다
- 운영 쿠키 보안 속성이 명시 설정으로 정의된다
- recovery endpoint와 공개 validation endpoint에 남용 방어가 적용된다
- validation endpoint 응답 계약이 기존 사용자 흐름을 깨지 않는다
- password reset timeout이 명시된다
- invalid / expired / reused reset token UX가 검증된다
- `django-axes` lockout / cooloff / reset-on-success 동작이 검증된다
- 웹과 데스크톱 보안 정책 차이가 문서화된다
- 후속 보안 항목은 deferred로 분리된다

## 8. 구현 검증 기준

최소 검증은 다음 수준을 요구한다.

- remember me 동작 테스트
- password reset / username recovery 동작 테스트
- realtime validation endpoint 보호 테스트
- `django-axes` 실제 lockout / cooloff / reset-on-success 테스트
- prod settings 기반 쿠키/세션 보안 테스트
- `manage.py check --deploy` 결과 확인

예상 검증 명령:

- `conda run -n knou-life-diary pytest apps/users/test_remember_me.py --tb=short`
- `conda run -n knou-life-diary pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py --tb=short`
- `conda run -n knou-life-diary pytest apps/users/test_realtime_validation.py --tb=short`
- `conda run -n knou-life-diary pytest apps/users/tests.py --tb=short`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy`

## 9. 현재 확인된 리스크

현재 기준에서 남아 있는 주요 리스크:

- 미검증 이메일이 복구 채널로 사용됨
- 공개 validation endpoint가 계정 존재를 노출함
- recovery endpoint rate limit 부재
- 장기 세션 탈취 시 피해 범위 큼
- reverse proxy HTTPS 감지가 부정확하면 reset 링크 품질이 흔들릴 수 있음
- 데스크톱은 웹과 다른 보안 모델을 사용하지만 정책 문서가 약함

## 10. 검토 근거

검토에 사용한 역할:
- Tech Lead / Architect
- Security / Reliability
- Infra / DevOps
- QA

QA fresh verification:
- `conda run -n knou-life-diary pytest apps/users/test_signup_email.py apps/users/test_welcome.py apps/users/test_remember_me.py apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_realtime_validation.py apps/users/test_auth_enhance_render.py apps/users/test_jsi18n_auth.py apps/users/test_i18n_phase4.py apps/users/tests.py --tb=short`
- 결과: `52 passed in 33.25s`

주의:
- 위 결과는 현재 인증 기능 회귀 안정성 근거다
- 이번 보안 범위 완료 근거는 아니다
- 완료 판단은 본 계획의 추가 검증 항목까지 통과한 뒤에만 가능하다

## 11. Deferred Refactoring Notes

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

## 12. 승인 후 다음 구현 범위

다음 구현 계획은 아래 범위로 자른다.

`웹 인증 보안 1차 구현`

- Phase 1: 순수 저간섭 변경
- Phase 2: 공개 endpoint 보호
- Phase 3: 운영 환경 결합 설정 검토
- focused tests 추가
- project-status / refactoring 문서 업데이트
