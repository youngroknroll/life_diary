# Desktop App Packaging Plan

**Date**: 2026-05-03
**Stack**: Django + SQLite + pywebview + PyInstaller + waitress
**Goal**: 기존 Django 웹앱을 macOS `.app` / Windows `.exe` 데스크톱 앱으로 배포

---

## 1. Decisions

| # | 항목 | 결정 |
|---|------|------|
| A | WSGI 서버 | **waitress** (크로스플랫폼, 안정) |
| B | 빌드 타겟 | macOS + Windows (각 OS에서 별도 빌드, 크로스컴파일 불가) |
| C | 초기 DB | 첫 실행 시 빈 DB 생성 + `migrate` 자동 실행 |
| D | django-axes | **비활성** (단일 사용자 로컬앱, 본인 잠금 위험) |
| E | 디렉토리 | `desktop/` 하위로 격리 (launcher + spec + README) |

### Why each decision

- **waitress**: `wsgiref`는 단일 스레드/저성능, `gunicorn`은 Windows 미지원. waitress는 두 OS 모두 동작.
- **각 OS에서 빌드**: PyInstaller는 크로스컴파일 미지원. macOS 빌드는 macOS에서, Windows 빌드는 Windows에서 수행.
- **빈 DB**: 개발용 `db.sqlite3`에는 더미 사용자/일기 데이터가 섞여 있을 수 있어 시드로 부적합. 사용자 데이터 디렉토리에 깨끗한 DB 생성.
- **axes 비활성**: 로컬앱은 `127.0.0.1`만 바인딩 → 외부 brute force 불가능. 본인 비번 5회 오타 시 1시간 잠김 UX는 최악.
- **`desktop/` 격리**: 데스크톱 빌드 산출물이 웹앱 코드와 섞이지 않도록 분리.

---

## 2. File Layout

```
lifeDiary/
├── desktop/                              # NEW
│   ├── launcher.py                       # 진입점 (waitress + pywebview)
│   ├── lifediary.spec                    # PyInstaller 스펙
│   └── README.md                         # 빌드/실행 가이드
├── lifeDiary/settings/
│   └── desktop.py                        # NEW (Django settings — 관례상 settings/ 내부)
├── requirements-desktop.txt              # NEW
└── .gitignore                            # UPDATE
```

### 산출물 (gitignore)
```
build/        # PyInstaller 중간 산출물
dist/         # 최종 .app / .exe / 단일 실행 파일
*.spec.bak
```

---

## 3. Component Design

### 3.1 `requirements-desktop.txt`

```
pywebview>=5.0
waitress>=3.0
pyinstaller>=6.0
```

런타임에 필요한 건 `pywebview`, `waitress`. `pyinstaller`는 빌드 도구 (런타임 미사용).

### 3.2 `lifeDiary/settings/desktop.py`

기반: `dev.py` 복사 후 차이점만 변경.

**변경 포인트**:
- `DEBUG = False`
- `ALLOWED_HOSTS = ["127.0.0.1", "localhost"]`
- `SECRET_KEY`: 사용자 데이터 디렉토리에서 로드, 없으면 생성·저장 (`secrets.token_urlsafe(50)`)
- `DATABASES["default"]["NAME"]`: `<user_data_dir>/db.sqlite3`
- `STATIC_ROOT`: PyInstaller 환경(`sys._MEIPASS`)이면 `_MEIPASS/staticfiles`, 아니면 `BASE_DIR/staticfiles`
- `MIDDLEWARE`: `axes.middleware.AxesMiddleware` 제외
- `AUTHENTICATION_BACKENDS`: `axes.backends.AxesStandaloneBackend` 제외 (`ModelBackend`만 유지)
- `INSTALLED_APPS`: `"axes"` 유지 (기존 마이그레이션 호환, 빈 DB라도 테이블은 만들어둠)
- `EMAIL_BACKEND`: console (로컬앱은 메일 발송 불가)
- `CACHES["default"]["LOCATION"]`: `<user_data_dir>/.cache`

