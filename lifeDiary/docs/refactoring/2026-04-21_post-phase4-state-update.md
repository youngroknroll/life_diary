# 2026-04-21 Post-Phase4 프로젝트 상태 업데이트

> 작성일: 2026-04-21
> 작성 동기: 선행 문서 3종(아키텍처 가이드 / 백엔드 flow / 비용·아키텍처 계획)이 커버하지 못한 변경분을 정리한다.
> 참조:
> - `docs/architecture/2026-04-21_business-logic-and-architecture-guide.md`
> - `docs/refactoring/2026-04-20_backend-flow-and-improvements.md`
> - `docs/plans/2026-04-20_architecture-and-cost-plan.md`
> - `docs/security/2026-04-21_xss-bruteforce-sri-remediation.md`

---

## 1. 이 문서의 역할

선행 문서 3종은 각각 다음 시점에 머물러 있다.

| 문서 | 기준일 | 포착 범위 |
|------|--------|-----------|
| 비즈니스 로직·아키텍처 가이드 | 2026-04-21 | 비즈니스 관점·레이어 구조 (보안/i18n 미포함) |
| Backend Flow & Improvements | 2026-04-20 | Phase 3 진입 직전 개선점 목록 |
| Architecture & Cost Plan | 2026-04-20 | Phase 3-A ~ Phase 4 계획(문서 내부에 완료 표시) |

그 이후 머지된 코드 변경(Phase 3-A ~ Phase 4 실제 구현, 보안 수정, i18n Phase 0, 프런트엔드 템플릿 정리, 테스트 인프라 전환)은 한곳에 모인 기록이 없다. 이 문서가 그 gap을 닫는다.

---

## 2. 구조 현황 스냅샷 (2026-04-21 기준)

### 2.1 앱별 레이어 도달 상태

| 앱 | Repository | Domain Service | Use Case | Port (Protocol) | Command DTO |
|----|-----------|----------------|----------|-----------------|-------------|
| `dashboard` | O | - | O (`UpsertTimeBlocksUseCase` 외) | O (`dashboard/ports.py`) | O (`dashboard/commands.py`) |
| `tags` | O | O (`TagPolicyService`) | O | O (`tags/ports.py`) | - |
| `users` | O | O (`GoalProgressService`) | O (CRUD 4종) | - | DTO 기반 분리 완료 (24a009f) |
| `stats` | 다른 앱 Port 경유 | - | O (`GetStatsContextUseCase`) | Port 소비자 | - |
| `core` | 공통 유틸 | - | - | - | - |

Backend Flow 문서의 "남은 과제" 열(`Use Case 미도입`, `Aggregation Service 미도입`)은 모두 해소됐다.

### 2.2 집계 레이어

`stats/logic.py`에 한 덩어리로 있던 `StatsCalculator`는 분해 완료.

```
apps/stats/aggregation/
├─ calculator.py   # 공통 헬퍼
├─ daily.py
├─ weekly.py
├─ monthly.py
└─ analysis.py
```

`get_stats_context`는 이제 조립기로만 동작한다. `fill_empty_slots_*` 4종·`add_unclassified_data` data_type 분기는 각 모듈로 분산됐다.

### 2.3 디렉터리 추가분

선행 문서 이후 새로 생긴 모듈.

```
apps/dashboard/ports.py
apps/dashboard/commands.py
apps/dashboard/use_cases.py
apps/dashboard/test_use_cases.py
apps/tags/ports.py
apps/tags/use_cases.py
apps/tags/templatetags/           # tag_dot / tag_badge 커스텀 태그
apps/users/use_cases.py
apps/users/test_use_cases.py
apps/stats/use_cases.py
apps/stats/aggregation/           # 4-way 분해
apps/stats/life_feedback.py       # 구 ai_feedback 리네임
```

---

## 3. Backend Flow 개선점 체크리스트 — 완료/미완 대조

2026-04-20 문서의 17개 개선점 중 현재 상태.

### 3.1 P1 (동작 위험·무결성)

| # | 항목 | 상태 | 근거 |
|---|------|------|------|
| 1 | `bulk_create` + `bulk_update` 트랜잭션 누락 | **해결** | `UpsertTimeBlocksUseCase.execute`에 `@transaction.atomic` 적용 (Phase 3-C) |
| 2 | 주간 비교 dead path | **제거** | `d2656d6` 커밋에서 `prev_weekly_stats` 경로 삭제 |
| 3 | `bulk_create`의 `full_clean` 우회 | **유지 + 주석화 필요** | 뷰·유스케이스 검증이 막고 있으나 모델 `clean()` 주석 미추가 — 잔여 작업 |

### 3.2 P2 (구조적 결합)

