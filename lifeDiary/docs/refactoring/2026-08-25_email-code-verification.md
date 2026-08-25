# 이메일 6자리 코드 인증 — 실행 로그

2026-08-25. 브랜치 `feat/email-code-verification`.
계획: `docs/plans/2026-08-25_email-code-verification-plan.md`

## 무엇을 바꿨나

가입과 비밀번호 재설정 두 흐름을 이메일 6자리 코드 인증으로 옮기고, 그 과정에서
드러난 allauth 중복 경로를 닫았다.

| 흐름 | 전 | 후 |
|---|---|---|
| 가입 | 폼 저장 즉시 `login()` | 코드 메일 → 코드 입력 → 인증 + 로그인 |
| 로그인 | 자격증명만 확인 | 미인증 계정은 세션을 열지 않고 코드 화면으로 |
| 비밀번호 재설정 | uidb64/token 링크 | 이메일 → 코드 → 새 비밀번호 |
| 구글 가입 | 자동 가입, 약관 동의 없음 | 시안 1a 경유, 아이디 선택 + 약관 동의 |
| allauth URL | `allauth.urls` 전체 | 소셜·프로바이더 경로만 |

## 새 파일

- `apps/users/verification_policy.py` — 정책값(수명·시도·쿨다운) 단일 출처.
  모델과 도메인 서비스가 같은 값을 봐야 해서 분리했다.
- `apps/users/email_verification.py` — 발급·발송·검증·인증 상태 도메인 서비스
- `apps/users/social_forms.py` — allauth 가입 폼 + 약관 동의.
  allauth 가 없는 데스크톱 설정에서 import 되지 않도록 별도 모듈이다.
- `apps/users/migrations/0004_...` — 모델 2개 + 기존 계정 backfill
- 템플릿: `users/verification/verify_code.html`, 메일 본문 4종,
  `users/password/password_reset_set.html`,
  `templates/socialaccount/{signup,login_cancelled,authentication_error}.html`
- `apps/users/static/users/js/verification.js` — 만료·쿨다운 카운트다운

## 지운 것

`password_reset_confirm.html`, `password_reset_done.html`,
`password_reset_email.txt`, `password_reset_subject.txt`,
`RateLimitedPasswordResetView`, `users:password_reset_confirm`,
`users:password_reset_done`.

## 설계 판단

- **코드는 해시로만 저장한다.** 6자리는 엔트로피가 20비트뿐이라 DB 유출 시
  평문이 남아 있으면 그대로 쓸 수 있다.
- **수명과 시도 한도가 실제 방어선이다.** 10분 · 코드당 3회(사용자 지정) ·
  재발송 60초 쿨다운 · 1시간 5회. 새 코드 발급 시 이전 미사용 코드는 모두 소진
  처리해 유효 코드가 둘 이상 존재하지 않게 한다.
- **재설정은 가입 여부를 응답으로 드러내지 않는다.** 없는 주소도 같은 화면,
  같은 만료·쿨다운 타이머로 넘어간다. 사용자가 없으면 타이머를 설정 기본값으로
  채우는 이유가 이것이다. 재설정 코드 화면에서는 남은 시도 횟수를 표시하지
  않는다 — 표시하면 없는 주소와 있는 주소가 구분된다.
- **재설정 코드 검증 성공은 이메일 인증도 완료시킨다.** 소유를 증명했는데도
  미인증이라 로그인이 막히는 막다른 길을 없앤다.
- **미인증 판정은 fail-closed 다.** `EmailVerification.verified_at` 이 있어야
  인증으로 본다. 행이 없으면 미인증이다. 기존 계정은 마이그레이션에서 채운다.
- **로그인 게이트는 살아 있는 코드가 있으면 새로 보내지 않는다.**
  자격증명을 아는 사람이 로그인을 반복해 메일을 쏟아내지 못하게 한다.

## 예정에서 바뀐 점

- 계획의 `apps/users/signals.py`(allauth `user_signed_up` 시그널)를 만들지
  않았다. `SOCIALACCOUNT_AUTO_SIGNUP = False` 로 모든 소셜 가입이 우리 폼을
  거치므로 폼 `save()` 에서 인증 표시를 하면 충분하다. 시그널을 두면 allauth 를
  `apps.py` 에서 import 하게 되어 데스크톱 설정이 깨진다.
- `ACCOUNT_EMAIL_VERIFICATION = "none"` 을 추가했다. account URL 을 닫자
  allauth 가 자기 확인 메일을 보내려다 `account_confirm_email` reverse 에서
  실패했다. 우리 코드 인증과 중복이라 껐다.
- `reverse("account_login")` 별칭을 `lifeDiary/urls.py` 에 남겼다. allauth
  내부(`socialaccount/views.py`, `account/internal/templatekit.py`)가 이 이름을
  reverse 한다. 해석은 먼저 include 되는 users 로그인이 가져간다.
- 카운트다운 자리표시자를 `%s` 에서 `{time}`·`{seconds}` 로 바꿨다. Django 의
  `templatize` 가 `{% trans %}` 안의 `%` 를 `%%` 로 이스케이프해 카탈로그 키가
  템플릿 원문과 어긋난다.
- 루트 `conftest.py` 의 `make_user` 가 인증 완료 행을 만들도록 했다. 이 픽스처가
  대신하는 것은 "이미 쓰고 있던 계정"이다. 미인증 계정은 테스트에서 명시적으로
  만든다.

## 검증

```
conda run -n knou-life-diary pytest
# 592 passed in 409.63s

conda run -n knou-life-diary python manage.py check
# System check identified no issues (0 silenced).

conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
# No changes detected

conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
# 1 warning (SECRET_KEY, 기존), ERROR 0

node --check apps/users/static/users/js/verification.js
# 통과

msgfmt --check-format locale/{ko,en}/LC_MESSAGES/django.po
# 양쪽 통과, 미번역 0건, fuzzy 0건(ko 헤더 제외)
```

신규 테스트 55건: `test_email_verification.py` 13, `test_signup_verification.py` 14,
`test_password_reset.py` 17(재작성), `test_social_signup.py` 13.

브라우저 실측(1280, 다크): 재설정 코드 화면, 코드 오류 상태, 소셜 가입 완성(1a),
로그인 취소(1b). dev DB 를 건드리지 않으려고 별도 SQLite 로 서버를 띄웠다.

## 미검증

- **모바일 뷰포트 실측.** 360px 캡처에서 카드가 넘치지만 기존 로그인 화면도
  같은 캡처에서 동일하게 넘친다. 캡처 방식(헤드리스 window-size, 뷰포트 에뮬레이션
  없음)의 한계로 보이며, 신규 화면이 기존 화면과 다르게 동작한다는 증거는 없다.
  실제 기기 확인이 필요하다.
- **인증 오류 화면(1c) 스크린샷.** 마크업은 1b 와 같은 구조이고 렌더(401)는
  테스트로 확인했지만 이미지로는 남기지 않았다.
- **실제 구글 OAuth 왕복.** 1a 는 대기 세션을 심어 확인했다.
- **prod 메일 발송량.** Gmail SMTP 일일 한도는 배포 전 확인 대상이다.

## Deferred

- 새 기기 단위 2단계 인증
- 미인증 계정 자동 정리 관리 명령
- 재설정 요청 응답 시간 균일화
- 이메일 주소 변경 기능과 변경 시 재인증
