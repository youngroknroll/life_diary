# Project Status

Last updated: 2026-08-12

This document is the single status index for LifeDiary planning, execution, and follow-up documents. It does not replace the detailed documents linked below, and no existing plan or refactoring document should be deleted only because it is listed here.

Status values are based on the repository documents available at the update time. They are not fresh code verification unless a verification command is explicitly listed.

## Status Legend

| Status | Meaning |
|---|---|
| Completed | Execution log or verification evidence exists in project documents. |
| Active Plan | Planned work that appears relevant and not yet documented as completed. |
| Deferred | Intentional later work or out-of-scope item. |
| Superseded | Older planning context replaced by a newer execution log or status document. |
| Reference | Architecture, analysis, or guidance document, not a task backlog item. |
| Unknown | Status cannot be determined from documents alone. |

## Latest Execution (2026-08-10 ~ 08-12) — 시안 정합 재작업

시안 22화면을 구현과 전수 대조해 격차를 7단계로 나눠 메웠다.
계획: `docs/plans/2026-08-10_sian-conformance-remediation-plan.md`

| 단계 | 범위 | 실행 로그 |
|---|---|---|
| 1~3 | 스킨 잔재, 인증 화면, 태그 모달·설정 재구성, 이름 10자 | `2026-08-10_sian-conformance-stage1~3.md` |
| 4 (D1) | 기본 태그 폐지 — 모든 태그를 개인 소유로. 되돌릴 수 없는 마이그레이션 | `2026-08-10_sian-conformance-stage4.md` |
| 5 (D2) | 달성률 분모를 지난 시간 기준으로, 룰 기반 피드백 제거 | `2026-08-11_sian-conformance-stage5.md` |
| 6 (B3+A3) | 빈 상태, 온보딩 3단계 (STEP2 는 실제로 저장한다) | `2026-08-11_sian-conformance-stage6.md` |
| 7 (A1) | 태그 관리를 행 리스트로 재작성 | `2026-08-12_sian-conformance-stage7.md` |

브랜치 `feat/p0-onboarding` (6·7단계). 4·5단계는 PR #40 에 포함됐다.
머지는 사용자 몫.

주의할 결정:

- **태그는 전부 개인 소유다.** `Tag.user` non-nullable, `is_default` 폐지.
  가입 시 시드 태그를 개인 태그로 만들어 준다
- **달성률 분모에서 아직 오지 않은 날을 뺀다.** 다만 오늘 이미 채웠으면 센다
- **지시형 코칭 문구를 전부 없앴다.** 남긴 `_observations` 는 사실 진술이다
- **태그 순서는 사용자가 정하지 않는다** (2026-08-12). 카테고리 순서는
  시스템이, 태그는 그 안에서 이름순. 7단계에서 만들었다가 걷어냈다
- **시안 이탈 신설**: 시안 6a 의 행 드래그와 인라인 이름 편집은 채택하지
  않는다. 편집은 행에서 바로 열리는 모달이다

## Latest Execution (2026-08-01 ~ 08-02)

P0 시안 리디자인을 마쳤다. 구현 명세 7단계와 시안 화면 19개 전부.
브랜치 `feat/p0-redesign-grid`, PR #40, 커밋 30개. **머지 완료(2026-08-11).**

- 실행 로그: `docs/refactoring/2026-08-01_p0-sian-redesign.md`
- 명세 단계 계획: `docs/plans/2026-08-01_p0-redesign-plan.md`
- 화면 인벤토리와 컴포넌트 스펙: `docs/plans/2026-08-01_sian-screen-inventory.md`

핵심 변경:

- 최상위 내비게이션이 홈·기록·분석·설정 넷으로 바뀌었다. 태그 관리는 설정
  하위로 내려갔고 언어·테마도 설정 안으로 들어갔다. 모바일은 하단 탭바.
- 기록 그리드가 24행 × 6열이 되고 같은 태그 연속 칸이 하나의 블록으로
  병합된다. 드래그는 그리드 하나에 위임하고 키보드 경로가 생겼다.
- 저장·삭제 후 페이지를 다시 읽지 않는다. 서버가 돌려준 행만 부분 갱신하고
  60초짜리 되돌리기를 준다.
- 분석 화면이 요약·일·주·월 4탭이 되고 "태그 분석" 탭은 흡수됐다.
- 색은 카테고리가 정한다. 태그별 색 선택기를 없앴다.
- 집계 4종 신설: `comparison` · `density` · `goal_progress` · `summary`.

주의할 결정:

- **주 기간은 달력 주(월~일)다.** 시안은 롤링 7일이었고 사용자가 뒤집었다.
  진행 중인 주는 `is_partial`과 경과일 분모로 표기한다.
- **홈에서 "10분 단위"를 노출한다.** 2026-04-11에 감추기로 한 결정을
  시안 5a가 뒤집었고 테스트를 반대로 고정했다.
- **프론트엔드는 테스트하지 않는다.** 마크업·CSS·JS 소스 문자열 검사
  테스트 12건을 제거했다. `AGENTS.md` Frontend Work Policy 참조.
- **Git은 에이전트가 직접 실행한다.** 커밋은 작은 기능 단위, 트랙마다
  브랜치 push + PR. 머지는 사용자.

## Review Follow-up (2026-08-10)

전수 점검 결과를 문서화했다. 사용자는 **현재 변경 중인 디자인 시안을 먼저
완료한 뒤** 최종 코드 기준의 프런트엔드·브라우저 재검토와 후속 수정을
진행하기로 결정했다. 따라서 디자인 관련 지적은 지금 수정하지 않으며, 새
시안의 최종 브랜치에서 다시 판정한다.

- 후속 계획: `docs/plans/2026-08-10_comprehensive-review-follow-up-plan.md`
- 문서화 로그: `docs/refactoring/2026-08-10_review-follow-up-documentation.md`
- 디자인과 무관하여 출시 전 별도 승인·수정이 필요한 P0: 기본 태그 이관의
  교차 사용자 소유권 침해, 통계 캐시 무효화 범위, 한국어 GNU gettext 카탈로그
  컴파일, 계정 삭제 purge 스케줄링.
