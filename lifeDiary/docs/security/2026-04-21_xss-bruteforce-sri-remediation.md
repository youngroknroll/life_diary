# 2026-04-21 보안 취약점 수정 로그 (XSS · 브루트포스 · CDN SRI)

> 실행일: 2026-04-21
> 담당: Yeongrok Song
> 대상: 저장형 XSS, 로그인 브루트포스, CDN 공급망 방어
> 결과: 3건 전부 수정 완료, 테스트 55 passed / 0 failed

---

## 요약

코드 검토를 통해 확인된 3가지 보안 취약점을 수정했다.

| # | 항목 | 위험도 | 상태 |
|---|------|--------|------|
| 1 | 저장형 XSS (통계 페이지) | 높음 | 완료 |
| 2 | 로그인 브루트포스 방어 없음 | 중간 | 완료 |
| 3 | CDN SRI Hash 누락 | 중간 | 완료 |

---

## 검토 배경

초기 보안 수준 평가는 "기본 방어는 갖췄지만 운영 기준 중간 이하"였다.
특히 민감한 사용자 세션을 다루는 서비스 기준으로는 안전하지 않은 상태로 판단했다.

### 발견 경로

1. `apps/core/utils.py:27` — `json.dumps()` 결과를 그대로 문자열로 반환
2. `apps/stats/logic.py:45` — 사용자 입력(태그명)이 섞인 JSON 생성
3. `apps/stats/templates/stats/index.html:340-347` — 위 JSON을 `|safe`로 `<script>` 내부에 직접 삽입
4. `apps/users/views.py:81` — `AuthenticationForm`만 사용, 로그인 실패 제한 없음
5. `templates/base.html:29-37` — Chart.js, htmx, Alpine.js를 외부 CDN에서 `integrity` 없이 로드

---

## Phase 1 — 저장형 XSS 수정 (높음)

### 원인

통계 페이지에서 태그명 등 사용자 입력이 포함된 JSON을 `|safe`로 스크립트 블록에 삽입.
태그명에 `</script>` 또는 `<!--` 등의 문자가 들어가면 스크립트 컨텍스트 탈출 가능.

### 수정 전

```html
<script id="stats-data" type="application/json">
{
    "daily": {{ daily_stats_json|safe }},
    "weekly": {{ weekly_stats_json|safe }},
    "monthly": {{ monthly_stats_json|safe }},
    "tagAnalysis": {{ tag_analysis_json|safe }}
}
</script>
```

### 수정 후

Django 내장 `json_script` 필터는 `</script>`, `<!--` 등 위험 문자를 자동으로 유니코드 이스케이프 처리한다.

```html
{{ daily_stats_json|json_script:"daily-stats-data" }}
{{ weekly_stats_json|json_script:"weekly-stats-data" }}
{{ monthly_stats_json|json_script:"monthly-stats-data" }}
{{ tag_analysis_json|json_script:"tag-analysis-data" }}
```

JS 파싱 방식도 변경:

```javascript
function parseJsonScript(id) {
    const el = document.getElementById(id);
    if (!el) { console.error(id + ' 요소를 찾을 수 없습니다.'); return null; }
    try { return JSON.parse(el.textContent); }
    catch (e) { console.error(id + ' 파싱 오류:', e); return null; }
}

const daily = parseJsonScript('daily-stats-data');
const weekly = parseJsonScript('weekly-stats-data');
const monthly = parseJsonScript('monthly-stats-data');
const tagAnalysis = parseJsonScript('tag-analysis-data');
```

### 변경 파일

- `apps/stats/templates/stats/index.html` — `|safe` 블록 제거, `json_script` 4개로 교체
- `apps/stats/static/stats/js/stats.js` — 단일 객체 파싱 → 개별 id 파싱

---

## Phase 2 — 브루트포스 방어 (중간)

### 원인

`views.py:81`의 로그인이 Django 기본 `AuthenticationForm`만 사용.
실패 횟수 제한, 지연, IP/계정별 잠금, CAPTCHA가 모두 없음.
비밀번호 정책은 있지만 온라인 브루트포스/크리덴셜 스터핑 방어는 별개 문제.

### 선택: `django-axes`

외부 패키지 없이 구현 시 코드 복잡도가 높아진다.
`django-axes`는 Django 표준 미들웨어로 통합되며 DB 기반 실패 횟수 추적 제공.

### 설정

`requirements.txt`:
```
django-axes==7.0.1
```

`lifeDiary/settings/dev.py`:
```python
INSTALLED_APPS = [..., "axes"]

MIDDLEWARE = [..., "axes.middleware.AxesMiddleware"]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AXES_FAILURE_LIMIT = 5      # 5회 실패 시 잠금
AXES_COOLOFF_TIME = 1       # 1시간 후 해제
AXES_RESET_ON_SUCCESS = True
```

### 마이그레이션

```bash
python manage.py migrate axes
```

