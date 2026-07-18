# 2026-07-18 전수 검토 (Comprehensive Project Review)

> 실행일: 2026-07-18
> 담당: Yeongrok Song (Claude Code 세션 지원)
> 방법: 방금 이식된 taku 서브에이전트 7종(security-resilience-reviewer,
> deployment-operations-reviewer, domain-architecture-reviewer,
> quality-verification-lead, browser-interaction-reviewer,
> web-experience-designer, product-scope-owner)을 병렬 실행해 코드/설정을
> 직접 검증. 문서 기록은 신뢰하지 않고 실제 파일과 신선한 명령 실행 결과만
> 근거로 채택했다.
> 결과: **신규 회귀 1건 발견(미수정)**, 배포 전 필수 보안 항목 2건, 구조적
> 부채 다수. 이 문서는 리뷰 전용이며 아무 코드도 수정하지 않았다.

---

## 요약

| # | 항목 | 심각도 | 상태 |
|---|------|--------|------|
| 1 | 한국어 번역 카탈로그 빈 msgstr → pytest 28건 실패 | **높음(신규)** | 미수정 |
| 2 | `TestLoginAxesBehavior` 2건 실패 확인 | 중간 | 미수정 (기존에 알려졌으나 방치) |
| 3 | `SECURE_PROXY_SSL_HEADER` 미설정 | 높음(배포 전 필수) | 미수정 |
| 4 | `CSRF_TRUSTED_ORIGINS` 미설정, 결정 미기록 | 중간(배포 전 확인 필요) | 미결정 |
| 5 | CSP 헤더 없음 | 중간 | 미수정 (기존에 알려짐) |
| 6 | `dashboard` ↔ `stats` 양방향 의존성 | 중간 | 미수정 |
| 7 | `apps/users/views.py` 인증 로직이 레이어링 우회 | 중간 | 미수정 |
| 8 | 타임슬롯 그리드 키보드 조작 불가 | 중간 | 미수정 |
| 9 | 모바일 바텀시트 Escape/포커스 트랩 없음 | 중간 | 미수정 |
| 10 | 저장/삭제 실패 시 `aria-live` 없음 | 중간 | 미수정 |
| 11 | 데스크톱 배포: PyInstaller spec/릴리스 워크플로 부재 | 낮음(설계 단계) | 미착수 |
| 12 | 최근 6주 작업이 우선순위 1-2번보다 3-4번에 집중 | 정보성 | 결정 필요 |
| 13 | 광고 슬롯 도입 시 `base.html` 격리 구조 없음 | 낮음(선제 확인) | 대비 필요 |

---

## 1. 한국어 i18n 카탈로그 빈 msgstr 회귀 (신규 발견, 최우선)

### 사실 확인

`locale/ko/LC_MESSAGES/django.po` 322개 항목 중 **265개가 `msgstr ""`**(번역 누락 상태)다.

```
msgid "미분류"
msgstr ""
```

`lifeDiary/settings/dev.py:165`에서 `LANGUAGE_CODE = "ko-kr"`로 한국어가 기본 언어다.
직접 실행으로 확인:

```python
with translation.override('ko'):
    print(repr(_('미분류')))  # -> ''
```

Django의 gettext는 msgstr가 빈 문자열이면 msgid로 폴백하지 않고 **빈 문자열을 그대로 반환**한다.
git 커밋된 상태이며(`git status --short locale/` 결과 없음) 로컬 dev 아티팩트가 아니다.

### 영향

`conda run -n knou-life-diary pytest` 전체 실행 결과 **28건 실패**:

```
FAILED apps/core/tests.py::TestHomePage::test_home_page_presents_simple_daily_recording_for_anonymous_user
FAILED apps/core/tests.py::TestHomePage::test_home_page_renders_korean_footer_copyright
FAILED apps/core/tests.py::TestHomePage::test_home_page_renders_header_utility_controls
FAILED apps/core/tests.py::TestHomePage::test_home_page_invites_authenticated_user_to_record_today
FAILED apps/dashboard/tests.py::TestDashboardIndexRendering::test_dashboard_renders_category_headers
FAILED apps/dashboard/tests.py::TestDashboardIndexRendering::test_dashboard_renders_tags_under_correct_category
FAILED apps/dashboard/tests.py::TestDashboardIndexRendering::test_sidebar_category_headers_use_separator_not_color_dot
FAILED apps/dashboard/tests.py::TestDashboardIndexRendering::test_memo_optional_text_is_placeholder_only
FAILED apps/tags/test_category_i18n.py::TestCategoryI18n::test_display_name_korean
FAILED apps/tags/test_category_i18n.py::TestCategoryI18n::test_category_list_api_returns_translated_name
FAILED apps/users/test_password_reset.py::TestPasswordReset::test_invalid_token_renders_invalid_link_state
FAILED apps/users/test_password_reset.py::TestPasswordReset::test_expired_token_renders_invalid_link_state
FAILED apps/users/test_password_reset.py::TestPasswordReset::test_reused_token_renders_invalid_link_state
FAILED apps/users/test_realtime_validation.py::TestCheckUsername::test_empty
FAILED apps/users/test_realtime_validation.py::TestCheckUsername::test_rate_limited_returns_generic_unavailable_response
FAILED apps/users/test_realtime_validation.py::TestCheckEmail::test_rate_limited_returns_generic_unavailable_response
FAILED apps/core/test_i18n_phase1.py::TestFormatTimeDisplay::test_korean_default
FAILED apps/core/test_messages.py::TestRenderMessage::test_renders_object
FAILED apps/core/test_messages.py::TestRenderMessage::test_renders_dict
FAILED apps/core/test_messages.py::TestRenderMessage::test_resolves_enum_param
FAILED apps/core/test_messages.py::TestRenderMessage::test_missing_code_returns_placeholder
FAILED apps/core/test_messages.py::TestRenderMessage::test_template_tag_loads_in_template
FAILED apps/core/test_messages.py::TestRenderMessage::test_handles_missing_param_gracefully
FAILED apps/dashboard/tests.py::TestDashboardServices::test_build_time_headers
FAILED apps/stats/tests.py::TestStatsServices::test_build_unclassified_daily_entry
FAILED apps/stats/tests.py::TestStatsServices::test_build_unclassified_weekly_entry
FAILED apps/stats/tests.py::TestStatsServices::test_build_unclassified_monthly_entry
FAILED apps/stats/tests.py::TestStatsServices::test_build_unclassified_analysis_entry
```

이는 `docs/project-status.md`에 기록된 과거 "N passed" 로그들과 모순된다. 해당 로그
이후(또는 별개로) ko 카탈로그에 새 문자열이 추가되면서 항등 번역(msgstr = msgid)
채우기가 누락된 것으로 추정된다.

추가로 pytest 프로세스 자체가 최종 요약 라인("N failed, M passed in Xs") 없이
비정상 종료했고, `conda run`이 자체 `ERROR` 메시지로 대체했다 — 원인 미확인,
재현 및 원인 규명 필요.

### 추정 원인 (미확정, 수정 전 재검토 필요)

소스 문자열 자체가 한국어라서 "번역이 필요 없다"고 오인해 `makemessages`가 생성한
ko 카탈로그의 msgstr를 채우지 않은 것으로 보인다. gettext 규격상 빈 msgstr는
"번역됨(빈 문자열)"으로 취급되므로, msgid와 동일한 텍스트라도 msgstr에 명시적으로
채워야 한다.

### 미결 질문

- 프로덕션 배포본도 동일한 `compilemessages` 파이프라인을 쓰는지, 실사용자에게도
  빈 텍스트가 노출되었는지는 이 리뷰에서 확인하지 못했다. 배포 로그/실제 서비스
  화면 확인이 필요하다.

---

## 2. `TestLoginAxesBehavior` 재확인 결과

`apps/users/tests.py::TestLoginAxesBehavior` 중 2개가 **현재 실제로 실패** 중임을
직접 실행으로 확인했다 (`2 failed, 3 passed in 18.03s`):

- `test_lockout_after_failure_limit` — `assert locked.status_code == 429` 에서 `200 == 429`로 실패
- `test_cooloff_allows_login_again` — 동일 패턴으로 실패