| # | 항목 | 상태 |
|---|------|------|
| 4 | Use Case 계층 부재 | **해결** (dashboard → tags → users 순으로 도입) |
| 5 | `StatsCalculator` 비대 | **해결** (Phase 4에서 `aggregation/` 분해) |
| 6 | 피드백 입력 결합(`FeedbackInput` DTO) | **미도입 결정** — 현재 규모에서 오버엔지니어링으로 판단, 계획 문서 §5 Phase 4에 근거 명시 |
| 7 | `users → stats` 역방향 의존 | **해결** — `GetMyPageUseCase` 도입 후 stats는 read-only로 호출 |
| 8 | `stats/services.py` 개명 | **미진척** — 파일은 존재하되 책임이 여전히 얕음. 우선순위 낮음 |

### 3.3 P3 (일관성)

| # | 항목 | 상태 |
|---|------|------|
| 9 | API 응답 포맷 불일치 | **해결** (`f7b6d66` success_response 플랫 통일) |
| 10 | `UserGoal.clean` 중복 | **부분** — 모델 제약 유지, Form 측 중복 정리 여부 재확인 필요 |
| 11 | `TagPolicyService` 퍼사드 중복 | **미진척** (영향도 낮음) |
| 12 | `_get_user_tag_queryset` 래퍼 | **미진척** |
| 13 | `NoteRepository` 정렬 중복 | **미진척** |
| 14 | `TimeBlock` 시간 상수 하드코딩 | **미진척** — `core.utils`의 `MINUTES_PER_SLOT` 등 상수 활용 안 됨 |

### 3.4 P4 (성능·관측성)

| # | 항목 | 상태 |
|---|------|------|
| 15 | 주간 7쿼리 | **해결** — `find_by_date_range` 단일 쿼리 (Phase 3-C) |
| 16 | 로깅 구조화 | **미진척** |
| 17 | 카테고리 변경 권한 검증 | **미진척** — `TagPolicyService.validate_category_change` 미도입 |

---

## 4. 아키텍처 가이드에 반영돼야 할 축 3개

2026-04-21 가이드 문서는 다음 세 축을 설명에서 빠뜨리고 있다. 다음 갱신 시 **8장 한계/9장 면접 포인트** 사이에 삽입하면 자연스럽다.

### 4.1 보안 베이스라인 (2026-04-21 완료)

- 저장형 XSS: `stats/index.html`의 `|safe` 블록을 Django `json_script`로 교체. 사용자 입력(태그명)이 섞인 JSON은 `<script id>` 요소에 텍스트로만 주입된다.
- 브루트포스 방어: `django-axes==7.0.1` 도입. 인증 백엔드가 2단계가 됐다.
  ```
  AUTHENTICATION_BACKENDS = [
      "axes.backends.AxesStandaloneBackend",
      "django.contrib.auth.backends.ModelBackend",
  ]
  AXES_FAILURE_LIMIT = 5
  AXES_COOLOFF_TIME = 1
  AXES_RESET_ON_SUCCESS = True
  ```
  테스트는 `conftest.py`에서 `AXES_ENABLED = False`로 비활성화해 우회한다.
- CDN SRI: Chart.js·chartjs-adapter-date-fns·htmx·Alpine.js 4종에 `integrity` 해시 추가. Alpine은 `@3.x.x` → `@3.14.9` 고정 버전 전환.
- 상세 기록: `docs/security/2026-04-21_xss-bruteforce-sri-remediation.md`.

### 4.2 i18n Phase 0

- `LANGUAGE_CODE = "ko-kr"`, `LANGUAGES = [("ko", ...), ("en", ...)]`, `USE_I18N = True`.
- `locale/en/LC_MESSAGES/` 디렉터리 구축.
- `lifeDiary/urls.py`에 `path("i18n/", include("django.conf.urls.i18n"))` 포함.
- 앱별 문자열 번역 로드맵은 auto-memory(`project_i18n.md`)에서 관리 중. 507+ 문자열 / 45 파일.

### 4.3 캐시 백엔드 결정

계획 문서 §3.4는 `LocMemCache`를 기본으로 제안했으나, **실제 구성은 `FileBasedCache`** 로 가 있다.

| 환경 | 설정 파일 | BACKEND | LOCATION |
|------|-----------|---------|----------|
| dev | `settings/dev.py` | `filebased.FileBasedCache` | `BASE_DIR/.cache` |
| prod | `settings/prod.py` | `filebased.FileBasedCache` | `/tmp/lifediary-cache` |

선택 사유: gunicorn `--workers=2 --threads=4` 구성에서 LocMemCache는 워커 간 캐시 공유가 안 된다. FileBasedCache가 계획 문서 §8 리스크 체크리스트의 "워커 간 공유 불가" 이슈에 대한 실제 채택 해법.

---

## 5. 테스트 인프라

