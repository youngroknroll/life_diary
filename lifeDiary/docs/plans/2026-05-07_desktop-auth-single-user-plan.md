# Desktop Auth — Single Local User Plan

**Date**: 2026-05-07
**Goal**: 데스크톱 앱은 개인 단독 사용 → 로그인/회원가입 없이 자동 진입
**Mode**: Option A (Single Local User Auto-Login)

---

## 1. Decisions

| # | 항목 | 결정 |
|---|------|------|
| A | 인증 모델 | **단일 로컬 유저 자동 로그인** |
| B | 회원가입/로그인/패스워드 찾기 페이지 | **차단만** (코드 삭제 X, URL 직접 접근 시 홈으로 redirect) |
| C | 프로필 페이지 | **유지** (display name, 향후 라이선스 키 입력란 등) |
| D | 로그아웃 버튼 | **데스크톱 모드에서 숨김** |
| E | 마스터 패스워드 | **사용 안 함** (단순성 우선, DB 암호화는 Phase 3에서 별도 검토) |
| F | local user 패스워드 | 랜덤 생성 후 폐기 (어디에도 저장 안 함) |

### Why each decision

- **A. 단일 로컬 유저**: 데스크톱 = 본인 PC = 이미 OS 단에서 보안 경계가 있음. Day One/Bear/Obsidian 모두 로컬 사용 시 무로그인.
- **B. 차단만**: Phase 3 수익화 시 회원가입 페이지를 "라이선스 키 입력 페이지"로 재활용 가능. 코드 삭제하면 재사용 비용 ↑.
- **C. 프로필 유지**: Phase 3에서 라이선스 키, 동기화 설정 등 추가될 자연스러운 위치.
- **D. 로그아웃 숨김**: 단일 유저 환경에서 로그아웃은 의미 없음. 클릭 시 다시 자동 로그인되어 UX 혼란.
- **E. 마스터 패스워드 미적용**: 첫 출시 단순성 우선. 향후 "Pro 보안 옵션"으로 추가 검토 가능.
- **F. 패스워드 폐기**: local user는 ORM으로만 식별. 패스워드 입력 자체가 없는 흐름이라 저장 불필요.

---

## 2. Architecture

### 2.1 흐름도

```
[launcher.py 실행]
   ├─ migrate
   ├─ ensure_local_user (없으면 생성)
   └─ waitress + pywebview 기동
        ↓
[브라우저 요청 도착]
   ↓
[DesktopAuthMiddleware]
   ├─ 차단 경로 (/login, /signup, /password-reset, /account-recovery)
   │     → "/" 로 redirect
   └─ 익명 요청 → local user로 강제 로그인
        ↓
[일반 view 처리]
```

### 2.2 컴포넌트

#### `desktop/middleware.py` (NEW)

```python
class DesktopAuthMiddleware:
    """단일 로컬 유저 자동 로그인 + 인증 페이지 차단."""

    BLOCKED_PREFIXES = (
        "/login", "/signup", "/password-reset",
        "/account-recovery", "/logout",
    )
    LOCAL_USERNAME = "local"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in self.BLOCKED_PREFIXES):
            from django.shortcuts import redirect
            return redirect("/")

        if not request.user.is_authenticated:
            from django.contrib.auth import get_user_model, login
            User = get_user_model()
            user = User.objects.filter(username=self.LOCAL_USERNAME).first()
            if user is not None:
                login(
                    request,
                    user,
                    backend="django.contrib.auth.backends.ModelBackend",
                )

        return self.get_response(request)
```

#### `desktop/bootstrap.py` (NEW) — local user 생성

```python
def ensure_local_user() -> None:
    """첫 실행 시 'local' 유저를 생성. 이미 있으면 no-op."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if User.objects.filter(username="local").exists():
        return
    User.objects.create_user(
        username="local",
        password=secrets.token_urlsafe(32),  # 폐기, 어디에도 저장 안 함
    )
```

#### `desktop/launcher.py` (UPDATE)

`migrate` 직후 `ensure_local_user()` 호출 추가.

#### `lifeDiary/settings/desktop.py` (UPDATE)

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "desktop.middleware.DesktopAuthMiddleware",  # NEW (auth 미들웨어 뒤)
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

LOGIN_URL = "/"  # @login_required 데코레이터가 redirect할 곳을 홈으로
```

⚠️ 미들웨어 순서: `AuthenticationMiddleware` 다음에 `DesktopAuthMiddleware`. 그래야 `request.user`가 이미 채워진 상태에서 익명 여부 판단 가능.

#### 템플릿 분기 (UPDATE)

로그아웃 버튼 등 인증 UI 숨김:

```django
{% if not desktop_mode %}
  <a href="{% url 'logout' %}">로그아웃</a>
{% endif %}
```

`desktop_mode` 컨텍스트 프로세서 추가 (`desktop.context_processors.desktop_flags`):

```python
def desktop_flags(request):
    return {"desktop_mode": "lifeDiary.settings.desktop" == os.environ.get("DJANGO_SETTINGS_MODULE")}