`2026-05-22-google-login.md`가 "pre-existing axes lockout failures"로 언급했던
문제가 이후에도 수정되지 않고 남아 있다. `apps/users/tests.py`에는 skip/xfail/TODO
마커가 전혀 없어 의도적 보류가 아니라 방치된 실패로 보인다.

---

## 3. 보안 — 배포 전 확인 필요 항목

`lifeDiary/lifeDiary/settings/{dev,prod,desktop}.py` 직접 검증 결과:

| 항목 | 현재 상태 | 근거 |
|---|---|---|
| HSTS / SSL 리다이렉트 | 완료 | `prod.py:33-36` |
| `SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE` | 완료 | `prod.py:37,39,40` |
| `CSRF_COOKIE_SECURE/SAMESITE` | 완료 | `prod.py:38,41` |
| `ALLOWED_HOSTS` | 완료 | `prod.py:30` 단일 호스트 |
| django-axes + reCAPTCHA | 완료(설계상 axes 임계값을 매우 높게 두고 reCAPTCHA가 먼저 개입) | `prod.py:48-56` |
| `DEBUG=False` | 완료 | `prod.py:15` |
| **`SECURE_PROXY_SSL_HEADER`** | **미설정** | Render가 TLS를 프록시에서 종료함. 이 설정이 없으면 `request.is_secure()`가 오판할 수 있고, `SECURE_SSL_REDIRECT`와 결합해 리다이렉트 루프 위험. 배포된 URL에 대한 `curl -I` 확인 필요 |
| **`CSRF_TRUSTED_ORIGINS`** | **미설정** | 교차 출처 POST 증거는 없으나, 명시적 결정 기록 없음 |
| CSP 헤더 | 없음 | `django-csp` 미설치, 미들웨어 없음. 2026-04-21 저장형 XSS는 코드로 막았으나 심층방어 헤더는 부재 |
| 로그인 실패 알림/로깅 | 없음 | `user_login_failed`/`axes.signals.user_locked_out` 시그널 리시버 없음, 관측성 공백(취약점 아님) |
| 비밀번호 정책 | 기본값만(강화 없음) | `MinimumLengthValidator` 등 Django 기본 4종, 커스텀 옵션 없음 |
| `CSRF_COOKIE_HTTPONLY` | 미설정(Django 기본) | JS의 CSRF 토큰 읽기와 트레이드오프, 의도적 결정으로 문서화되지 않음 |

---

## 4. 아키텍처 — 레이어링 위반 2건

- **`dashboard` ↔ `stats` 양방향 의존성**: `apps/dashboard/use_cases.py:10`이
  `apps.stats.use_cases.invalidate_stats_cache`를 호출(`use_cases.py:67,85`).
  AGENTS.md 계약상 `stats`는 `dashboard`를 읽기 전용으로만 참조해야 하는데,
  반대 방향 의존이 생겨 양방향 결합이 됨.
- **`apps/users/views.py`(568줄, 400줄 가이드라인 초과)에 인증/계정 로직이
  use_case/repository 없이 직접 ORM 접근**: `views.py:268-284`,
  `:292-293`, `:374-378`, `:401-405` 등. Goal/Note는 정상적으로
  `GoalRepository`/`NoteRepository`를 거치지만, 앱에서 가장 복잡한 책임인
  인증/복구 로직만 레이어를 우회함. `User`/인증에 대한 repository나
  domain_service가 아예 없음(누락된 레이어).
- 그 외 파일 크기 400/800줄 가이드라인 위반은 `users/views.py` 외 없음.

---

## 5. 접근성 / 상호작용 — 핵심 기능이 키보드로 조작 불가

- **대시보드 144개 타임슬롯 그리드가 키보드로 전혀 접근 불가**:
  `apps/dashboard/templates/dashboard/index.html:105-111`이 `onclick`/
  `onmousedown`/`onmouseenter`/`onmouseup`/터치 이벤트만 연결, `tabindex`/
  `role`/keydown 핸들러 전무. 키보드 전용/스크린리더 사용자는 핵심 기록
  기능 자체를 사용할 수 없음.