**사용자 데이터 디렉토리** (OS별):
- macOS: `~/Library/Application Support/LifeDiary/`
- Windows: `%APPDATA%\LifeDiary\`
- Linux: `~/.local/share/LifeDiary/` (테스트용)

`platformdirs` 라이브러리 추가 vs `pathlib`로 직접 처리 → 직접 처리 (의존성 최소화):

```python
def _user_data_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    path = base / "LifeDiary"
    path.mkdir(parents=True, exist_ok=True)
    return path
```

### 3.3 `desktop/launcher.py`

**책임**:
1. `DJANGO_SETTINGS_MODULE` 설정
2. `sys.path`에 프로젝트 루트 추가 (PyInstaller 환경 대응)
3. `django.setup()` → `call_command("migrate", "--noinput")`
4. 빈 포트 탐색 (`socket` 모듈)
5. waitress 서버를 데몬 스레드로 기동
6. 헬스체크 (포트 응답 대기, 최대 10초)
7. pywebview 창 생성 → `webview.start()`
8. 창 종료 시 정상 exit (waitress는 데몬 스레드라 자동 종료)

**의사 코드**:
```python
import os, sys, socket, threading, time
from pathlib import Path

# PyInstaller bundle: sys._MEIPASS = 임시 추출 디렉토리
if hasattr(sys, "_MEIPASS"):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lifeDiary.settings.desktop")

import django
django.setup()

from django.core.management import call_command
call_command("migrate", "--noinput", verbosity=0)

from django.core.wsgi import get_wsgi_application
from waitress import serve
import webview

def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False

def main() -> None:
    app = get_wsgi_application()
    port = find_free_port()
    thread = threading.Thread(
        target=serve,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": port, "threads": 4, "_quiet": True},
        daemon=True,
    )
    thread.start()

    if not wait_for_server(port):
        sys.exit("Server failed to start within 10s")

    webview.create_window(
        "LifeDiary",
        f"http://127.0.0.1:{port}",
        width=1200,
        height=800,
    )
    webview.start()

if __name__ == "__main__":
    main()
```

### 3.4 `desktop/lifediary.spec`

PyInstaller 스펙 (Python 코드 형식). 핵심:

```python
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH).parent  # lifeDiary 프로젝트 루트

datas = [
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "locale"), "locale"),
    (str(ROOT / "staticfiles"), "staticfiles"),
]
# 각 앱의 templates, migrations 포함
for app in ["core", "dashboard", "stats", "tags", "users"]:
    datas.append((str(ROOT / "apps" / app / "templates"), f"apps/{app}/templates"))
    datas.append((str(ROOT / "apps" / app / "migrations"), f"apps/{app}/migrations"))

hiddenimports = [
    "django.contrib.admin", "django.contrib.auth",
    "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles",
    "axes", "axes.apps", "whitenoise",
    "apps.core", "apps.dashboard", "apps.stats", "apps.tags", "apps.users",
    # 마이그레이션 동적 import 대응
    "apps.core.migrations", "apps.dashboard.migrations",
    "apps.stats.migrations", "apps.tags.migrations", "apps.users.migrations",
]

a = Analysis(
    [str(ROOT / "desktop" / "launcher.py")],
    pathex=[str(ROOT)],
    datas=datas,
    hiddenimports=hiddenimports,
    ...
)
...
exe = EXE(..., name="LifeDiary", console=False, ...)

# macOS: BUNDLE 추가
import sys
if sys.platform == "darwin":
    app = BUNDLE(coll, name="LifeDiary.app", bundle_identifier="com.knou.lifediary")
```

`console=False` = `--windowed`.

### 3.5 빌드 명령

```bash
# 사전: 정적 파일 수집 (settings는 dev로도 가능, STATIC_ROOT는 동일)
python manage.py collectstatic --settings=lifeDiary.settings.desktop --noinput

# 빌드
pyinstaller desktop/lifediary.spec --clean