axes가 생성한 테이블:
- `axes_accessattempt` — 실패 시도 기록
- `axes_accesslog` — 접근 로그
- `axes_accessfailurelog` — 실패 상세

### 트러블슈팅

**이슈 1: conda 환경 누락**

프로젝트가 conda 환경(`knou-life-diary`)을 사용하는데 `.venv` 환경에만 `pip install`하여 `ModuleNotFoundError: No module named 'axes'` 발생.

해결: conda 환경에 별도 설치
```bash
conda run -n knou-life-diary pip install django-axes==7.0.1
```

**이슈 2: 테스트 실패 (6건)**

`AxesStandaloneBackend`는 `authenticate()` 호출 시 `request` 객체 필수.
`self.client.login()`은 내부적으로 request 없이 호출되어 `AxesBackendRequestParameterRequired` 예외 발생.

해결: `conftest.py`에서 테스트 환경 시 axes 비활성화
```python
settings.AXES_ENABLED = False
settings.AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
```

### 변경 파일

- `requirements.txt` — `django-axes==7.0.1` 추가
- `lifeDiary/settings/dev.py` — axes 설정 블록 추가
- `conftest.py` — 테스트 환경 axes 비활성화

---

## Phase 3 — CDN SRI Hash 추가 (중간)

### 원인

`base.html`에서 Chart.js, chartjs-adapter-date-fns, htmx, Alpine.js를 외부 CDN에서 로드하지만 `integrity` 속성 없음.
특히 Alpine.js는 `@3.x.x` 부동 버전으로 공급망 공격에 추가로 취약.

### 수정 전

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"
        crossorigin="anonymous"></script>
<script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"
        crossorigin="anonymous"></script>
```

### 수정 후

| 라이브러리 | 버전 변경 | integrity |
|-----------|---------|-----------|
| Chart.js | 3.9.1 (유지) | `sha384-9MhbyIRcBVQiiC7FSd7T38oJNj2Zh+EfxS7/vjhBi4OOT78NlHSnzM31EZRWR1LZ` |
| chartjs-adapter-date-fns | 2.0.0 (유지) | `sha384-Crp3O/636k0LjUK6uxSF2i5herKUb8UIA16lRYz/PGAlkuavAVGFH5v2YlBayW8d` |
| htmx | 1.9.12 (유지) | `sha384-ujb1lZYygJmzgSwoxRggbCHcjc0rB2XoQrxeTUQyRjrOnlCoYta87iKBWq3EsdM2` |
| Alpine.js | `@3.x.x` → **`@3.14.9`** | `sha384-9Ax3MmS9AClxJyd5/zafcXXjxmwFhZCdsT6HJoJjarvCaAkJlk5QDzjLJm+Wdx5F` |

SRI hash 생성 방법:
```bash
curl -sf <url> | openssl dgst -sha384 -binary | openssl base64 -A
```

### 변경 파일

- `templates/base.html` — 4개 스크립트 태그에 `integrity` 추가, Alpine 버전 고정

---

## 변경 파일 총괄

| 파일 | Phase | 변경 유형 |
|------|-------|----------|
| `apps/stats/templates/stats/index.html` | 1 | `|safe` → `json_script` |
| `apps/stats/static/stats/js/stats.js` | 1 | 데이터 파싱 방식 변경 |
| `requirements.txt` | 2 | `django-axes==7.0.1` 추가 |
| `lifeDiary/settings/dev.py` | 2 | axes 설정 추가 |
| `conftest.py` | 2 | 테스트 환경 axes 비활성화 |
| `templates/base.html` | 3 | SRI hash 4개 추가, Alpine 버전 고정 |

**총 6개 파일**

---

## 검증 증거

```
$ python manage.py check
System check identified no issues (0 silenced).

$ pytest
55 passed in 5.89s
```

---

## 남은 보안 과제 (다음 사이클)

이번 작업으로 해결되지 않은 항목:

1. **CSP (Content-Security-Policy) 헤더 없음** — 향후 `django-csp` 도입 검토
2. **`settings/prod.py` 미검토** — 운영 환경 보안 헤더 (HSTS, SECURE_SSL_REDIRECT 등) 점검 필요
3. **로그인 실패 알림 없음** — 계정 탈취 시도 로깅/알림 미구현
4. **세션 보안 설정** — `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE` 명시 필요
5. **CSRF 쿠키 보안** — `CSRF_COOKIE_SECURE`, `CSRF_COOKIE_HTTPONLY` 명시 필요
6. **비밀번호 정책 강화** — 최소 길이, 특수문자 요구 등 검토

---

## 참고

- Django 공식 `json_script` 필터: https://docs.djangoproject.com/en/5.2/ref/templates/builtins/#json-script
- django-axes 문서: https://django-axes.readthedocs.io/
- SRI 스펙 (W3C): https://www.w3.org/TR/SRI/
- 선행 계획 문서: `prompt_plan.md`
