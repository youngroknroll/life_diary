# 2026-04-28 i18n Phase 1~5 (한영 전환) 실행 로그

> 실행일: 2026-04-26 ~ 2026-04-28 (커밋 `cdd4ac1` ~ `5fc0971`)
> 범위: Phase 1 (base/core) → Phase 2 (dashboard) → Phase 3 (tags) → Phase 4 (users, TDD) → Phase 5 (stats, 코드+파라미터 패턴)
> 전제: Phase 0 (인프라 — `LocaleMiddleware`, `LANGUAGES=[ko,en]`, `locale/en` 스캐폴드)는 2026-04-21에 완료. (`docs/refactoring/2026-04-21_post-phase4-state-update.md` §4.2)

---

## 산출물 요약

| 항목 | 수치 |
|------|------|
| `locale/en/LC_MESSAGES/django.po` msgid | 269 |
| `locale/en/LC_MESSAGES/djangojs.po` msgid | 48 |
| 신규 모듈 | `apps/core/messages.py`, `apps/core/templatetags/i18n_messages.py`, `apps/stats/messages.py` |
| 신규 테스트 파일 | `apps/{core,dashboard,tags,users,stats}/test_i18n_phase{1..5}.py` (5개, 27 테스트) |
| 수정된 앱 | core / dashboard / tags / users / stats (전체 5앱) |

---

## 아키텍처 결정

### 1. `LocalizableMessage` (코드 + 파라미터 + severity)

**위치**: `apps/core/messages.py`

```python
@dataclass(frozen=True)
class LocalizableMessage:
    code: str                # 예: "stats.feedback.goal_achieved"
    params: dict             # 예: {"period": "daily", "name": "운동", "hours": 5}
    severity: Severity       # "positive" | "info" | "warning" | "error"

    def to_dict(self) -> dict: ...
```

**채택 사유**:
1. **다국어 확장성**: 비즈니스 로직은 한국어 문자열 대신 코드를 반환. 일본어 추가 시 `.po`만 추가하면 됨 — Python 코드 변경 0.
2. **JSON API 호환**: `to_dict()` → 그대로 직렬화. SSR 템플릿과 향후 REST 엔드포인트가 같은 반환 타입 공유.
3. **severity 통일**: 토스트/알림 색상 결정을 클라이언트 책임에서 도메인 책임으로 이동.

**적용 범위**: Phase 5의 `apps/stats/life_feedback.py`만. Phase 1~4의 단순 UI 문자열은 `gettext_lazy`/`{% trans %}` 직접 사용 (오버엔지니어링 회피).

### 2. 앱별 `messages.py` (CATALOG + ENUM_LABELS)

**위치**: `apps/<app>/messages.py` (자동 발견)

```python
# apps/stats/messages.py
CATALOG = {
    "stats.feedback.goal_achieved": _("%(period)s '%(name)s' 목표(%(hours)s시간)를 이미 달성했습니다!"),
    ...
}
ENUM_LABELS = {
    "period": {"daily": _("오늘"), "weekly": _("이번주"), "monthly": _("이번 달")},
}
```

- **CATALOG**: code → lazy 번역 문자열 매핑.
- **ENUM_LABELS**: params 안 enum 값(`"daily"`)을 표시 라벨(`"오늘"` / `"Today"`)로 자동 치환.

### 3. `{% render_message %}` 템플릿 태그

**위치**: `apps/core/templatetags/i18n_messages.py`

- `apps.get_app_configs()`로 모든 앱의 `messages.py` 자동 import.
- 코드 충돌 시 `ImproperlyConfigured` 발생 → 네임스페이스 강제.
- 템플릿 사용: `{% load i18n_messages %}{% render_message fb %}`.
- dict 입력도 지원 (API 응답 → 템플릿 렌더링 시).

---

## Phase 1 — base/core (커밋 `a51059c`)

**목표**: 홈 페이지 + 공통 네비 + `format_time_display` 유틸 영문화.

### 변경
- `lifeDiary/urls.py`: `path("jsi18n/", JavaScriptCatalog.as_view(packages=[...]))` 추가 → JS 측 `gettext()`/`interpolate()` 카탈로그 엔드포인트.
- `apps/core/utils.py::format_time_display`: locale-aware 분기 (`activate("en")` 시 `"2h 30m"`).
- `templates/base.html`, `apps/core/templates/core/index.html`: 네비 + 히어로 + 모달 라벨에 `{% trans %}` 적용.
- 신규: `apps/core/test_i18n_phase1.py` (5 테스트).

### 발견 이슈
- 모든 템플릿 상단에 `{% load i18n %}` 누락 시 `{% trans %}` 무시. 일괄 추가.

---

## Phase 2 — dashboard (커밋 `7b9922b`, 검토 후 `4cc4d77`)

