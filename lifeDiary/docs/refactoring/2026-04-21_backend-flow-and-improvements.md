# 2026-04-21 Backend Flow & Improvements

> 작성일: 2026-04-21
> 범위: `dashboard`, `tags`, `users`, `stats`, `core` 앱의 현재 백엔드 로직 플로우와 잔여 개선점
> 선행 문서: `docs/refactoring/2026-04-20_backend-flow-and-improvements.md` (Phase 3 진입 직전 시점), `docs/plans/2026-04-21_architecture-and-cost-plan.md`

---

## 1. 현재 레이어 구조

Phase 3-A ~ 4 적용 후 안정화된 구조.

```
[Interface]        views.py                         ← HTTP 파싱/응답
       │
       ▼
[Use Case]         use_cases.py                     ← 단일 기능 흐름 조립, @transaction.atomic
       │
       ├──► [Domain Service]  domain_services.py    ← 정책 판단, 계산
       ├──► [Repository]      repositories.py       ← ORM 쿼리 전담
       ├──► [Port/Protocol]   ports.py              ← 앱 경계 추상화
       └──► [Command DTO]     commands.py           ← 입력 경계 검증 (Pydantic)
       │
       ▼
[Model]            models.py                        ← 제약/유효성
```

| 계층 | 도입 앱 | 비고 |
|------|---------|------|
| Repository | `dashboard`, `tags`, `users` | `stats`는 read-only 경로로 타 앱 Repository를 Port 경유 |
| Domain Service | `GoalProgressService`(users), `TagPolicyService`(tags) | 추가 도입 여부는 규칙 증가 시 재검토 |
| Use Case | `dashboard`, `tags`, `users`, `stats` 전부 도입 | 뷰 4~8줄 수준으로 축소 |
| Port (Protocol) | `dashboard/ports.py`(TimeBlockReader/Writer), `tags/ports.py`(TagReader) | 앱 경계 크로싱에만 적용 |
| Command DTO | `dashboard/commands.py` (`UpsertTimeBlocksCommand`, `DeleteTimeBlocksCommand`) | Pydantic v2. 슬롯 범위·길이 검증 중앙화 |
| Aggregation | `stats/aggregation/{calculator, daily, weekly, monthly, analysis}.py` | `stats/logic.py`는 조립기로만 동작 |

---

## 2. 앱별 로직 플로우

### 2.1 Dashboard — 시간 기록 (144슬롯)

**HTML 렌더링 뷰**

```
GET /dashboard/                        (dashboard_view)
  → safe_date_parse(date)
  → TimeBlockRepository.find_by_date(user, date)    # select_related(tag)
  → TagRepository.find_accessible_ordered(user)
  → calculate_time_statistics(filled_count)
  → build_time_headers()
  → render("dashboard/index.html", {slots[144], user_tags, stats})
```

**RESTful API (Use Case 경유)**

```
POST /api/time-blocks/
  → views: UpsertTimeBlocksCommand(user_id, target_date, slot_indexes, tag_id, memo)
       ├─ Pydantic 검증: slot_indexes 1개 이상, 0~143 범위, memo ≤ 500자
  → UpsertTimeBlocksUseCase.execute(cmd, user)      # @transaction.atomic
       ├─ TagReader.find_by_id_accessible(tag_id, user)   # PermissionError on miss
       ├─ TimeBlockWriter.find_by_slots(...)              # 기존 블록 분류
       ├─ to_create: Writer.build + bulk_create
       ├─ to_update: bulk_update(["tag", "memo"])
       └─ invalidate_stats_cache(user_id, target_date)    # 캐시 무효화
  → success_response(UpsertResult.created/updated/tag_{id,name,color})

DELETE /api/time-blocks/
  → DeleteTimeBlocksCommand 검증
  → DeleteTimeBlocksUseCase.execute(cmd, user)      # @transaction.atomic
       └─ Writer.delete_by_slots
  → success_response(deleted, requested)
```

**특징**
- 뷰는 "입력 파싱 + Command 생성 + Use Case 호출 + 응답 조립" 4단계로 한정
- 태그 권한은 Use Case가 `TagReader` Port로 검증 (구현은 `TagRepository`)
- 통계 캐시 무효화가 쓰기 성공 시 단일 지점(Use Case 내부)에서 일어남

### 2.2 Tags — 태그 & 카테고리 (Use Case 4종)

```
GET  /api/tags/                         ListTagsUseCase
  → TagRepository.find_accessible(user).order_by("is_default", "name")
  → 각 태그에 can_edit/can_delete 주입 (TagPolicyService)

POST /api/tags/                         CreateTagUseCase
  → TagPolicyService.validate_create_default(user, is_default)
  → 필수값 검증(name, color), 카테고리 조회, 중복 체크
  → TagRepository.create(...)

PUT  /api/tags/<id>/                    UpdateTagUseCase
  → TagRepository.get_for_owner_or_404(...)
  → TagPolicyService.validate_default_flip(...)
  → 중복 체크, 카테고리 교체(선택)
  → tag.user = None if is_default else user        # 도메인 규칙
  → TagRepository.save(tag)

DELETE /api/tags/<id>/                  DeleteTagUseCase
  → TagRepository.get_for_owner_or_404(...)
  → TimeBlockRepository.is_tag_in_use(tag)         # 사용 중 기본 태그 보호
  → TagRepository.delete(tag)
```

