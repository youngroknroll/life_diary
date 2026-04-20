# 보안 취약점 수정 계획

**작성일**: 2026-04-21  
**우선순위**: 높음 → 중간 → 중간  
**대상 파일**: 4개

---

## 요구사항 요약

코드 검토를 통해 확인된 3가지 보안 취약점을 수정한다.

1. 저장형 XSS — `stats/index.html` `|safe` + 비이스케이프 JSON
2. 브루트포스 방어 없음 — 로그인 실패 횟수 제한 없음
3. CDN SRI 누락 — Chart.js, htmx, Alpine.js 무결성 해시 없음

---

## Phase 1 — 저장형 XSS 수정 (높음)

**대상 파일**
- `apps/stats/templates/stats/index.html:340-347`
- `apps/core/utils.py:27` (필요 시)

**현재 코드 (취약)**
```html
<script id="stats-data" type="application/json">
{
    "daily": {{ daily_stats_json|safe }},
    ...
}
</script>
```

**수정 방법: `json_script` 태그 사용**

Django 내장 `json_script` 필터는 `</script>`, `<!--` 등 위험 문자를 자동으로 유니코드 이스케이프 처리한다.

```html
{{ daily_stats_json|json_script:"daily-stats-data" }}
{{ weekly_stats_json|json_script:"weekly-stats-data" }}
{{ monthly_stats_json|json_script:"monthly-stats-data" }}
{{ tag_analysis_json|json_script:"tag-analysis-data" }}
```

JS에서 읽는 방법:
```javascript
const daily = JSON.parse(document.getElementById('daily-stats-data').textContent);
```

**변경 내용**
- `index.html:340-347` — `<script type="application/json">` 블록 제거, `json_script` 4개로 교체
- `stats/js/stats.js` — `stats-data` 단일 객체 파싱 → 개별 id 파싱으로 변경
- `utils.py:serialize_for_js` — context에서 JSON 문자열 대신 원본 dict 전달 가능 (선택)

**리스크**: stats.js의 데이터 접근 방식 변경 필요 → stats.js 확인 후 수정

> ✅ **완료** (2026-04-21)  
> `index.html` `|safe` 블록 → `json_script` 4개로 교체.  
> `stats.js` 단일 파싱 → `parseJsonScript(id)` 헬퍼로 개별 파싱 변경.

---

## Phase 2 — 브루트포스 방어 추가 (중간)

**대상 파일**
- `apps/users/views.py:81-102`
- `requirements.txt`

**방법: `django-axes` 패키지 사용**

외부 패키지 없이 구현하면 코드가 복잡해진다. `django-axes`는 Django 표준 미들웨어로 통합되며, DB 기반 실패 횟수 추적을 제공한다.

**설치**
```
django-axes==7.0.1
```

**settings.py 추가**
```python
INSTALLED_APPS = [
    ...
    'axes',
]

MIDDLEWARE = [
    ...
    'axes.middleware.AxesMiddleware',  # 마지막에 추가
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# 5회 실패 시 1시간 잠금
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_CALLABLE = None  # 기본 403 응답
AXES_RESET_ON_SUCCESS = True
```

**마이그레이션**
```bash
python manage.py migrate
```

**리스크**: `django-axes`는 DB 테이블을 생성하므로 마이그레이션 필요. 개발 환경에서 사전 테스트 권장.

> ✅ **완료** (2026-04-21)  
> `requirements.txt`, `settings/dev.py` 수정 및 마이그레이션 완료.  
> **트러블슈팅**: conda 환경(`knou-life-diary`)에 별도 설치 필요했음 → `conda run -n knou-life-diary pip install django-axes==7.0.1`  
> **테스트 대응**: `conftest.py`에 `AXES_ENABLED = False` 추가 — 테스트 환경에서 axes 비활성화.

---

## Phase 3 — CDN SRI Hash 추가 (중간)

**대상 파일**
- `templates/base.html:30-37`

**현재 누락 항목 및 계산된 SRI Hash**

| 라이브러리 | 버전 | integrity |
|-----------|------|-----------|
| Chart.js | 3.9.1 | `sha384-9MhbyIRcBVQiiC7FSd7T38oJNj2Zh+EfxS7/vjhBi4OOT78NlHSnzM31EZRWR1LZ` |
| chartjs-adapter-date-fns | 2.0.0 | `sha384-Crp3O/636k0LjUK6uxSF2i5herKUb8UIA16lRYz/PGAlkuavAVGFH5v2YlBayW8d` |
| htmx | 1.9.12 | `sha384-ujb1lZYygJmzgSwoxRggbCHcjc0rB2XoQrxeTUQyRjrOnlCoYta87iKBWq3EsdM2` |
| Alpine.js | **3.14.9** (고정) | `sha384-9Ax3MmS9AClxJyd5/zafcXXjxmwFhZCdsT6HJoJjarvCaAkJlk5QDzjLJm+Wdx5F` |

**Alpine.js 버전 변경**: `@3.x.x` (부동) → `@3.14.9` (고정)

**수정 후 예시**
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"
        integrity="sha384-9MhbyIRcBVQiiC7FSd7T38oJNj2Zh+EfxS7/vjhBi4OOT78NlHSnzM31EZRWR1LZ"
        crossorigin="anonymous"></script>
```

**리스크**: 없음. 기존 동작에 영향 없이 integrity 속성만 추가.

> ✅ **완료** (2026-04-21)  
> `base.html` Chart.js, chartjs-adapter, htmx, Alpine.js 4개에 integrity 추가.  
> Alpine `@3.x.x` → `@3.14.9` 버전 고정.

---

## 실행 순서

```
Phase 1 (XSS)       → stats.js 파싱 방식 확인 후 template + JS 수정
Phase 2 (브루트포스) → requirements.txt 추가 → settings.py 설정 → migrate
Phase 3 (SRI)       → base.html 4개 스크립트 태그 수정
```

## 변경 파일 목록

| 파일 | Phase | 변경 유형 |
|------|-------|----------|
| `apps/stats/templates/stats/index.html` | 1 | template 수정 |
| `apps/stats/static/stats/js/stats.js` | 1 | JS 파싱 수정 |
| `requirements.txt` | 2 | 패키지 추가 |
| `lifeDiary/settings/dev.py` | 2 | 설정 추가 |
| `conftest.py` | 2 | 테스트 환경 axes 비활성화 |
| `templates/base.html` | 3 | SRI hash 추가 |

총 6개 파일

---

## 최종 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
pytest               → 55 passed, 0 failed
```

**완료일**: 2026-04-21