**목표**: 대시보드 사이드바·통계 카드·날짜 셀렉터·API 메시지 영문화.

### 변경
- `apps/dashboard/templates/dashboard/index.html`: 사이드바 + 카드 헤더 + 빈 상태 메시지 전부 `{% trans %}`.
- `apps/dashboard/views.py`: `JsonResponse({"message": _("Invalid JSON format.")})` — API 에러 메시지 lazy.
- 신규: `apps/dashboard/test_i18n_phase2.py` (4 테스트).

### 검토 후 수정 (`4cc4d77`)
| 이슈 | 원인 | 수정 |
|------|------|------|
| 날짜 포맷이 영문 locale에서도 `"4월 26일 (일)"` | 템플릿에 `{{ date|date:"Y년 m월 d일" }}` 하드코딩 | `{{ date|date:"DATE_FORMAT" }}` (locale-aware) |
| 템플릿 `with` 구문에 `_("목표 추가")` 사용 | Django 템플릿 문법 아님 | `{% trans "목표 추가" as label %}` |
| `services.py`의 `f"{minute}분"` | f-string은 gettext가 추출 못 함 | `gettext("%(minute)s분") % {"minute": minute}` |

---

## Phase 3 — tags (커밋 `b9ec409`)

**목표**: 태그 관리 페이지 + 태그 생성/수정 모달 + API 검증 메시지.

### 변경
- `apps/tags/templates/tags/index.html`, `apps/tags/templates/tags/_form.html`: 라벨/플레이스홀더 영문화.
- `apps/tags/views.py`: `_("Please enter a tag name and color.")`, `_("Malformed request.")`.
- `apps/tags/static/tags/js/tags.js`: `gettext("Loading tags...")`, `gettext("No tags yet.")`.
- 신규: `apps/tags/test_i18n_phase3.py` (4 테스트).

### 발견 이슈
- HTML 주석 `<!-- 목표 추가 -->`가 `assertNotContains("목표 추가")` 실패 유발. 한국어 주석 제거.

---

## Phase 4 — users (커밋 `983cee7`, TDD 사이클)

**목표**: 로그인/회원가입/마이페이지/UserGoal/UserNote — 가장 큰 표면적 (forms.py 11, views.py 13, domain_services.py 6, 9 templates ~60, goals.js 5).

### TDD 흐름
1. **RED**: 영어 locale 테스트 5개 클래스 작성 → 모두 fail.
2. **GREEN**: `gettext_lazy` / `{% blocktrans %}` 적용 → `.po` 입력 → 컴파일 → pass.

### 변경
- `apps/users/forms.py`: `verbose_name` / `help_text` / `error_messages` 모두 `_()`.
- `apps/users/views.py`: messages framework `messages.success(request, _("Successfully logged out."))`.
- `apps/users/domain_services.py`: validation 메시지 lazy.
- 9 템플릿: 라벨 + 버튼 + 빈 상태 + 안내 문구 전부 `{% trans %}` / `{% blocktrans %}`.
- `apps/users/static/users/js/goals.js`: `gettext()` 적용.
- 신규: `apps/users/test_i18n_phase4.py` (8 테스트).

### 발견 이슈
| 이슈 | 수정 |
|------|------|
| `LogoutMessageEnglishTests`가 매번 새 user 생성 — 다른 테스트 격리 | `setUpTestData` 분리 |
| `.po`에서 `%(minute)s분` ↔ fuzzy 매칭된 `%(minutes)sm` (s 차이) | 수동 .po 편집으로 placeholder 일치시킴 |
| `messages framework` lazy 평가 시점 — request locale 적용 확인 | `messages.success(request, _("..."))` 로 OK (다음 요청에서 활성 locale로 평가) |

---

## Phase 5 — stats (커밋 `5fc0971`, **코드+파라미터 패턴**)

**목표**: 통계 페이지 영문화 + `life_feedback.py`를 **`LocalizableMessage`** 기반으로 재설계.

### 왜 stats만 코드+파라미터?
- `life_feedback.py`는 동적 메시지 생성 (`f"{name} 목표 달성!"` 식). gettext 추출이 안 되고, 향후 일본어 추가나 JSON API 전환 시 다시 손봐야 함.
- 단순 UI 문자열(Phase 1~4)은 `{% trans %}` / `gettext_lazy` 직접 사용으로 충분.

### 변경
- `apps/core/messages.py` 신규 — `LocalizableMessage` dataclass.
- `apps/core/templatetags/i18n_messages.py` 신규 — `render_message` 태그 + 자동 catalog 발견.
- `apps/stats/messages.py` 신규 — CATALOG (6 코드) + ENUM_LABELS (`period`).
- `apps/stats/life_feedback.py` 리팩터링: 모든 f-string `_msg(code, params, severity)` 반환으로 통일.
- `apps/stats/templates/stats/life_feedback.html`: `{% render_message fb %}`로 렌더링, `severity`에 따라 토스트 색상 분기.
- `apps/stats/static/stats/js/stats.js`: `gettext()` + `interpolate()` 적용.
- 신규: `apps/stats/test_i18n_phase5.py` — `LocalizableMessage` 반환 타입 검증 + 영문 템플릿 렌더링 검증.

