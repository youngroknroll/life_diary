# 2026-07-18 전수 검토 지적사항 수정 실행 로그

> 계획: `docs/plans/2026-07-18_comprehensive-review-remediation-plan.md`
> 근거 리뷰: `docs/2026-07-18_comprehensive-project-review.md`
> 제외(사용자 지시): 타임슬롯 그리드 키보드 접근, aria-live 알림

## 변경 요약

| # | 항목 | 결과 |
|---|---|---|
| 1 | ko 카탈로그 빈 msgstr | `msgen`으로 `django.po` 265건 + `djangojs.po` 112건 항등 번역 채움. 전체 스위트 28건 실패 → 0건 |
| 2 | `TestLoginAxesBehavior` | **코드 수정 없음** — 단독 3회 + 전체 스위트 3회 연속 통과, 재현 불가. 검토 시점의 캐시/타이밍 요인으로 추정 |
| 3 | `SECURE_PROXY_SSL_HEADER` | `prod.py`에 `("HTTP_X_FORWARDED_PROTO", "https")` 추가 |
| 4 | `CSRF_TRUSTED_ORIGINS` | `["https://lifediary.onrender.com"]` — 단일 프로덕션 호스트만 신뢰하기로 결정·기록 |
| 5 | CSP 헤더 | 신규 의존성 없이 `apps/core/middleware.py::ContentSecurityPolicyMiddleware` 추가, prod 전용 정책. 설정 없으면 no-op(dev/desktop 무영향) |
| 6 | dashboard↔stats 양방향 의존 | `apps/dashboard/signals.py::time_blocks_changed` 시그널로 역전. dashboard의 `apps.stats` import 제거, `apps/stats/receivers.py`가 구독. 금지 import 계약 테스트 추가 |
| 7 | users/views.py 레이어링 | `UserAccountRepository` 신설(탈퇴 유예 조회, 이메일 계정 조회, username/email 중복 확인). 뷰의 직접 ORM 4개 지점 치환, `get_user_model` import 제거 |
| 8 | 바텀시트 Escape + 포커스 트랩 | `dashboard.js`에 `handleQuickInputSheetKeydown` 추가. 열림 전이당 1회 등록, 닫힘 2경로(일반 + 리사이즈 강제) 해제, IME `isComposing` 가드, `.modal.show` 중첩 모달 가드, 매 Tab 포커스 집합 재계산 |

## 변경 파일

- `locale/ko/LC_MESSAGES/django.po`, `djangojs.po` (`.mo`는 git 미추적)
- `lifeDiary/settings/prod.py`, `lifeDiary/test_prod_settings.py`
- `apps/core/middleware.py` (신규), `apps/core/test_csp_middleware.py` (신규)
- `apps/dashboard/signals.py` (신규), `apps/dashboard/use_cases.py`,
  `apps/dashboard/test_domain_boundaries.py` (신규)
- `apps/stats/apps.py`, `apps/stats/receivers.py` (신규),
  `apps/stats/test_receivers.py` (신규)
- `apps/users/repositories.py`, `apps/users/views.py`
- `apps/dashboard/static/dashboard/js/dashboard.js`
- `docs/plans/2026-07-18_comprehensive-review-remediation-plan.md` (계획+리뷰 증거)

## TDD 증거

| Scenario | Red | Green |
|---|---|---|
| SEC-01 프록시 SSL 헤더 | `AttributeError: no attribute 'SECURE_PROXY_SSL_HEADER'` | 8 passed (계약 5 + web 2 + 기존) |
| SEC-02 CSRF 신뢰 오리진 | `AttributeError: no attribute 'CSRF_TRUSTED_ORIGINS'` | 동일 실행에 포함 |
| SEC-03/04 CSP | `ModuleNotFoundError: apps.core.middleware` | `lifeDiary/test_prod_settings.py apps/core/test_csp_middleware.py` → `8 passed in 0.89s` |
| ARCH-01 금지 import | dashboard→stats import 위반 검출로 실패 | boundary+receiver `2 passed in 0.05s` |
| ARCH-02 시그널 캐시 무효화 | `ModuleNotFoundError: apps.dashboard.signals` | 동일 실행에 포함 |
| USR-01 행동 보존 리팩터링 | (신규 행동 없음 — Red 불요) | `pytest apps/users` EXIT=0 |
| I18N-01 ko 문자열 | 전체 스위트 28건 실패 (기존) | 전체 스위트 0 실패 |

주의: msgen 직후 첫 전체 실행은 여전히 28건 실패였다. 시작 시점에 stale `.mo`가
재컴파일 전에 로드·캐시된 잔여 효과로, 두 번째 실행부터 완전히 해소되었다.
`.po`가 소스이고 `.mo`는 시작 시 `conftest.py`가 재컴파일한다.

## 최종 검증 (fresh, 2026-07-18)

- 전체 회귀: `conda run -n knou-life-diary pytest -q` → **256건 전부 통과, EXIT=0**
  (pytest 요약 라인이 출력되지 않는 리포터 문제가 있어 종료 코드와 진행
  표시 100%로 판정 — 검토 문서의 "비정상 종료" 관찰과 동일 증상이며 실패와
  무관)
- `python manage.py check` → no issues
- prod deploy check(`--fail-level ERROR`) → EXIT=0 (W009 경고 1건은 로컬 .env의
  개발용 SECRET_KEY에 대한 환경 의존 경고로 이번 변경과 무관)
- `makemigrations --check --dry-run` → No changes detected
- `node --check apps/dashboard/static/dashboard/js/dashboard.js` → exit 0

## 프론트엔드 이중 리뷰 게이트 (항목 8)

- 사전: WED 경험 사양(수용 기준 11개) + BIR 상호작용 기준(High 3, Medium 2
  리스크) — 구현 착수 전 산출 완료, 계획 문서에 기록.
- 사후: WED = 11/11 정적 추적 일치이나 실기기 증거 부재로 **Unverified**,
  BIR = 10/10 **소스 수준 Conforms**, 런타임(실기기 Tab 순환, VoiceOver/
  TalkBack, 중첩 모달 Escape 레이스)은 Unverified.
- QVL 결정: 코드 수준 완료. 실기기 모바일 브라우저 검증은 미수행 —
  **사용자의 잔여 리스크 수용 필요** (기존 바텀시트 작업들과 동일한 한계).

## 미검증/미해결 항목

- 실기기 모바일 브라우저에서 Escape/Tab 트랩 동작 (위 게이트 결정 참조)
- 프로덕션 배포 파이프라인의 `compilemessages` 실행 여부 및 실서비스 화면의
  빈 문자열 노출 여부 (검토 문서의 미결 질문, 배포 로그 확인 필요)
- 배포된 URL에 대한 `curl -I` 리다이렉트 확인 (SECURE_PROXY_SSL_HEADER 적용
  후 실배포 시점에 확인)
- pytest 요약 라인 미출력 리포터 문제 (기능 영향 없음, 원인 미규명)

## Deferred

계획 문서의 Deferred Refactoring Notes 3건 참조: users/views.py 전면 분할,
CSP nonce 엄격화, 로그인 실패 관측성.