**특징**
- API 응답은 `apps/core/utils.py`의 `success_response/error_response`로 통일 (플랫 구조, `data` 래핑 없음)
- 태그 정책은 `TagPolicyService`에 집중, 입력 검증·중복 체크는 Use Case 내부로 이동 (뷰 검증 잔재 제거)

### 2.3 Users — 인증 · 목표 · 노트 · 마이페이지

```
POST /users/signup/  (signup_view)
  → UserCreationForm.save() → login(user, backend="axes.backends.AxesStandaloneBackend")
  → redirect("home")

POST /users/login/   (login_view)
  → AuthenticationForm → login(request, form.get_user(), backend=...)
  → django-axes가 실패 횟수 추적 (AXES_FAILURE_LIMIT=5, AXES_COOLOFF_TIME=1h)

GET /users/mypage/   (mypage)
  → GetMyPageUseCase.execute(user)
       ├─ GoalRepository.find_by_user(user)
       ├─ needed_periods = {g.period for g in goals}            # 선택적 계산
       ├─ get_daily/weekly/monthly_stats_data(...) only if needed
       ├─ GoalProgressService.attach_progress(goals, ...stats)
       └─ NoteRepository.find_latest(user)
  → render("users/mypage.html")

POST /users/mypage/  (mypage, 일반 요청)
  → SaveGoalUseCase.execute(GoalData, user)        # full_clean + save
  → redirect(f"{reverse('users:mypage')}?saved=1")

POST /users/mypage/  (AJAX, X-Requested-With=XMLHttpRequest)
  → 성공: 204 No Content
  → 검증 실패: JSON({"errors": {...}}, 400)
  → 클라이언트는 /users/mypage/goals-partial/ GET으로 목록만 재로드

GET /users/mypage/goals-partial/  (mypage_goals_partial)
  → GetMyPageUseCase.execute(user)
  → render("users/usergoal_list.html", {"goals": goals})        # partial

목표/노트 CRUD: 각각 Save*/Delete* Use Case (DTO 기반)
```

**특징**
- `users → stats` 역방향 의존 제거됨 — mypage가 stats/logic을 직접 import하지 않고 Use Case 내부에서 필요한 함수만 호출
- 목표 추가는 AJAX 기본, 비-AJAX fallback은 리다이렉트 유지
- `_goal_progress_service`는 period별 필요한 stats만 받아 계산

### 2.4 Stats — 집계 · 피드백 · 캐싱

```
GET /stats/?date=YYYY-MM-DD
  → GetStatsContextUseCase.execute(user, target_date)
       ├─ cache.get("stats:{uid}:{date}")                        # 캐시 우선
       │    ├─ hit  → 반환
       │    └─ miss → get_stats_context() 실행 후 cache.set(ttl)
  → TTL: 과거 날짜 24h / 오늘 5min
  → render("stats/index.html", context)
  → 템플릿에서 json_script 필터로 4개 데이터 블록 직렬화 (XSS 방어)
     (logic.py는 dict를 그대로 전달, serialize_for_js 래핑 없음)

get_stats_context 내부
  → StatsCalculator(user, target_date)                           # 공통 헬퍼
  → aggregation.daily      → get_daily_stats_data
  → aggregation.weekly     → get_weekly_stats_data
  → aggregation.monthly    → get_monthly_stats_data
  → aggregation.analysis   → get_tag_analysis_data
  → GoalRepository.find_by_period × 3 → attach_progress
  → NoteRepository.find_latest
```

**피드백** (`stats/life_feedback.py`)
- `generate_feedback(context)`가 규칙 기반 피드백 생성
- 이전에 있던 `prev_weekly_stats` 비교 dead path는 제거됨 (2026-04-20 Phase 4)

---

## 3. 의존성 맵

```
views.py (각 앱)
   │
   ├──► 같은 앱 use_cases.py
   │       ├──► domain_services.py
   │       ├──► repositories.py
   │       └──► ports.py (TimeBlockReader/Writer, TagReader)
   │
   ├──► 다른 앱 Port 경유
   │       - dashboard.use_cases  → apps.tags.ports.TagReader
   │       - dashboard.use_cases  → apps.stats.use_cases.invalidate_stats_cache
   │       - stats.logic          → apps.dashboard.repositories (via Reader)
   │       - stats.logic          → apps.users.repositories (Goal/Note)
   │       - tags.use_cases       → apps.dashboard.repositories (is_tag_in_use)
   │
   └──► apps/core/utils  (상수, 날짜 파싱, JSON 응답 헬퍼, serialize_for_js)
```

`users → stats.logic`의 역방향 호출은 제거됐다. `stats → users.repositories`는 read-only이며 Use Case가 아닌 조립 함수만 사용한다.

---

## 4. 잔여 개선점

