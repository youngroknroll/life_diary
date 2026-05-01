# 계정 복구 기능 구현 계획 (아이디 찾기 + 비밀번호 재설정)

- 작성일: 2026-05-01
- 상태: 승인 대기
- 범위: 아이디(username) 찾기, 비밀번호 재설정, 이메일 인프라
- 후속(별도): 구글 OAuth 로그인 (이번 범위에서 제외)

## 1. 배경

현재 인증 흐름은 Django 기본 `User` 모델 + `UserCreationForm` 기반이다. 다음 자산이 빠져 있다.

- 회원가입 폼에 `email` 필드 없음 → 기존 사용자 다수가 이메일 미등록 가능성
- `EMAIL_*` 설정 전무 → 메일 발송 불가
- 비밀번호/아이디 복구 화면 및 라우트 없음

요구사항: **아이디 찾기** + **비밀번호 찾기** 추가.

## 2. 결정 사항

| 항목 | 선택 | 이유 |
|---|---|---|
| 아이디 찾기 방식 | 이메일로 username 발송 | 화면 표시는 enumeration 위험 |
| 비밀번호 재설정 방식 | Django 내장 `PasswordResetView` (토큰 링크) | 검증된 흐름, 임시비번보다 안전 |
| 메일 백엔드 (dev) | `console.EmailBackend` | 실제 발송 없이 터미널 출력 |
| 메일 백엔드 (prod) | SMTP, `.env` 자격증명 | 시크릿 분리 |
| 소셜 로그인 | 본 범위 제외 | allauth 도입 결정과 분리하여 단계 진행 |

## 3. Phase 별 작업

### Phase 1 — 이메일 인프라

**파일**
- `lifeDiary/settings/dev.py`: `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`, `DEFAULT_FROM_EMAIL = "noreply@lifediary.local"`
- `lifeDiary/settings/prod.py`: SMTP 설정을 `os.getenv`로 (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`)
- `.env.example`: 위 변수 자리표시자 추가

**검증**: `python manage.py shell -c "from django.core.mail import send_mail; send_mail('t','b','a@a','b@b'.split())"` → dev 콘솔 출력 확인.

### Phase 2 — 회원가입 이메일 필드

**파일**
- `apps/users/forms.py`: `SignupForm(UserCreationForm)` 신설. `email` 필수 + `clean_email`에서 `User.objects.filter(email__iexact=...)` 중복 검사
- `apps/users/views.py`: `signup_view`가 `SignupForm` 사용
- `templates/users/signup.html`: 폼이 필드 자동 렌더링하면 변경 최소

**마이그레이션**: 불필요. Django `User.email`은 이미 존재하며 blank 허용. 기존 미등록 계정은 복구 시 "이메일 미등록" 안내.

### Phase 3 — 비밀번호 재설정 (Django 내장)

**라우트** (`apps/users/urls.py`)

```
password-reset/           → PasswordResetView
password-reset/done/      → PasswordResetDoneView
reset/<uidb64>/<token>/   → PasswordResetConfirmView
reset/done/               → PasswordResetCompleteView
```

각 view에 `template_name`, `email_template_name`, `subject_template_name`, `success_url`을 명시.

**템플릿** (신규, `templates/users/password/`)
- `password_reset_form.html`
- `password_reset_done.html`
- `password_reset_confirm.html`
- `password_reset_complete.html`
- `password_reset_email.txt`, `password_reset_email.html`
- `password_reset_subject.txt`

**진입점**: `templates/users/login.html`에 "비밀번호 찾기" 링크 추가.

### Phase 4 — 아이디 찾기 (커스텀)

**폼** (`apps/users/forms.py`): `UsernameRecoveryForm` (email 1필드).

**뷰** (`apps/users/views.py`): `username_recovery_view`
- POST: `User.objects.filter(email__iexact=email)` 결과가 있을 때만 발송, **응답은 항상 동일 done 페이지** (enumeration 방지)
- 한 이메일에 다중 계정이면 모든 username 나열

**라우트**
```
username-recovery/        → username_recovery_view
username-recovery/done/   → username_recovery_done_view
```

**템플릿** (`templates/users/recovery/`)
- `username_recovery_form.html`
- `username_recovery_done.html`
- `username_recovery_email.txt`
- `username_recovery_subject.txt`

**진입점**: `login.html`에 "아이디 찾기" 링크 추가.

### Phase 5 — 테스트 (pytest, TDD)

- `apps/users/test_password_reset.py`
  - 유효 email → `mail.outbox` 1건, 메일 본문에 토큰 URL 포함
  - 미등록 email → 메일 0건, 동일 done 응답
  - 토큰으로 confirm GET 200, POST 새 비번 → complete 리다이렉트, 새 비번 로그인 성공
- `apps/users/test_username_recovery.py`
  - 등록 email → 메일 1건, 본문에 username
  - 미등록 email → 메일 0건, 동일 done 응답 (enumeration 방지 검증)
  - 동일 email 다중 계정 → 모든 username 포함
- `apps/users/test_signup_email.py`
  - email 누락 → form invalid
  - 이메일 중복 → form invalid

### Phase 6 — i18n

- 모든 신규 사용자 노출 문자열 `gettext` / `gettext_lazy` 마킹
- `django-admin makemessages -l en` (conda env `knou-life-diary`)
- `locale/en/LC_MESSAGES/django.po` 번역
- `compilemessages`

## 4. 변경/추가 파일 요약

**수정**
- `apps/users/forms.py`
- `apps/users/views.py`
- `apps/users/urls.py`
- `lifeDiary/settings/dev.py`
- `lifeDiary/settings/prod.py`
- `templates/users/signup.html`
- `templates/users/login.html`
- `.env.example`
- `locale/en/LC_MESSAGES/django.po` (+ `.mo`)

**신규 템플릿** (11개): password_reset 5종(html) + email 2종 + subject 1종 + username_recovery 2종(html) + email 1종 + subject 1종

**신규 테스트**: 3 파일

## 5. 보안 고려

| 위협 | 대응 |
|---|---|
| Account enumeration | 미등록/등록 email 모두 동일 done 응답 |
| 토큰 탈취 | Django 기본 토큰 + 만료 (필요시 `PASSWORD_RESET_TIMEOUT` 단축 검토) |
| 메일 본문 노출 | 토큰 URL은 단발성, 사용 후 무효화 (Django 내장) |
| 폼 자동화 공격 | 본 PR 범위 외 — `django-axes`는 `/login/`만 보호. 후속으로 복구 엔드포인트 rate-limit 검토 |
| 시크릿 노출 | SMTP 자격증명은 `.env`만, 리포지토리 커밋 금지 |

## 6. 비범위 (후속 이슈로 분리)

- 구글/소셜 로그인 (`django-allauth` 도입 여부 별도 결정)
- 복구 엔드포인트 rate limit (axes 확장 또는 `django-ratelimit`)
- 이메일 검증(가입 시 confirm) — 현 단계는 신뢰 입력으로 가정
- 회원가입 시 기존 사용자 email backfill 정책

## 7. 진행 순서

1. 본 문서 승인
2. Phase 1 → 2 → 3 → 4 (각 단계마다 테스트 우선 작성, RED → GREEN)
3. Phase 5 통합 테스트 일괄 검증 (`pytest apps/users/`)
4. Phase 6 i18n
5. 사용자 검증 후 커밋 (사용자 직접 실행, Claude는 명령 블록만 제시)
