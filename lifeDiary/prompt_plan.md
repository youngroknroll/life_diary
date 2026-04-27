# 한→영 i18n + 코드+파라미터 아키텍처 구현 계획

**작성일**: 2026-04-27
**대상**: 전체 앱 (`apps/core`, `apps/dashboard`, `apps/tags`, `apps/users`, `apps/stats`)
**복잡도**: HIGH
**총 예상**: 22–25h

---

## 확정 사항

- **범위**: 이번 작업은 ko→en 만. 일본어/기타는 구조만 준비 (실제 번역 X)
- **반환 타입**: 사용자 메시지는 모두 `LocalizableMessage` (code + params + severity)
- **렌더링**: Django 템플릿 (현재) + DRF Serializer (향후 B 하이브리드 대비)
- **확장성 목표**: 일본어 추가 시 `.po` 파일 + 톤 가이드만 추가, 코드 변경 0
- **JS 전략**: Django `JavaScriptCatalog` 뷰 (단일 .po 소스)
- **Phase 0 완료 (2026-04-18)**: i18n 인프라(LANGUAGES/LOCALE_PATHS/LocaleMiddleware/언어 토글) 설치됨

---

## 설계 표준

### 1. 표준 타입 (`apps/core/messages.py`)

```python
from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["positive", "info", "warning", "error"]

@dataclass(frozen=True)
class LocalizableMessage:
    code: str
    params: dict = field(default_factory=dict)
    severity: Severity = "info"

    def to_dict(self) -> dict:
        return {"code": self.code, "params": self.params, "severity": self.severity}
```

### 2. 카탈로그 위치

- 앱별 `messages.py`에 모음 (전역 카탈로그 X)
- 코드 네임스페이스: `{app}.{domain}.{action}` 예: `stats.feedback.goal_achieved`

```python
# apps/stats/messages.py
from django.utils.translation import gettext_lazy as _

CATALOG = {
    "stats.feedback.goal_achieved": _(
        "%(period)s '%(name)s' 목표(%(hours)s시간)를 이미 달성했습니다!"
    ),
    ...
}

PERIOD_LABELS = {
    "daily": _("오늘"),
    "weekly": _("이번주"),
    "monthly": _("이번 달"),
}
```

### 3. 렌더링 헬퍼 (`apps/core/templatetags/i18n_messages.py`)

```python
@register.simple_tag
def render_message(msg):
    code = msg["code"] if isinstance(msg, dict) else msg.code
    params = dict(msg["params"] if isinstance(msg, dict) else msg.params)
    template = _resolve_template(code)
    params = _resolve_enum_params(params)
    return template % params
```

### 4. 비즈니스 로직 변경 패턴

```python
# Before
feedback.append(_fb(f"{period_label} '{goal.tag.name}' 목표(...)를 달성...", POSITIVE))

# After
feedback.append(LocalizableMessage(
    code="stats.feedback.goal_achieved",
    params={"period": period, "name": goal.tag.name, "hours": goal.target_hours},
    severity="positive",
))
```

→ `period`는 한국어 문자열 X, **enum 키** ("daily"/"weekly"/"monthly").

### 5. 일본어 이식 대비 규칙 (지금부터 강제)

| 규칙 | 이유 |
|------|------|
| msgid에 단위까지 포함: `"%(hours)s시간"` | ja「時間」, en "hours" 위치 다름 |
| 조사 결합 금지: `"%(name)s를"` X → 문장 통째 번역 | ja 조사 동일 문제 |
| 카운트 메시지는 `ngettext` 강제 | 한/일 단수만, 영어 복수 분기 |
| `gettext_lazy`만 모듈 레벨 사용 | 첫 요청 locale 고정 방지 |
| f-string 금지 | makemessages 추출 실패 |
| `gettext`는 별칭 X (요청 컨텍스트 grep 용이) | 모듈/요청 구분 명확화 |

---

## Phase별 작업

| Phase | 작업 | 의존 | 시간 |
|-------|------|------|------|
| **0.5** | 인프라: `LocalizableMessage` 타입 + `render_message` 태그 + `apps/core/messages.py` | — | 2h |
| **1** | base/core: `utils.py`, `base.html`, `index.html`, `utils.js`, JS catalog 배선 | 0.5 | 4–5h |
| **2** | dashboard | 1 | 3–4h |
| **3** | tags | 1 | 3h |
| **4** | users | 1 | 4–5h |
| **5** | stats: `life_feedback.py` 전면 코드+파라미터 변환 | 1, 0.5 | 5–6h |

### Phase 0.5 — 인프라

**신규 파일**
- `apps/core/messages.py` — `LocalizableMessage` 타입, `Severity` Literal
- `apps/core/templatetags/__init__.py` (없으면)
- `apps/core/templatetags/i18n_messages.py` — `render_message` 태그
- `apps/core/tests_messages.py` — 타입/태그 단위 테스트

**검증**
- pytest: `LocalizableMessage` 직렬화/불변성, `render_message` 다양한 입력 (dict/객체/missing code) 처리
- 더미 카탈로그로 영어 locale 출력 확인

### Phase 1 — base/core (모든 후속 차단)

**파일**
- `lifeDiary/urls.py` — `path("jsi18n/", JavaScriptCatalog.as_view(packages=[...]), name="javascript-catalog")`
- `apps/core/utils.py` (51) — `gettext_lazy as _` 래핑
- `templates/base.html` (31) — `{% load i18n %}` + 토글/네비/푸터 `{% trans %}` + `<script src="{% url 'javascript-catalog' %}">`
- `templates/index.html` (28)
- `templates/shared/*.html`
- `apps/core/static/core/js/utils.js` (29) — `gettext()` / `interpolate()`
- `apps/core/static/core/js/tag.js`