- pytest-django 기반으로 수집 통합(`8dd02d5`).
- Use Case 전용 테스트 분리: `apps/dashboard/test_use_cases.py`, `apps/users/test_use_cases.py`.
- 2026-04-21 기준 `pytest`: **55 passed**(보안 수정 검증 당시 수치, 보안 문서 §검증 증거 참조).

```bash
pytest
# 55 passed in 5.89s
```

---

## 6. 프런트엔드/템플릿 정리

선행 문서가 아키텍처 중심이라 언급하지 않은 프런트엔드 변경 요약.

- 날짜 선택기 공통 partial 추출 (`f30bc9f`).
- 인라인 스타일 제거, Bootstrap 유틸리티로 통합 (`0099a36`).
- `tags/templatetags/`에 `tag_dot`, `tag_badge` 커스텀 템플릿 태그 분리 (`ee546a8`).
- `usergoal_list` 중복 테이블 partial 추출 (`876499d`).
- `usernote_form` Bootstrap `form-control` 적용 (`49f7e72`).
- 리네임: `ai_feedback` → `life_feedback` (`c72ddf0`) — 가이드 문서 §3.6의 "규칙 기반 피드백" 섹션과 이름을 맞춤.

관련 상세: `docs/refactoring/2026-04-15-inline-js-extraction.md`, `docs/refactoring/2026-04-21_frontend-template-refactor-log.md`.

---

## 7. 남은 과제

### 7.1 운영 보안 (우선순위 높음)

| 항목 | 상태 | 비고 |
|------|------|------|
| `settings/prod.py`의 `DEBUG = True` | **위험** | 최근 `3c19106 production debug` 커밋에서 일시적으로 켜짐. 배포 전 반드시 `False` 복구 |
| CSP 헤더 | 미도입 | `django-csp` 검토 |
| 로그인 실패 알림 | 미구현 | axes 이벤트 로깅 연결 필요 |
| 세션/CSRF 쿠키 플래그 | 부분 | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`는 prod에 있음. `SESSION_COOKIE_HTTPONLY`·`SAMESITE` 명시 필요 |
| 비밀번호 정책 강화 | 기본값 수준 | 최소 길이·특수문자 요구 재검토 |

### 7.2 측정/관측

계획 문서 §9가 제안한 `apps/core/middleware.py`의 `MetricsMiddleware`는 아직 미구현(`apps/core/`에 `middleware.py` 없음). Phase 3-A ~ 4의 비용 개선 효과를 수치로 검증하려면 이 단계가 남아 있다.

### 7.3 백엔드 자잘한 정리

Backend Flow 문서의 P3-#10~14, P4-#16~17, P2-#8이 열려 있다. 단일 커밋으로 한 번에 마감할 수 있는 크기.

### 7.4 i18n Phase 1+

메시지 추출·영어 번역 적용은 이번 문서의 범위 밖. auto-memory `project_i18n.md`의 로드맵으로 계속 추적.

---

## 8. 참고: Phase 실행 결과와 계획 문서의 차이

`docs/plans/2026-04-20_architecture-and-cost-plan.md`는 Phase 3-A ~ 4 전부 "완료"로 마킹됐으나, 문서의 **목표 지표**(성공 지표 §6)는 실제 배포 측정 없이 가설 상태로 남아 있다. `MetricsMiddleware`가 붙으면 비교 숫자가 생긴다.

- Before/After egress, 쿼리 수, `/stats/` 응답 시간: 측정 미수행
- 캐시 히트율: 측정 미수행
- 구조 지표(grep 기반): 실측 가능

구조 지표 재확인 명령:

```bash
# 뷰가 models를 직접 import하지 않는지 (0 유지 목표)
grep -rn "from .models import\|from apps\..*models import" \
  apps/*/views.py apps/stats/logic.py

# 뷰가 다른 앱 logic/views를 import하지 않는지 (Phase 3-E 이후 0)
grep -rn "from apps\.stats\.logic\|from apps\.\(stats\|dashboard\|tags\|users\)\.views" apps/*/views.py
```

---

## 9. 요약

- Phase 3-A ~ Phase 4의 설계는 **코드에 반영 완료**. 계획 문서의 완료 표시는 실제와 일치한다.
- 아키텍처 가이드 문서는 비즈니스·레이어 설명에 집중돼 있어, 2026-04-21 당일 완료된 **보안 수정**과 **i18n Phase 0**, **FileBasedCache 결정**이 빠져 있다. 다음 가이드 갱신 시 4장 "아키텍처 축"에 보안/국제화/캐시 결정 섹션이 필요하다.
- 운영 배포 전 우선 처리 항목: `prod.py`의 `DEBUG = True` 원복, `MetricsMiddleware` 도입으로 비용 개선 효과 실측, 세션/CSRF 쿠키 플래그 보강.