선행 문서(2026-04-20)의 17개 항목 중 미해결 + 새로 발견된 것.

### P1 — 운영 위험

| # | 항목 | 현상 | 제안 |
|---|------|------|------|
| 1 | `settings/prod.py`의 `DEBUG = True` | `3c19106 production debug` 커밋 이후 유지 | 디버깅 종료 후 `False` 복구, 복구 확인용 체크리스트 추가 |
| 2 | `bulk_create`가 `full_clean` 우회 | 뷰·유스케이스 검증이 막고 있음. 모델 주석 누락 | `TimeBlock.clean()`에 "bulk_create 경로에서는 호출되지 않음" 주석 추가 |

### P2 — 관측성

| # | 항목 | 현상 | 제안 |
|---|------|------|------|
| 3 | `MetricsMiddleware` 미구현 | Phase 3-A~4 효과 측정 불가 | `apps/core/middleware.py` 신설, duration_ms/path/user_id 구조화 로그 |
| 4 | 로깅 메시지 표준화 | `logging.getLogger(__name__).exception("...")` 맥락 부족 | user_id, 요청 경로, 요청 바디 요약을 `extra`에 구조화 |
| 5 | axes 이벤트 알림 없음 | 로그인 잠금 시 알림/로그 통합 없음 | `AXES_LOCKOUT_CALLABLE` 연결 검토 |

### P3 — 일관성·정리

| # | 항목 | 현상 | 제안 |
|---|------|------|------|
| 6 | `TagPolicyService.can_edit/can_delete` 외형 중복 | 내부는 `can_manage` 하나로 통합되어 있으나 외부 퍼사드 2종 유지 | 외부 호출부를 `can_manage` 직접 사용으로 정리 (선택) |
| 7 | `_get_user_tag_queryset` 얕은 래퍼 | `users/views.py`에서 `TagRepository.find_accessible`만 감쌈 | 래퍼 제거 후 레포지토리 직접 호출 |
| 8 | `NoteRepository` 정렬 중복 | `find_by_user`, `find_latest`가 동일 `order_by("-created_at")` | 공통 기본 쿼리셋 헬퍼로 통합 |
| 9 | `TimeBlock` 시간 상수 하드코딩 | `time_to_slot_index`, `slot_index_to_time`이 `6`, `10`을 그대로 씀 | `core.utils`의 `MINUTES_PER_SLOT`, `SLOTS_PER_HOUR` 활용 |
| 10 | `stats/services.py` 책임 얕음 | 이름에 비해 미분류 데이터 셰이프 빌더 수준 | 용도 재검토 후 `stats/builders.py`로 개명 또는 내용 확장 |
| 11 | 카테고리 변경 권한 검증 | `UpdateTagUseCase`가 `category_id` 전달 시 그대로 교체 | `TagPolicyService.validate_category_change` 도입 검토 |

### P4 — 테스트 확대

| # | 항목 | 제안 |
|---|------|------|
| 12 | 마이페이지 AJAX 경로 회귀 테스트 | `mypage` POST(AJAX) 204 응답, `mypage_goals_partial` 렌더 테스트 추가 |
| 13 | 통계 캐시 TTL 분기 | 과거/오늘 TTL 분기 단위 테스트 (`freezegun` 또는 `mock.patch("date.today")`) |
| 14 | axes 잠금 시나리오 | 5회 실패 → 6회 시도 시 잠금 확인 (테스트 환경에서 `AXES_ENABLED=True`로 임시 전환) |

---

## 5. 권장 다음 단계

우선순위 순.

1. **P1-#1** — `prod.py` `DEBUG=False` 복구. PR 전 필수.
2. **P1-#2** — 모델 주석 보강 (5분).
3. **P2-#3** — `MetricsMiddleware` 도입. 이후 Phase 3-A~4 개선 효과를 `duration_ms`로 측정.
4. **P2-#4** — 주요 에러 로깅에 user_id·경로 구조화 필드 추가.
5. **P4-#12~14** — 최근 추가/변경 경로 회귀 테스트 보강.
6. **P3 번들** — #6~#11을 하나의 정리 커밋으로 묶어 마감.

각 단계는 모델/URL/템플릿 변경을 최소화하고 `apps/*/tests.py`와 `test_use_cases.py`를 기반으로 테스트를 추가한다.

---

## 6. 검증 체크리스트

리팩터링 중 수시로 확인.

```bash
# 뷰가 models를 직접 import하지 않는지 (0이 목표)
grep -rn "from .models import\|from apps\..*models import" \
  apps/*/views.py apps/stats/logic.py

# 뷰가 다른 앱의 logic/views를 import하지 않는지 (0 유지)
grep -rn "from apps\.stats\.logic\|from apps\.\(stats\|dashboard\|tags\|users\)\.views" apps/*/views.py

# Django 체크 & 전체 테스트
DJANGO_SECRET_KEY=test python manage.py check
pytest
```

배포 직전:
```bash
DJANGO_SETTINGS_MODULE=lifeDiary.settings.prod DJANGO_SECRET_KEY=test python manage.py check --deploy
```