**검증**
- `conda run -n knou-life-diary django-admin makemessages -l en --ignore=.venv --ignore=staticfiles`
- `conda run -n knou-life-diary django-admin makemessages -d djangojs -l en --ignore=.venv --ignore=staticfiles`
- `.po` 영문 입력 → `compilemessages -l en`
- 네비 토글 → `/` 영문 확인 + `jsi18n/` 200 OK
- pytest `@override_settings(LANGUAGE_CODE='en')` 스모크

### Phase 2 — dashboard

**파일**
- `apps/dashboard/views.py` (35), `models.py`
- `apps/dashboard/templates/dashboard/index.html`, `_tag_image_modal.html`
- `apps/dashboard/static/dashboard/js/dashboard.js` (38) — 카운트는 `ngettext`

### Phase 3 — tags

**파일**
- `apps/tags/models.py` (35), `views.py` (34), `domain_services.py` (12)
- `apps/tags/templatetags/` — 함수 본문에서 `_()` 호출 (모듈 레벨 X)
- `apps/tags/templates/tags/index.html`, `_tag_modal.html`

### Phase 4 — users

**파일**
- `apps/users/forms.py` (11) — `gettext_lazy`로 labels/error_messages/help_text
- `apps/users/views.py` (13), `domain_services.py` (6)
- `apps/users/templates/users/*.html` (~60)
- `apps/users/static/users/js/goals.js` (5)
- 비고: `axes` 패키지 메시지는 기본 영어, 별도 작업 X

### Phase 5 — stats (코드+파라미터 본격 적용)

**파일**
- `apps/stats/messages.py` (신규) — `CATALOG`, `PERIOD_LABELS`
- `apps/stats/life_feedback.py` — `_fb` 시그니처 변경:
  ```python
  def _fb(code: str, params: dict, severity: str = "info") -> LocalizableMessage:
      return LocalizableMessage(code=code, params=params, severity=severity)
  ```
- `apps/stats/views.py` (26), `use_cases.py`
- `apps/stats/templates/stats/index.html` (~70), `life_feedback.html` (~23)
  - `{{ fb.message }}` → `{% render_message fb %}` 일괄 치환
- `apps/stats/static/stats/js/stats.js` (20)

**life_feedback 메시지 코드 매핑 (예시)**

| 기존 메시지 | 코드 |
|------------|------|
| 목표 달성 | `stats.feedback.goal_achieved` |
| 목표 진행 중 | `stats.feedback.goal_in_progress` |
| 태그 불균형 (60%+) | `stats.feedback.tag_imbalance` |
| 리듬 붕괴 (CV>=0.7) | `stats.feedback.tag_volatility` |
| 휴식 과다 | `stats.feedback.rest_excess` |
| 미분류 과다 | `stats.feedback.unclassified_excess` |

---

## 명시적 범위 밖 (이번 작업 제외)

- 일본어 추가 (구조만 준비, `.po` 파일 X)
- DRF API 엔드포인트 신설 (B 하이브리드 준비만, 실제 추가 X)
- 캐시 키 locale 분리 (영어만일 때 영향 미미, 일본어 추가 시점에 일괄)
- Chart.js locale 설정
- AI/LLM (현재 코드에 없음)

---

## 리스크 및 완화

| 리스크 | 완화 |
|--------|------|
| f-string이 makemessages에 추출 안 됨 | PR 체크리스트 + grep 검사 (`grep -rn 'f"' apps/`) |
| 영어 글자 폭 팽창 (한 100자 → 영 ~120자) | Phase 1 base.html 작업 시 주요 카드/버튼 max-width 점검 |
| `messages.py` 카탈로그-사용 코드 불일치 | 단위 테스트: 모든 사용 코드가 카탈로그에 존재 검증 |
| 템플릿이 `LocalizableMessage` 객체 직접 출력 | Phase 5 시 `{{ fb.message }}` grep → `{% render_message fb %}` 일괄 치환 |
| 모듈 레벨 `gettext` 잘못 사용 → 첫 요청 locale 고정 | `gettext_lazy as _` 만 모듈 레벨 import 강제 (코드 리뷰 항목) |
| 커스텀 템플릿 태그 문자열 발견 누락 | 함수 본문 `_()` 사용 강제 + makemessages 후 .po 결과 검증 |

---

## 검증 체크리스트 (각 Phase 공통)

```bash
# 1. 메시지 추출
conda run -n knou-life-diary django-admin makemessages -l en --ignore=.venv --ignore=staticfiles
conda run -n knou-life-diary django-admin makemessages -d djangojs -l en --ignore=.venv --ignore=staticfiles

# 2. .po 파일 영문 입력 후 컴파일
conda run -n knou-life-diary django-admin compilemessages -l en

# 3. 단위 테스트
conda run -n knou-life-diary pytest apps/{app}/ -v

# 4. 수동 확인
conda run -n knou-life-diary python manage.py runserver
# → 네비 언어 토글 → 해당 앱 주요 URL 클릭 통과
```

---

## 실행 순서

```
Phase 0.5 (인프라)
  → Phase 1 (base/core, 후속 차단)
    → Phase 2/3/4/5 (병렬 가능)
      → 통합 검증 (전체 pytest + 수동 토글 회귀)
```

---

## 이전 계획

> 2026-04-24 작성된 "대시보드 태그 UX 개선 계획" (Feature 1: 범례 클릭 핸들러, Feature 2: 사이드바 카테고리 그룹화). 완료 여부는 git log로 확인 필요.