- **모바일 퀵인풋 바텀시트에 Escape 닫기·포커스 트랩 없음**:
  `dashboard.js:135-152`가 `role="dialog"`/`aria-modal="true"`를 설정하지만
  keydown 리스너가 없어 Escape가 동작하지 않고, Tab이 배경 요소로 빠져나갈 수 있음.
- **저장/삭제 실패 시 `aria-live` 없음**: `showNotification`/`showOverlay`
  (`utils.js:35-59, 67-90`)에 `aria-live`/`role="status"`/`role="alert"`가
  없어, 저장 실패가 스크린리더 사용자에게 전달되지 않음(성공했다고 오인 가능).
- `prefers-reduced-motion` 대응 전무(리포지토리 전체 검색 0건).
- 480px 이하에서 타임슬롯 터치 타겟이 16px로, 같은 스타일시트의 다른 버튼(44px)
  대비 지나치게 작음.

---

## 6. 데스크톱 배포 — 설계만 존재, 구현 없음

- `desktop/*.spec` 파일이 리포지토리 전체에 없음 — 패키징 자체가 불가능한 상태.
- `DesktopAuthMiddleware`, 로컬 유저 부트스트랩, context processor, 로그아웃
  숨김 로직이 `docs/plans/2026-05-07_desktop-auth-single-user-plan.md`에만
  설계로 존재하고 코드에는 없음.
- 데스크톱 릴리스 빌드용 GitHub Actions 워크플로 없음(`deploy-pr.yml`은 웹
  프로덕션 PR 게이트만 수행).
- `desktop/launcher.py:52`가 매 부팅 시 `migrate --noinput`을 예외 처리 없이
  실행 — 마이그레이션 실패 시 사용자에게 원시 traceback이 노출됨(패키징
  계획 문서 자체가 이미 미해결 리스크로 인지하고 있음).

---

## 7. 제품 방향 — 우선순위 드리프트

CLAUDE.md의 표명된 우선순위는 (1) 10분 슬롯 기록/태깅 품질 (2) 통계·라이프
피드백 인사이트 (3) 데스크톱 배포 (4) 공개 페이지·광고 순이다.

`docs/project-status.md`의 최근 6주(2026-05-15~05-26) 완료 항목 20여 건 중
대부분이 인증/계정(구글 로그인, 쿠키 보안, reCAPTCHA, 계정 삭제 유예),
브랜딩/법무(푸터, 개인정보/이용약관), UI 폴리싱(바텀시트, 태그 색상, 통계
접기)에 집중되어 있고, 우선순위 1-2번(기록/태깅 로직 자체, 피드백 규칙
품질 자체)을 직접 개선한 작업은 없다. `apps/stats/life_feedback.py`는 이
기간 완료 로그에 등장하지 않는다.

활성 계획 중 "High" 우선순위 2건이 모두 우선순위 3번(데스크톱) 항목이라,
표명된 순위와 실제 계획 배분이 어긋난다.

---

## 8. 광고 도입 대비 — 구조적 격리 장치 없음(선제 확인, 아직 위험 아님)

`templates/base.html`을 공개 페이지(home, legal)와 비공개 페이지(dashboard,
stats, tags, users, account)가 모두 공유하며, `ad_slot` 블록이나 별도
`base_public.html`/`base_private.html` 분리가 전혀 없다(리포지토리 전체
grep 결과 `ad_slot`/`adsense` 0건). 지금은 광고 코드가 없어 위험하지 않지만,
향후 광고 단계 착수 시 `base.html`에 직접 광고 블록을 추가하면 대시보드/통계/
인증 페이지까지 새어나갈 수 있다. 착수 전에 공개 템플릿 전용 include 또는
빈 기본값 `{% block ad_slot %}{% endblock %}` + 비공개 페이지에서 광고
마크업이 없음을 보장하는 회귀 테스트가 필요하다.

---

## 이 리뷰에서 다루지 않은 것

- 실사용자 대상 프로덕션 환경에서의 라이브 검증(배포된 URL 응답 확인 등)은
  수행하지 않았다. 위 발견 중 다수가 "코드/설정 기준 확인"이며 실배포 환경
  재확인이 필요하다고 각 항목에 명시했다.
- 어떤 코드도 수정하지 않았다. 모든 항목은 착수 전 사용자 승인이 필요한
  다음 계획 대상이다.