```

`desktop.py`의 `TEMPLATES.OPTIONS.context_processors`에 등록.

---

## 3. Web App Impact

| 영향 항목 | 결과 |
|---|---|
| `dev.py` / `prod.py` 동작 | **무영향** (미들웨어/컨텍스트 프로세서는 desktop.py에만 등록) |
| 기존 회원가입/로그인 view/template/url | **그대로 유지** |
| 기존 테스트 | **무영향** (settings 분리) |
| 마이그레이션 | **불필요** (스키마 변경 없음) |

데스크톱 모드는 **순수하게 desktop.py settings + desktop/ 패키지 안에서만 작동**.

---

## 4. Phase 3 Compatibility

향후 수익화 (Open Core) 도입 시:

1. **회원가입 페이지 재활용**: `/signup` 대신 `/upgrade`로 alias → 라이선스 키 입력 + 클라우드 동기화 활성화
2. **local user 프로필 확장**: `License` 모델 추가, `OneToOneField(User)` 연결
3. **Pro 식별자**: 이메일 X, **라이선스 키만**으로 식별 (Lemon Squeezy 모델과 일치)

본 plan은 Phase 3 모델과 충돌 없음.

---

## 5. Edge Cases

| 상황 | 처리 |
|---|---|
| 어드민 통해 local user 삭제됨 | 다음 실행 시 `ensure_local_user`가 재생성. 단, **기존 일기 데이터의 author FK가 끊김** → 미들웨어에서 데이터 마이그레이션 필요 (out of scope, 어드민 접근 자체가 비정상 경로) |
| local user 외에 추가 유저가 DB에 있음 | 무시 (관리자가 의도적으로 만든 경우. local user만 자동 로그인) |
| 어드민 페이지 접근 | 차단 미해당 → 정상 동작. 단, `local` 유저는 staff/superuser X → admin 진입 시 권한 거부. 디버깅 필요 시 Django shell에서 `is_superuser=True` 부여 |
| 로그아웃 URL 직접 호출 | 차단 prefix에 포함됨 → 홈으로 redirect (실제 로그아웃 처리 안 됨) |

---

## 6. Verification

### 6.1 데스크톱 모드

- [ ] 첫 실행 → 회원가입/로그인 화면 없이 일기 페이지 바로 진입
- [ ] DB에 `User.objects.filter(username="local").count() == 1`
- [ ] `/login` 접근 → "/" redirect
- [ ] `/signup` 접근 → "/" redirect
- [ ] `/password-reset` 접근 → "/" redirect
- [ ] `/account-recovery` 접근 → "/" redirect
- [ ] 종료 후 재실행 → 데이터 + 자동 로그인 유지
- [ ] 템플릿 상단/사이드 메뉴에 "로그아웃" 버튼 없음
- [ ] "프로필" 메뉴는 표시됨

### 6.2 웹 모드 회귀 (Red-Green)

- [ ] `python manage.py runserver` (dev) → `/login` 정상 동작
- [ ] dev 모드 회원가입 → 로그인 → 기존 흐름 그대로
- [ ] pytest 전체 통과 (settings 분리 영향 없음 확인)

---

## 7. Implementation Order

1. `desktop/__init__.py` (패키지 마커, 빈 파일)
2. `desktop/bootstrap.py` (`ensure_local_user`)
3. `desktop/middleware.py` (`DesktopAuthMiddleware`)
4. `desktop/context_processors.py` (`desktop_flags`)
5. `lifeDiary/settings/desktop.py` 업데이트 (미들웨어 + context_processor + LOGIN_URL)
6. `desktop/launcher.py` 업데이트 (migrate 후 `ensure_local_user` 호출)
7. 템플릿 분기 (로그아웃/회원가입 링크 숨김) — 영향 받는 base 템플릿 식별 후 최소 수정
8. 데스크톱 실행 검증 (§6.1)
9. 웹 회귀 검증 (§6.2)

---

## 8. Out of Scope

- DB 암호화 (마스터 패스워드, SQLCipher 등)
- 다중 로컬 프로필 (가족 공유 PC 시나리오)
- 어드민 페이지 차단 (개발자 디버깅 용도로 유지)
- 로그아웃 URL의 view-level 비활성화 (미들웨어 redirect로 충분)

---

## 9. Approval Required

- [ ] 본 plan 승인
- [ ] 구현 진행

---

## 10. Linked Plans

- `2026-05-03_desktop-app-packaging-plan.md` — Phase 0 빌드 (선행)
- `2026-05-06_distribution-and-monetization-plan.md` — Phase 3 수익화 (라이선스 키 모델 호환)
- `2026-05-01_account-recovery-plan.md` — 웹 모드에서만 의미 있음. 데스크톱에서는 차단됨