# 산출물
# macOS: dist/LifeDiary.app
# Windows: dist/LifeDiary/LifeDiary.exe (one-dir 모드 권장)
```

---

## 4. Risks & Mitigations

| 리스크 | 대응 |
|--------|------|
| PyInstaller 누락 import (Django 동적 로드) | `hiddenimports`에 모든 앱과 contrib 명시 |
| 첫 실행 시 마이그레이션 실패 | `call_command("migrate")` 실패 시 에러 다이얼로그 (pywebview 미실행 상태이므로 stderr + 종료) |
| Windows: WebView2 런타임 부재 | README에 "Windows 10/11은 기본 탑재, Windows 8 이하 미지원" 명시 |
| macOS: Gatekeeper 차단 (서명 없음) | 자체 서명 또는 사용자에게 "우클릭 > 열기" 안내 |
| SQLite 동시성 (단일 사용자라 무관) | 영향 없음 |
| 정적 파일 manifest (whitenoise CompressedManifestStaticFilesStorage) | `collectstatic` 빌드 단계에서 manifest 생성, 번들 포함 |
| SECRET_KEY 평문 저장 | 사용자 디렉토리 권한(0700) 설정 검토. 단일 사용자 로컬이라 위험도 낮음 |
| pywebview 의존성 (macOS: pyobjc, Win: pythonnet) | `pip install pywebview[qt]` 또는 기본(Cocoa/EdgeChromium) — 일단 기본으로 |

---

## 5. Verification

### 5.1 개발 환경 실행 (PyInstaller 없이)
```bash
conda activate knou-life-diary
pip install -r requirements-desktop.txt
python desktop/launcher.py
```
→ pywebview 창이 뜨고 LifeDiary UI 표시되는지 확인.

### 5.2 macOS 빌드 검증
```bash
python manage.py collectstatic --settings=lifeDiary.settings.desktop --noinput
pyinstaller desktop/lifediary.spec --clean
open dist/LifeDiary.app
```
체크리스트:
- [ ] 첫 실행 시 `~/Library/Application Support/LifeDiary/db.sqlite3` 생성됨
- [ ] 회원가입 → 일기 작성 → 저장 동작
- [ ] 종료 후 재실행 시 데이터 유지
- [ ] 정적 파일 (CSS/JS) 정상 로드

### 5.3 Windows 빌드 검증 (Windows 환경에서)
- [ ] `%APPDATA%\LifeDiary\db.sqlite3` 생성됨
- [ ] `LifeDiary.exe` 더블클릭 실행
- [ ] WebView2 정상 동작

### 5.4 Red-Green (회귀 방지)
- DB 경로 분리 검증: `desktop` settings로 실행 후 프로젝트 루트의 `db.sqlite3`에 변동 없음을 확인
- axes 미들웨어 비활성 확인: 로그인 5회 실패해도 잠기지 않음

---

## 6. Implementation Order

1. **`requirements-desktop.txt`** 작성
2. **`lifeDiary/settings/desktop.py`** 작성
3. **`desktop/launcher.py`** 작성
4. **개발 환경 실행 테스트** (`python desktop/launcher.py`) — pywebview 창 동작 확인
5. **`desktop/lifediary.spec`** 작성
6. **macOS 빌드 + 실행 검증**
7. **`desktop/README.md`** 작성 (빌드/배포 가이드)
8. **`.gitignore`** 업데이트 (`build/`, `dist/`)
9. (별도 환경) Windows 빌드 검증

각 단계에서 문제 발생 시 다음 단계 진입 금지.

---

## 7. Out of Scope

- 코드 서명 (Apple Developer ID, Windows Authenticode) — 추후 배포 단계
- 자동 업데이트 (Sparkle, electron-updater 류)
- 설치 마법사 (DMG 커스터마이징, NSIS) — 일단 raw `.app` / `.exe`
- 다국어 인스톨러
- 네이티브 메뉴바 통합

---

## 8. Approval Required

- [ ] Plan 승인
- [ ] 구현 단계 1~4 진행 (개발 환경 동작 확인까지)
- [ ] 단계 5~6 진행 (PyInstaller 빌드)