- 재검토 대기 P0: Shift+Arrow 슬롯 키보드 오류, 닫힌 모바일 퀵인풋 시트의
  포커스 누출, 사용자 문자열의 inline JavaScript/`innerHTML` 경계.

**2026-08-12 갱신 — 위 목록에서 해소된 것들.** 시안 정합 재작업이 지나가며
같이 닫혔다. 아래 2026-08-10 증거 블록의 수치와 실패는 그 시점의 기록이다.

| 지적 | 해소 |
|---|---|
| 기본 태그 이관의 교차 사용자 소유권 침해 | 4단계 — 공유 태그 개념 자체를 폐지 |
| 한국어 gettext 카탈로그 컴파일 실패 | `msgfmt --check-format` 4개 파일 통과, fuzzy·미번역 0건 |
| Shift+Arrow 슬롯 키보드 오류 | 6단계 — 정의되지 않은 `slotIndex` 참조 수정 |
| 사용자 문자열의 inline JS/`innerHTML` 경계 | 7단계 — 태그 관리의 인라인 `onclick` 문자열 보간 제거 |

남은 것: 통계 캐시 무효화 범위, 계정 삭제 purge 스케줄링, 닫힌 모바일
퀵인풋 시트의 포커스 누출.

2026-08-10 신선한 증거:

```bash
conda run -n knou-life-diary pytest
# 405 passed in 221.59s

conda run -n knou-life-diary python manage.py check
# System check identified no issues (0 silenced).

conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
# No changes detected

msgfmt --check -o /dev/null locale/ko/LC_MESSAGES/django.po
msgfmt --check -o /dev/null locale/ko/LC_MESSAGES/djangojs.po
# 둘 다 Korean plural-form 오류로 실패
```

프로덕션 deploy check는 오류 레벨로 통과했지만, 로컬 환경의 기본 `SECRET_KEY`
관련 W009 경고가 남았다. 실제 배포 환경의 키 품질은 이 확인으로 검증되지
않았다.

## Production Domain (2026-08-12)

서비스 도메인이 `lifediary.kr` 로 바뀌었다. **`ALLOWED_HOSTS` 등록만으로
운영에서 정상 동작하는 것이 확인됐다**(사용자 확인).

```python
ALLOWED_HOSTS = ["lifediary.onrender.com", "www.lifediary.kr", "lifediary.kr"]
```

`CSRF_TRUSTED_ORIGINS` 를 손대지 않아도 되는 이유 — Django 의 origin 검사는
`request.get_host()` 로 만든 origin 과 **먼저** 대조하고, 호스트가
`ALLOWED_HOSTS` 에 있으면 그 목록을 보지 않는다
(`CsrfViewMiddleware._origin_verified`, Django 5.2 소스로 확인). 실제로
`origin/production` 의 `prod.py` 에는 `CSRF_TRUSTED_ORIGINS` 자체가 없고
문제없이 서비스되고 있다.

### 브랜치 사이의 어긋남 (2026-08-12 정리)

도메인 수정이 `production` 브랜치에서 **직접** 이루어져 `main` 에 없었다.

| 브랜치 | `ALLOWED_HOSTS` |
|---|---|
| `origin/production` | `onrender`, `www.lifediary.kr`, `lifediary.kr` (커밋 `ca221bf`·`ff9157d`) |
| `origin/main` | `onrender` 뿐 |
| `feat/p0-onboarding` | production 과 동일하게 맞춤 |

그대로 두면 다음 `main -> production` 배포에서 `www.lifediary.kr` 이 도로
사라질 수 있었다. 이 브랜치가 production 의 목록을 그대로 가져와 `main` 을
따라잡게 한다.

**배포 흐름 메모**: `main` 이 `production` 으로 흘러가는 구조인데
(`Deploy: main -> production` PR), 지금 `production` 은 `main` 보다 앞선
커밋 2개와 뒤진 커밋 다수를 동시에 갖고 있다. 운영 급한 수정을 production
에 직접 넣으면 이런 어긋남이 반복된다.

메일 발신은 현재 Gmail SMTP 다(`prod.py`). 도메인이 생겼으므로 발신 도메인
검증을 미뤄 두었던 항목을 다시 볼 수 있으나, DNS 설정 여부는 확인하지 않았다.

## Known Current Regressions (Read Before Trusting "Passed" Evidence Below)