### life_feedback 변환 예시

**Before** (한국어 hardcoded):
```python
feedback.append(f"{period_label} '{goal.tag.name}' 목표({goal.target_hours}시간)를 이미 달성했습니다!")
```

**After** (LocalizableMessage):
```python
feedback.append(_msg(
    "stats.feedback.goal_achieved",
    {"period": period, "name": goal.tag.name, "hours": goal.target_hours},
    POSITIVE,
))
```

---

## 공통 발견 이슈 (전체 phase)

### A. `.po` 폴루션 — 테스트 fixture msgid 누출
- `apps/core/test_messages.py`의 테스트용 `_("test.code.foo")` 등이 `makemessages` 실행 시 production `.po`에 침투.
- **수정**: `manage.py makemessages -l en --ignore=apps/*/tests*.py --ignore=apps/*/test_*.py`.

### B. f-string anti-pattern
- `f"{minute}분"` 류는 gettext가 추출 못 함.
- 모든 f-string을 `gettext("...") % {...}` 형태로 변환.

### C. 하드코딩된 날짜 포맷
- `Y년 m월 d일` → 영문 locale에서도 한국어 형식 출력.
- `DATE_FORMAT` 사용 (Django locale-aware 포맷).

### D. 템플릿에 Python 표현식
- `_("...")`는 Python 문법, 템플릿에서 무효.
- `{% trans "..." as var %}` 또는 `{% blocktrans %}` 사용.

### E. 한국어 HTML 주석이 영문 테스트 깨뜨림
- `<!-- 목표 추가 -->`가 `assertNotContains` 실패 유발.
- 주석 제거 또는 영문화.

---

## 검증

### 자동 테스트 (`test_i18n_phase{1..5}.py`)
- 27 테스트 (Phase 1: 5, Phase 2: 4, Phase 3: 4, Phase 4: 8, Phase 5: 6)
- 모두 통과 — `Accept-Language: en` 헤더로 영문 출력 검증.

### 수동 회귀
- 한국어 locale (`Accept-Language: ko`)에서 모든 페이지가 기존과 동일하게 한국어로 출력됨을 확인.
- `format_time_display(2, 30)`: ko → `"2시간 30분"`, en → `"2h 30m"`.

---

## 명시적 범위 밖

- 일본어(`ja`) 번역: 향후 별도 phase. 현재는 `LANGUAGES=[ko, en]`만.
- API 엔드포인트의 `LocalizableMessage` JSON 반환: 인프라(`to_dict()`)는 마련됐지만 실제 REST 엔드포인트는 없음 — SSR 전용.
- `apps/core/test_messages.py`의 메시지 코드 충돌 검증 테스트는 별도 작업.

---

## 후속 과제

| 항목 | 비고 |
|------|------|
| 일본어 `.po` 추가 | `LANGUAGES`에 `ja` 추가 + `locale/ja/LC_MESSAGES/django.po` 작성. 코드 변경 0. |
| Phase 4 외 메시지를 `LocalizableMessage`로 일관화? | 단순 UI 문자열은 `{% trans %}`로 충분. 동적 생성 메시지가 더 늘면 그때 검토. |
| `messages.py` 카탈로그 lint | 코드 prefix(`<app>.<area>.<name>`) 규칙 검사 자동화 |
| messages framework lazy 평가 회귀 테스트 | 현재 수동 검증만 — 자동화 가치 낮음 (Django 보장 동작) |

---

## 핵심 파일

- 인프라: `apps/core/messages.py`, `apps/core/templatetags/i18n_messages.py`, `lifeDiary/urls.py` (jsi18n)
- 카탈로그: `apps/stats/messages.py`
- 번역 자원: `locale/en/LC_MESSAGES/django.po` (269 msgid), `locale/en/LC_MESSAGES/djangojs.po` (48 msgid)
- Phase 5 핵심: `apps/stats/life_feedback.py`, `apps/stats/templates/stats/life_feedback.html`
- 검증: `apps/{core,dashboard,tags,users,stats}/test_i18n_phase{1..5}.py`

---

## 관련 문서

- 인프라(Phase 0): `docs/refactoring/2026-04-21_post-phase4-state-update.md` §4.2
- 계획: `prompt_plan.md` (i18n 한영 전환 + 코드+파라미터 아키텍처)
- 자매 문서: `docs/refactoring/2026-04-28_pytest-migration.md` (오늘 함께 진행한 테스트 스타일 전환)