Resolved 2026-07-18 (same day, later session): the 28-test failure caused by
empty `msgstr` entries in the ko catalogs was fixed by filling identity
translations with `msgen` (`django.po` 265, `djangojs.po` 112 entries), and
the full suite is green again: 256 tests, exit 0. The 2
`TestLoginAxesBehavior` failures reported by the morning review could not be
reproduced (3 isolated runs + 3 full-suite runs all pass, no code change);
treat them as environment/timing artifacts unless they reappear. Remediation
plan, evidence, and remaining unverified items:
`docs/plans/2026-07-18_comprehensive-review-remediation-plan.md`,
`docs/refactoring/2026-07-18_comprehensive-review-remediation.md`. The other
review findings (security settings, architecture, bottom-sheet interaction)
were remediated in the same pass; excluded by user decision: timeslot-grid
keyboard access and aria-live announcements. Still open from the review:
desktop packaging absence (#11), priority drift (#12), ad-slot isolation
(#13), and live-deployment verification questions.

## Current Product Direction

LifeDiary is a Django-based life logging app. Users record a day in 10-minute slots, classify time with tags, manage goals and notes, and review life patterns through statistics and rule-based feedback.

The project has moved from a web-only portfolio app toward a desktop distribution path:

- local desktop app packaging with `pywebview`, `waitress`, SQLite, and PyInstaller;
- single local user desktop mode;
- GitHub Releases distribution;
- operational visibility and monetization experiments as later phases.

The current codebase direction is conservative: keep the Django monolith, maintain the app-level boundaries, and use the existing `views -> use_cases -> repositories/domain_services -> models` flow where it already exists.

## Completed Or Documented Execution

| Area | Evidence document | Summary | Verification evidence in document |
|---|---|---|---|
| Initial code review fixes | `docs/refactoring/2026-04-08_fix-log.md` | Fixed selected issues from the 2026-04-08 review, including stats/query and settings concerns. | Document lists verification commands and remaining unfixed items. |
| Phase 0 fixes | `docs/refactoring/2026-04-09_phase0-fix-log.md` | Fixed early architecture/review issues before repository extraction. | Document includes verification section. |
| Repository layer | `docs/refactoring/2026-04-09_phase1-repository-log.md` | Introduced repositories for dashboard, tags, users, goals, and notes. | Document includes import checks and verification. |
| Domain services | `docs/refactoring/2026-04-09_phase2-domain-service-log.md` | Introduced `GoalProgressService` and `TagPolicyService`. | Document includes grep checks and tests. |
| Frontend CSS refactor | `docs/frontend/2026-04-11-css-refactor.md` | Consolidated frontend tokens/components and loading overlay styling. | Document includes verification section. |
| Mobile dashboard responsive pass | `docs/frontend/2026-04-12-mobile-responsive.md` | Improved dashboard mobile responsiveness. | Document includes manual verification method. |
| Inline JS extraction | `docs/refactoring/2026-04-15-inline-js-extraction.md` | Extracted inline JS to static files and aligned dashboard/stats UI behavior. | Document records architecture decisions and changed files. |
| Tag contrast and category fixes | `docs/frontend/2026-04-15-tag-contrast-and-fixes.md` | Fixed tag category behavior and automatic contrast handling. | Document records changed files and implementation details. |
| Sidebar UX | `docs/frontend/2026-04-15-sidebar-ux.md` | Improved dashboard sidebar UX after user feedback. | Document records modified files and JS details. |
| Architecture/cost phases 3-4 | `docs/refactoring/2026-04-20_phase3-4-execution-log.md` | Applied cost and architecture changes including use cases, caching, and stats calculator decomposition. | Document records phase results and final structure. |
| Frontend template remediation | `docs/refactoring/2026-04-21_frontend-template-refactor-log.md` | Fixed stats weekday display, extracted partials/tags, renamed AI feedback to life feedback, and consolidated styles. | Document records final test section. |
| Security remediation | `docs/security/2026-04-21_xss-bruteforce-sri-remediation.md` | Fixed stored XSS risk, added brute-force protection with `django-axes`, and added CDN SRI hashes. | Document reports `55 passed / 0 failed` and lists remaining security work. |
| Post-phase architecture snapshot | `docs/refactoring/2026-04-21_post-phase4-state-update.md` | Captured post-Phase4 architecture status and remaining work. | Document reports `55 passed in 5.89s`. |
| Frontend DRY + dashboard UX | `docs/refactoring/2026-04-23_frontend-dry-and-dashboard-ux.md` | Improved global loading, cache invalidation, dashboard overlays, drag behavior, and frontend DRY structure. | Document includes browser manual checklist. |
| Dashboard tag UX + stats tab preserve | `docs/refactoring/2026-04-24_dashboard-tag-ux-and-stats-tab-preserve.md` | Added dashboard tag legend/category UX and preserved active stats tab on date changes. | Document includes final verification section. |
| Dashboard mobile bottom sheet | `docs/plans/2026-05-15_dashboard-mobile-bottom-sheet-design.md`, `docs/plans/2026-05-15_dashboard-mobile-bottom-sheet.md`, `docs/plans/2026-05-15_dashboard-bottom-sheet-01-line-design.md`, `docs/plans/2026-05-15_dashboard-bottom-sheet-01-line.md`, `docs/plans/2026-05-15_dashboard-tag-list-compact-row.md`, `docs/plans/2026-05-15_tag-category-select-font-size.md`, `docs/plans/2026-05-23-dashboard-mobile-sheet-80vh.md`, `docs/frontend/2026-05-15-dashboard-mobile-bottom-sheet.md`, `docs/refactoring/2026-05-15_dashboard-mobile-bottom-sheet.md` | Added a mobile-only quick input bottom sheet for the dashboard so selected slots can be tagged without scrolling to the desktop sidebar. Desktop sidebar behavior remains in place. Touch cancellation now guards `event.cancelable` to avoid browser intervention warnings while scrolling. The sheet now uses fixed `80dvh` mobile viewport height with border-box sizing, anchored to the visible screen bottom instead of the earlier 01:00 grid-line dynamic cap. Quick input category headers now use `-`, tag buttons use a compact wrapping row content-width layout, the tag modal category select uses readable 1rem text, and the category explanation modal now switches between Korean and English guide images by active language. | Fresh verification for 2026-05-23 language image adjustment: `conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short` -> `22 passed in 9.50s`; `git diff --check` -> exit 0. Manual mobile browser checks remain unverified. |
| Dashboard quick input state | `docs/plans/2026-05-20-dashboard-quick-input-state.md`, `docs/plans/2026-05-20-dashboard-tag-prompt.md`, `docs/refactoring/2026-05-20_dashboard-quick-input-state.md` | Updated the dashboard quick input form so the disabled save button has a gray visual state, `메모 (선택사항)` appears only inside the memo textarea placeholder, and selected slot info prompts the user to choose a tag next. | Fresh verification: `conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short` -> `20 passed in 8.93s`; `node --check apps/dashboard/static/dashboard/js/dashboard.js` -> exit 0; `git diff --check` -> exit 0. Manual browser color inspection remains unverified. |
| Stats life feedback toggle | `docs/plans/2026-05-15_stats-life-feedback-toggle-design.md`, `docs/plans/2026-05-15_stats-life-feedback-toggle.md`, `docs/refactoring/2026-05-15_stats-life-feedback-toggle.md` | Changed the stats page life feedback list from always-visible toast cards to a default-closed Bootstrap collapse section with count badge, accessible toggle attributes, and compact responsive styling. The expanded feedback cards use a horizontal wrapping row without sideways scrolling. Feedback generation and ordering remain unchanged. | Fresh verification: `conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py::TestLifeFeedbackToggleStructure --tb=short` -> `2 passed in 1.58s`; stats regression bundle -> `22 passed in 8.44s`; `node --check apps/stats/static/stats/js/stats.js` -> exit 0; `git diff --check` -> exit 0; full suite -> `176 passed in 78.74s (0:01:18)`. Manual mobile browser interaction remains unverified. |
| Korean-English i18n | `docs/refactoring/2026-04-28_i18n-phase1-5-execution-log.md` | Completed i18n phases for base/core, dashboard, tags, users, and stats using `LocalizableMessage` and JS catalog. | Document includes verification section and phase commits. |
| pytest migration | `docs/refactoring/2026-04-28_pytest-migration.md` | Converted unittest-style tests to pytest-native style and expanded fixtures. | Document reports `111 passed in 45.02s`. |
| Account recovery and email infrastructure | Code analysis: `apps/users/urls.py`, `apps/users/forms.py`, `apps/users/views.py`, `apps/core/email_backends.py`, `apps/users/templates/users/password/`, `apps/users/templates/users/recovery/` | Implemented password reset, username recovery, signup email capture/validation, and Resend HTTPS email backend. | Fresh verification: `conda run -n knou-life-diary pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_signup_email.py apps/core/test_email_backends.py ... --tb=short` included in a 50-test run, `50 passed in 29.65s`. |
| Auth cookie and login security phase 1 | `docs/plans/2026-05-19_auth-cookie-login-security-plan.md`, `docs/plans/2026-05-19_auth-cookie-login-security-implementation-plan.md`, `docs/refactoring/2026-05-19_auth-cookie-login-security.md` | Hardened web auth without changing the overall auth architecture: reduced remember-me to 14 days, made key production cookie settings explicit, added production password reset timeout, added cache-based throttling for password reset / username recovery / signup validation endpoints, removed trust in spoofable `X-Forwarded-For` for throttling, translated retry messages at request time, and added behavior tests for reset-token failure states and `django-axes` lockout/cooloff/reset behavior. | Fresh verification: focused auth regression `42 passed in 34.03s`; prod deploy check reported `System check identified no issues (0 silenced)`; `compilemessages` succeeded; `git diff --check` exit 0. |
| Google login | `docs/plans/2026-05-22-google-login-design.md`, `docs/plans/2026-05-22-google-login.md`, `docs/refactoring/2026-05-22-google-login.md` | Added a web login page "Google로 계속하기" entry point using `django-allauth`, configured the Google provider from environment variables, and preserved existing username/password routes. | Fresh verification: `conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py apps/users/test_google_login_settings.py --tb=short` -> `8 passed, 4 warnings in 1.46s`; `conda run -n knou-life-diary python manage.py check` -> `System check identified no issues`; `git diff --check` -> exit 0. Real Google OAuth round trip remains unverified pending Google Console credentials. Broader `apps/users/tests.py` still has 2 pre-existing axes lockout failures observed before this task. |
| Production deploy email readiness | `docs/plans/2026-05-15_production-deploy-email-readiness.md`, `docs/refactoring/2026-05-15_production-deploy-email-readiness.md`, `.github/workflows/deploy-pr.yml`, `lifeDiary/settings/prod.py`, `lifeDiary/test_prod_settings.py` | Added a production settings regression test, set production `DEBUG=False`, added deploy PR verification before PR creation/update, and documented that live recovery email delivery is deferred until a sender domain is purchased/configured and verified in Resend. | Fresh verification: `conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short` -> `3 passed`; prod deploy check -> `System check identified no issues`; `ruby ... YAML.load_file(...)` -> `yaml ok`; full suite -> `167 passed in 73.18s`. |
| Footer copyright LogBetter display | `docs/refactoring/2026-05-18_footer-copyright-logbetter.md` | Updated the shared footer copyright notice to use `LogBetter`, with a 2025 service-start year range and localized app names: Korean screens show `라이프 다이어리 © 2025-2026 LogBetter. All rights reserved.`, and English screens show `Life Diary © 2025-2026 LogBetter. All rights reserved.` for the current year. | Fresh verification: targeted RED failed before implementation for the missing footer strings; after implementation `conda run -n knou-life-diary pytest apps/core/tests.py::TestHomePage::test_home_page_renders_korean_footer_copyright apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_footer_copyright --tb=short` -> `2 passed in 0.64s`; focused core/i18n regression `conda run -n knou-life-diary pytest apps/core/tests.py apps/core/test_i18n_phase1.py --tb=short` -> `12 passed in 1.92s`. |
| Header utility controls and dashboard drag polish | `docs/plans/2026-05-19-header-utility-controls-design.md`, `docs/plans/2026-05-19-header-utility-controls.md`, `docs/refactoring/2026-05-19_header-utility-controls.md` | Added a stable header utility row beside the Life Diary brand for the language selector and text-based dark/light toggle, updated theme toggle accessibility attributes, and prevented dashboard time-slot text selection during drag. | Fresh verification: targeted RED failed before implementation with `3 failed`; after implementation the same targeted command passed with `3 passed in 0.75s`; focused regression `conda run -n knou-life-diary pytest apps/core/tests.py apps/core/test_i18n_phase1.py apps/dashboard/tests.py --tb=short` -> `29 passed in 8.74s`. Manual browser viewport and pointer-drag checks remain unverified. |
| Auth onboarding and signup UX | Code analysis: `apps/users/views.py`, `apps/users/urls.py`, `apps/users/templates/users/login.html`, `apps/users/templates/users/signup.html`, `apps/users/templates/users/welcome.html`, `apps/users/static/users/js/` | Implemented remember-me session behavior, signup-to-welcome flow, realtime username/email checks, password visibility/strength enhancements, and auth JS i18n catalog wiring. | Fresh verification: auth-related tests included in the same 50-test run, `50 passed in 29.65s`. |
| Stats goal cards and mobile tab structure tests | Code analysis: `apps/stats/templates/stats/life_feedback.html`, `apps/stats/templates/stats/_goal_accordion_item.html`, `apps/stats/test_goal_accordion.py`, `apps/stats/test_mobile_layout.py` | Implemented daily/weekly/monthly goal cards with per-card collapse behavior, weekly default expansion, count badges, and empty-state add links. Stats tab structure regression tests exist. | Fresh verification: stats goal/mobile tests included in the same 50-test run, `50 passed in 29.65s`. |
| Stats UserGoal query consolidation and performance guard | Code analysis: `apps/users/repositories.py`, `apps/stats/logic.py`, `apps/users/test_goal_repository.py`, `apps/stats/test_stats_perf.py` | Implemented `GoalRepository.find_grouped_by_period()` and stats context usage to fetch goals once and split by period; query target is guarded by performance tests. | Fresh verification: `conda run -n knou-life-diary pytest apps/users/test_goal_repository.py apps/stats/test_stats_perf.py --tb=short` -> `7 passed in 8.12s`. |
| Production console logging | `docs/refactoring/2026-05-24_production-console-logging.md` | Added production `LOGGING` so `DEBUG=False` deployments send framework warnings and request errors to the server console/deployment logs. | Fresh verification: RED `pytest lifeDiary/test_prod_settings.py::test_prod_settings_send_error_logs_to_console` -> missing `LOGGING`; GREEN same command -> `1 passed in 0.03s`; regression `pytest lifeDiary/test_prod_settings.py apps/users/test_prod_settings.py` -> `4 passed in 0.06s`; production check `python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR` -> `System check identified no issues (0 silenced).`; `git diff --check` -> exit 0. Live deployment logs were not verified. |
| Shared tag category header | `docs/plans/2026-05-24-shared-tag-category-header.md`, `docs/refactoring/2026-05-24_shared-tag-category-header.md` | Added a shared category header partial and reused it from dashboard server rendering, dashboard dynamic tag rendering, and tag-management dynamic rendering. Category headers now show `- 카테고리명` instead of category color icon boxes; tag color badges remain unchanged. | Fresh verification: RED focused command -> `2 failed, 1 passed`; GREEN focused command -> `3 passed in 1.87s`; `pytest apps/dashboard/tests.py apps/tags/tests.py --tb=short` -> `53 passed in 20.81s`; `node --check apps/dashboard/static/dashboard/js/dashboard.js` -> exit 0; `git diff --check` -> exit 0. Manual mobile browser rendering was not verified. |
| Tag color recommendations | `docs/plans/2026-05-24-tag-color-recommendations.md`, `docs/refactoring/2026-05-24_tag-color-recommendations.md` | Added a one-line `추천색상:` row to the tag create/edit modal with 14 swatches: red, orange, yellow, green, blue, navy, and purple, two options each. Swatch clicks update the existing color picker and HEX text input. | Fresh verification: RED focused command -> `2 failed`; GREEN focused command -> `2 passed in 0.07s`; `pytest apps/tags/tests.py apps/dashboard/tests.py --tb=short` -> `55 passed in 19.79s`; `node --check apps/core/static/core/js/tag.js` -> exit 0; `node --check apps/dashboard/static/dashboard/js/dashboard.js` -> exit 0; `git diff --check` -> exit 0. Manual browser inspection was not verified. |
| Password reset request host | `docs/plans/2026-05-24-password-reset-request-host.md`, `docs/refactoring/2026-05-24_password-reset-request-host.md` | Password reset emails now use the current request host via `domain_override=request.get_host()` instead of the default `django.contrib.sites` `example.com` domain. | Fresh verification: RED focused command -> email body contained `http://example.com/...`; GREEN focused command -> `1 passed in 1.69s`; `pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py --tb=short` -> `14 passed in 14.66s`; `git diff --check` -> exit 0. Manual email link click was not verified. |
| Login reCAPTCHA after failures | `docs/plans/2026-05-25-login-recaptcha-after-failures.md`, `docs/refactoring/2026-05-25_login-recaptcha-after-failures.md` | Local development disables axes lockout. Production keeps axes enabled but raises its hard-lock threshold above the reCAPTCHA threshold, and the login view now requires reCAPTCHA after 5 failed login attempts before allowing a correct-password login. | Fresh verification: RED focused command -> `5 failed`; GREEN focused command -> `5 passed in 16.98s`; final auth/settings regression `pytest apps/users/tests.py lifeDiary/test_prod_settings.py apps/users/test_auth_enhance_render.py apps/users/test_remember_me.py --tb=short` -> `23 passed in 37.19s`; `python manage.py check` and prod deploy check -> no issues; `git diff --check` -> exit 0. Real reCAPTCHA browser completion was not verified. |
| Merge description generator | `docs/plans/2026-05-25-merge-description-generator.md`, `docs/refactoring/2026-05-25_merge-description-generator.md` | Added a local `scripts/merge_description.py` helper that creates short merge descriptions from a commit body and related plan/refactoring docs, using `변경 요약`, `검증`, and `문서` sections instead of long commit-history dumps. | Fresh verification: RED `pytest scripts/test_merge_description.py --tb=short` -> missing module; GREEN same command -> `3 passed in 0.03s`; `python scripts/merge_description.py --commit HEAD` -> compact markdown output. GitHub workflow integration was not implemented. |
| Pytest translation compilation | `docs/plans/2026-05-25-pytest-compilemessages.md`, `docs/refactoring/2026-05-25_pytest-compilemessages.md` | Added a pytest startup hook that compiles Korean and English Django message catalogs before tests run. When GNU gettext is unavailable, it falls back to a Python-only `.po -> .mo` compiler so English locale tests still have the generated catalogs they need. | Fresh verification: `conda run -n knou-life-diary python -m pytest test_pytest_i18n_compile.py --tb=short` -> `2 passed in 0.03s`; `conda run -n knou-life-diary python -m pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short` -> `5 passed in 0.04s`; `PATH=/usr/bin:/bin /Users/yeongroksong/opt/anaconda3/envs/knou-life-diary/bin/python -m pytest apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_hero --tb=short` -> `1 passed in 1.77s`. |
| Legal policy pages | `docs/plans/2026-05-25-legal-policy-pages.md`, `docs/refactoring/2026-05-25_legal-policy-pages.md` | Added public `/privacy/` and `/terms/` pages plus footer links. The privacy page covers account/contact data, user-created diary/tag/goal/statistics data, recovery email flows, and functional/security/language cookies. The terms page covers account responsibility, acceptable use, user content responsibility, service changes, and contact path. English translations and i18n rendering tests were added for the new public copy, and the shared `<html lang>` now follows the active language. | Fresh verification: `pytest apps/core/tests.py apps/core/test_i18n_phase1.py --tb=short` -> `21 passed in 2.05s`; English-cookie render sample for `/`, `/privacy/`, and `/terms/` -> HTTP 200, `Content-Language: en`, `<html lang="en">`, English policy labels, no Korean policy labels; `git diff --check` -> exit 0. Legal review and manual browser inspection were not verified. |
| Account deletion grace period | `docs/plans/2026-05-26-account-deletion-grace-period.md`, `docs/refactoring/2026-05-26_account-deletion-grace-period.md` | Added 15-day account deletion grace period. Deletion request disables the user, login within the deadline cancels the request, and `purge_deleted_accounts` permanently deletes due accounts while retaining minimal audit data with masked email and original `User.date_joined`. Korean and English UI/messages are covered. | Fresh verification: RED service test -> missing `apps.users.account_deletion`; RED English i18n -> `3 failed`; GREEN focused account deletion -> `14 passed in 12.59s`; deletion + users i18n -> `24 passed in 21.15s`; `pytest apps/users --tb=short` -> `101 passed in 81.95s`; `python manage.py makemigrations --check --dry-run` -> `No changes detected`; `git diff --check` -> exit 0. Production scheduler and manual browser inspection were not verified. |

| Comprehensive review remediation | `docs/plans/2026-07-18_comprehensive-review-remediation-plan.md`, `docs/refactoring/2026-07-18_comprehensive-review-remediation.md` | Fixed ko catalog empty-msgstr regression (28 test failures), added `SECURE_PROXY_SSL_HEADER`/`CSRF_TRUSTED_ORIGINS`/CSP middleware to prod settings, inverted the dashboard->stats cache-invalidation dependency via a dashboard signal with a forbidden-import contract test, extracted `UserAccountRepository` for the direct-ORM auth spots in `apps/users/views.py`, and added Escape-close plus a dynamic focus trap to the mobile quick-input bottom sheet under the frontend dual-review gate. `TestLoginAxesBehavior` failures were not reproducible; no code change. | Fresh verification: full suite 256 tests exit 0; `manage.py check` no issues; prod deploy check `--fail-level ERROR` exit 0; `makemigrations --check` no changes; `node --check` exit 0. Unverified: real-device mobile browser Escape/Tab behavior (user risk acceptance pending), production `compilemessages` pipeline, live URL redirect check. |

## Active Plans

| Priority | Document | Scope | Next decision or action |
|---|---|---|---|
| High | `docs/plans/2026-05-07_desktop-auth-single-user-plan.md` | Desktop mode auto-login with one local user; block auth pages only in desktop settings. | Approve or revise scope, then create an integrated implementation plan before code work. |
| High | `docs/plans/2026-08-10_comprehensive-review-follow-up-plan.md` | Finish active design work, re-review the final UI, then remediate confirmed P0 ownership, cache, i18n, and operations defects. | User declares design complete; run the documented dual-review gate before frontend changes. |
| High | `docs/plans/2026-05-03_desktop-app-packaging-plan.md` | Package the Django app as macOS `.app` and Windows `.exe` with pywebview, waitress, and PyInstaller. | Partial code exists (`desktop/launcher.py`, `lifeDiary/settings/desktop.py`, `requirements-desktop.txt`), but no PyInstaller spec or release workflow was found in this pass. Confirm scope before continuing. |
| Medium | `docs/plans/2026-05-07_stats-dashboard-mobile-ui-plan.md` | Improve mobile stats/dashboard UX: stacked stats sections, goal accordion, feedback reveal, mobile tag bottom sheet. | Goal cards, dashboard mobile bottom sheet, and default-closed stats feedback reveal are implemented and covered by focused tests. Re-check item #1 expectations before marking complete because current tests preserve tab structure rather than requiring all mobile panes to be stacked. |
| Medium | `docs/plans/2026-04-26_stats-tab-performance-plan.md` | Measure and optimize stats tab backend queries and chart rendering. | Backend query consolidation and query-count guards are implemented and verified. Frontend chart lazy render was not confirmed in this pass. |
| Strategic | `docs/plans/2026-05-06_distribution-and-monetization-plan.md` | Public distribution, operational infrastructure, monetization experiment, portfolio metrics. | Treat as roadmap; each phase requires explicit approval. |
| Strategic | `docs/plans/2026-05-28-ad-revenue-marketing-strategy.md` | Advertising-only marketing and revenue strategy for covering roughly KRW 30,000/month in server operating costs through public content pages, conservative ad placement, and weekly revenue/traffic measurement. | Treat as planning scope. Before implementing ad code, approve the content/policy/ad-slot phase and keep ads off private dashboard, stats, auth, and account workflows. |

## Code Found But Not Fully Completed

| Area | Files found | Current read |
|---|---|---|
| Desktop packaging foundation | `desktop/launcher.py`, `lifeDiary/settings/desktop.py`, `requirements-desktop.txt` | Basic desktop runtime foundation exists: desktop settings, user data directory, local SQLite path, persisted secret key, axes disabled in desktop auth backends/middleware, waitress server, pywebview launcher, migrate, and local collectstatic. The broader packaging plan still appears incomplete because `desktop/lifediary.spec`, desktop README, and release workflow were not found. |
| Desktop single local user auth | `docs/plans/2026-05-07_desktop-auth-single-user-plan.md`, `lifeDiary/settings/desktop.py`, `desktop/launcher.py` | The desktop settings/launcher exist, but the planned local user bootstrap, desktop auth middleware, context processor, auth-page blocking, and logout hiding were not found in this pass. Keep this as active planned work. |

## Superseded Or Historical Plans

| Document | Current status | Superseded or informed by |
|---|---|---|
| `prompt_plan.md` | Superseded as implementation plan | `docs/refactoring/2026-04-28_i18n-phase1-5-execution-log.md` is the current i18n execution record. |
| `docs/plans/2026-05-01_account-recovery-plan.md` | Completed by code analysis and fresh targeted tests | Password reset, username recovery, signup email validation, and Resend backend are implemented. |
| `docs/plans/2026-04-26_stats-goal-repo-refactor-plan.md` | Completed by code analysis and fresh targeted tests | `GoalRepository.find_grouped_by_period()` and stats context usage are implemented. |
| `docs/plans/2026-04-09_light-ddd-plan.md` | Largely completed / historical | Phase 0-2 logs and later architecture execution logs. |
| `docs/plans/2026-04-11-business-logic-refactor-design.md` | Historical design | Later repository/domain/use case execution logs. |
| `docs/plans/2026-04-11-business-logic-refactor.md` | Historical implementation plan | Later architecture and phase logs. |
| `docs/plans/2026-04-20_architecture-and-cost-plan.md` | Historical plan | `docs/refactoring/2026-04-20_phase3-4-execution-log.md` and `2026-04-21_post-phase4-state-update.md`. |
| `docs/plans/2026-04-21_architecture-and-cost-plan.md` | Snapshot / historical | Use as reference, not the primary active backlog. |
| `docs/plans/2026-04-20_frontend-template-remediation-plan.md` | Completed / historical | `docs/refactoring/2026-04-21_frontend-template-refactor-log.md`. |
| `docs/plans/2026-04-20_review-remediation-plan.md` | Mostly historical | Later architecture, frontend, pytest, and security execution logs cover much of the remediation. |
| `docs/plans/2026-04-11-home-main-ui-design.md` | Historical design | Check current UI before using. |
| `docs/plans/2026-04-11-home-main-ui.md` | Unknown / likely historical | No direct execution log was matched in this pass. |

## Reference Documents

| Document | Purpose |
|---|---|
| `AGENTS.md` | Operating guide for agent roles, project file flow, TDD rules, review gates, and completion reporting. |
| `docs/architecture/2026-04-21_business-logic-and-architecture-guide.md` | Product and architecture guide for LifeDiary's business flow, domain model, and app responsibilities. |
| `docs/refactoring/2026-04-08_code-review.md` | Original 2026-04-08 review findings and action items. |
| `docs/refactoring/2026-04-09_business-logic-analysis.md` | Early business logic analysis and service-layer refactoring direction. |
| `docs/refactoring/2026-04-20_backend-flow-and-improvements.md` | Backend flow and improvement snapshot before later phase completion. |
| `docs/refactoring/2026-04-21_backend-flow-and-improvements.md` | Updated backend flow and remaining improvement snapshot. |
| `docs/2026-07-18_comprehensive-project-review.md` | Cross-cutting review (security, architecture, accessibility, desktop, product-direction drift) and the currently-failing test suite regression. Read this before trusting older "N passed" evidence in this file. |

## Deferred Or Later Work

| Area | Source | Deferred work |
|---|---|---|
| i18n | `docs/refactoring/2026-04-28_i18n-phase1-5-execution-log.md` | Japanese support, DRF API behavior, cache key locale split, and Chart.js locale configuration. |
| Security | `docs/security/2026-04-21_xss-bruteforce-sri-remediation.md` | CSP, stronger cookie/security flags, production debug review, and login failure notifications. |
| pytest | `docs/refactoring/2026-04-28_pytest-migration.md` | More locale parametrization, possible `factory_boy`, and optional locale leak guard fixture. |
| Desktop distribution | `docs/plans/2026-05-06_distribution-and-monetization-plan.md` | Code signing, notarization, auto-update, operational metrics, and monetization phases. |
| Account recovery | `docs/plans/2026-05-01_account-recovery-plan.md` | Social login, email verification, and email backfill policy. |
| Production auth security | `docs/refactoring/2026-05-19_auth-cookie-login-security.md` | `SECURE_PROXY_SSL_HEADER`, deployed `Set-Cookie` header inspection, and live sender-domain verification remain deferred. `ALLOWED_HOSTS`는 2026-08-12에 도메인 변경으로 갱신됐고 운영에서 동작이 확인됐다(위 "Production Domain" 참조). `CSRF_TRUSTED_ORIGINS`는 이 구성에서 불필요하다. |
| Account recovery email delivery | `docs/refactoring/2026-05-15_production-deploy-email-readiness.md` | Live Resend recovery email delivery is deferred until a sender domain is purchased/configured, DNS records are set, and Resend marks the domain as verified. No live delivery verification has been performed. |
| P0 시안 잔여 | `docs/refactoring/2026-08-01_p0-sian-redesign.md` | 웹폰트 CDN 탑재, `Tag.color` 컬럼 드롭, 데스크톱 슬롯 19px의 WCAG 2.5.8 격차. 시안 6a의 행 끌어 순서 바꾸기는 **채택하지 않기로 결정**(2026-08-12). |
| 시안 정합 잔여 | `docs/refactoring/2026-08-12_sian-conformance-stage7.md` | `style.css`의 `.settings-row + /* 주석 */ .home-daygrid` 인접 형제 결합자 오류, 확인 모달 없는 태그 삭제 경로의 이중 제출 가드(`tag.js`), 삭제 모달 이중 제출 창, `_table_row_actions.html`의 44px 미달 버튼(메모 화면), sessionStorage 차단 환경에서 온보딩 STEP3 취소 버튼 부재를 알리지 않음. |

## Next Recommended Work

0. 현재 변경 중인 디자인 시안 작업을 완료한 뒤
   `docs/plans/2026-08-10_comprehensive-review-follow-up-plan.md`의
   post-design dual review gate를 수행한다.
0-1. P0 데이터 무결성·캐시·i18n·계정 삭제 스케줄링 결함은 디자인 완료 후
   별도 승인된 백엔드/운영 계획으로 처리한다.
1. `feat/p0-onboarding` (6·7단계) 리뷰와 머지 결정. PR #40 은 머지 완료.
1-0. `production` 에만 있던 도메인 수정 2건이 `main` 에 반영되도록
   이 PR 을 먼저 넣는다. 위 "Production Domain" 절 참조.
1-1. 결정 대기 세 건 — 웹폰트(Pretendard·IBM Plex Mono) CDN 탑재 여부,
   `Tag.color` 컬럼 드롭 여부, 태그 관리 화면에 카테고리 색을 어떤 형태로
   되살릴지(7단계에서 색 표시가 사라졌다).
2. Choose one active plan as the next approved scope.
3. Before code work, create an integrated plan document that combines analyst requirements, design, risks, TDD checkpoints, and verification commands.
4. For a small implementation start, consider either:
   - `docs/plans/2026-05-07_desktop-auth-single-user-plan.md`; or
   - the remaining unimplemented items from `docs/plans/2026-05-07_stats-dashboard-mobile-ui-plan.md`.
5. After each completed implementation, update this `docs/project-status.md` file and write the required refactoring document.

## Fresh Verification From This Status Update

Commands run on 2026-08-12 (시안 정합 7단계 종료 시점):

```bash
conda run -n knou-life-diary pytest
# 466 passed in 270.46s

conda run -n knou-life-diary python manage.py check
# System check identified no issues (0 silenced).

conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
# No changes detected

node --check apps/tags/static/tags/js/tag_list.js
# exit 0

for f in locale/*/LC_MESSAGES/*.po; do msgfmt --check-format -o /dev/null "$f"; done
# 4개 파일 모두 통과, fuzzy 0건, 미번역 0건
```

브라우저 확인은 각 단계 실행 로그에 있다. 이 문서는 명령 증거만 싣는다.

Commands run on 2026-08-02:

```bash
conda run -n knou-life-diary pytest
# 405 passed

conda run -n knou-life-diary python manage.py check
# System check identified no issues (0 silenced).

conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
# No changes detected

node --check apps/core/static/core/js/tag.js
node --check apps/dashboard/static/dashboard/js/dashboard.js
node --check apps/stats/static/stats/js/stats.js
# ok
```

브라우저 실측(크롬 MCP): 대시보드 접근성 96 · 분석 100 ·
Best Practices 100 · SEO 100 · agentic-browsing 100.
대시보드 LCP 165ms · 분석 401ms · CLS 둘 다 0.00. 콘솔 에러 0건.

`TestLoginAxesBehavior::test_cooloff_allows_login_again`은 간헐적으로
실패한다(타이밍 의존). 2026-07-18 기록과 같은 증상이며 이번 변경과 무관함을
stash 실행으로 확인했다.

---

Commands run on 2026-05-14:

```bash
conda run -n knou-life-diary pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_signup_email.py apps/core/test_email_backends.py apps/users/test_remember_me.py apps/users/test_realtime_validation.py apps/users/test_welcome.py apps/users/test_auth_enhance_render.py apps/users/test_jsi18n_auth.py apps/stats/test_goal_accordion.py apps/stats/test_mobile_layout.py --tb=short
# 50 passed in 29.65s

conda run -n knou-life-diary pytest apps/users/test_goal_repository.py apps/stats/test_stats_perf.py --tb=short
# 7 passed in 8.12s
```

Commands run on 2026-05-15:

```bash
conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short
# 3 passed in 0.07s

DJANGO_SECRET_KEY=test-ci-secret-value-for-deploy-readiness-checks-only-1234567890 DB_NAME=test_db DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost DB_PORT=6543 RESEND_API_KEY=re_test_dummy DEFAULT_FROM_EMAIL='LifeDiary <noreply@example.com>' conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
# System check identified no issues (0 silenced).

ruby -e "require 'yaml'; YAML.load_file('/Users/yeongroksong/Desktop/study/project/knou/.github/workflows/deploy-pr.yml'); puts 'yaml ok'"
# yaml ok

conda run -n knou-life-diary pytest --tb=short
# 167 passed in 73.18s
```

Commands run on 2026-05-19:

```bash
conda run -n knou-life-diary pytest apps/users/test_remember_me.py apps/users/test_prod_settings.py apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_realtime_validation.py apps/users/tests.py --tb=short
# 42 passed in 34.03s

conda run -n knou-life-diary pytest apps/users/test_realtime_validation.py --tb=short
# 16 passed in 4.49s

conda run -n knou-life-diary python manage.py compilemessages
# locale/en, locale/ko catalogs compiled successfully

DJANGO_SECRET_KEY=test-ci-secret-value-for-deploy-readiness-checks-only-1234567890 DB_NAME=test_db DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost DB_PORT=6543 RESEND_API_KEY=re_test_dummy DEFAULT_FROM_EMAIL='LifeDiary <noreply@example.com>' conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
# System check identified no issues (0 silenced).

git diff --check
# exit 0
```

The default local `python -m pytest ...` command failed before test collection because the default Python environment did not initialize Django settings/apps correctly. The conda environment used by project documents, `knou-life-diary`, was used for the successful verification runs.
