# 2026-04-20 Backend Flow & Improvements

> 작성일: 2026-04-20
> 범위: `dashboard`, `tags`, `users`, `stats`, `core` 앱의 현재 백엔드 로직 플로우 정리 및 잔여 개선점 진단
> 선행 문서: `docs/refactoring/2026-04-09_business-logic-analysis.md`, `docs/plans/2026-04-09_light-ddd-plan.md`, Phase 0~2 수행 로그

---

## 1. 현재 레이어 구조

Phase 1~2까지 반영된 상태 기준.

```
[Interface Layer]      views.py                         ← HTTP 파싱/응답
       │
       ├── (일부 직접 호출)
       ▼
[Domain Services]      domain_services.py               ← 정책/계산 (부분 도입)
[Repositories]         repositories.py                  ← ORM 쿼리 전담
       │
       ▼
[Models]               models.py                        ← 제약/유효성
```

| 계층 | 도입 상태 | 남은 과제 |
|------|----------|-----------|
| Repository | `dashboard`, `tags`, `users` 3개 도입 완료 | `stats` 전용 Repository 없음. 다른 앱 Repository를 직접 호출 |
| Domain Service | `GoalProgressService`, `TagPolicyService` 2개 | Category, TimeBlock 도메인 서비스 없음 |
| Use Case | **미도입** (Phase 3 예정) | 뷰에 여전히 검증/분기/응답 조립이 혼재 |
| Aggregation Service | **미도입** (Phase 4 예정) | `stats/logic.py`가 계산+조립을 모두 담당 |

`stats/services.py`는 이름과 달리 "미분류 데이터 셰이프 빌더" 수준이며, 실제 집계/프레젠테이션 분리를 수행하지 않는다.

---

## 2. 앱별 로직 플로우

### 2.1 Dashboard — 시간 기록 (144슬롯)

**엔트리 2개**: HTML 렌더링 뷰 + RESTful API.

```
GET /dashboard/                        (dashboard_view)
  → safe_date_parse(date)
  → TimeBlockRepository.find_by_date(user, date)          # select_related(tag)
  → TagRepository.find_accessible_ordered(user)
  → calculate_time_statistics(filled_count)
  → build_time_headers()                                  # dashboard/services.py
  → render("dashboard/index.html", {slots[144], user_tags, stats})

POST /api/time-blocks/                 (time_block_api → _handle_create_update)
  → JSON 파싱 → slot_indexes / date / tag_id / memo
  → validate_slot_indexes()                               # 0 ≤ idx < 144
  → 길이 검증: memo ≤ 500
  → TagRepository.find_by_id_accessible(tag_id, user)     # 권한 포함 조회
  → TimeBlockRepository.find_by_slots(...)                # 기존 블록 분류
  → 새 블록: build() + bulk_create()
  → 기존 블록: bulk_update(["tag", "memo"])
  → success_response(created/updated count)

DELETE /api/time-blocks/               (time_block_api → _handle_delete)
  → TimeBlockRepository.delete_by_slots(...)
  → success_response(deleted_count)
```

**특징**
- 뷰가 직접 Repository 2개를 조율 (Use Case 역할 수행 중)
- 태그 권한 검증은 `find_by_id_accessible` 레포지토리 쿼리가 담당 (도메인 서비스 아님)
- `bulk_create`는 모델 `clean()`을 건너뛰므로, 슬롯 범위 검증은 뷰 레벨만 유효

### 2.2 Tags — 태그 & 카테고리

```
GET  /tags/                             (index) → 빈 셸 템플릿, JS가 API로 데이터 로드
GET  /api/categories/                   (category_list)
  → CategoryRepository.find_all()

GET  /api/tags/                         (tag_list_create, GET)
  → TagRepository.find_accessible(user).order_by("is_default", "name")
  → 각 태그에 can_edit / can_delete 주입 (TagPolicyService)

POST /api/tags/                         (tag_list_create, POST)
  → TagPolicyService.validate_create_default(user, is_default)   # 403
  → CategoryRepository.find_by_id(category_id)                   # 400 if none
  → TagRepository.exists_duplicate(user, name)                    # 400 if exists
  → TagRepository.create(...)

PUT    /api/tags/<id>/                  (tag_detail_update_delete, PUT)
  → TagRepository.get_for_owner_or_404(tag_id, user)              # 404/403 통합
  → TagPolicyService.validate_default_flip(...)                   # 403
  → TagRepository.exists_duplicate(exclude_id=tag.id)             # 400
  → 카테고리 교체 선택
  → TagRepository.save(tag)

DELETE /api/tags/<id>/                  (tag_detail_update_delete, DELETE)
  → tag.is_default && TimeBlockRepository.is_tag_in_use(tag) → 400
  → TagRepository.delete(tag)
```

**특징**
- 정책은 `TagPolicyService`에 잘 모였으나, 입력 검증(name/color 필수, 중복 체크)은 여전히 뷰에 산재
- `tag.user = None if is_default else user` 같은 **도메인 규칙이 뷰에 그대로** 존재 (PUT 핸들러 내부)
- 응답 포맷이 `dashboard`의 `success_response`/`error_response`와 다름 (직접 `JsonResponse` 구성)

### 2.3 Users — 인증 · 목표 · 노트 · 마이페이지

```
POST /users/signup/                     (signup_view)
  → UserCreationForm.save() → login(user, backend=...)  # 자동 로그인
  → redirect("home")

POST /users/login/                      (login_view)
  → AuthenticationForm → authenticate → login → redirect("home")

GET/POST /users/mypage/                 (mypage)
  → GoalRepository.find_by_user(user)                    # select_related("tag")
  → StatsCalculator(user, today)
  → get_daily/weekly/monthly_stats_data(...)              # 전체 집계 수행
  → GoalProgressService.attach_progress(goals, stats...)  # actual/percent 주입
  → (POST인 경우 UserGoalForm 저장)
  → render("users/mypage.html")

CRUD: usergoal_{list,create,update,delete}
       usernote_{list,create,update,delete}
  → 각각 GoalRepository / NoteRepository 의 get_or_404 + Form 저장
  → 모든 delete는 @require_http_methods(["GET","POST"])
```

**특징**
- `mypage`가 `stats/logic.py`를 호출하여 **역방향 의존** (users → stats → users.domain_services/repositories)
- 목표 폼 queryset 제한은 `_get_user_tag_queryset` 헬퍼가 TagRepository를 감싼 중복 래퍼

### 2.4 Stats — 집계 · 피드백

```
GET /stats/                             (index)
  → get_stats_context(user, selected_date)                     # stats/logic.py
       ├─ StatsCalculator(user, selected_date)
       ├─ get_daily_stats_data()        # TimeBlockRepository.find_by_date
       ├─ get_weekly_stats_data()       # find_by_date × 7
       ├─ get_monthly_stats_data()      # find_by_month + find_daily_counts
       ├─ get_tag_analysis_data()       # find_by_month + find_daily_counts
       ├─ GoalRepository.find_by_period × 3 (daily/weekly/monthly)
       ├─ GoalProgressService.attach_progress × 3
       └─ NoteRepository.find_latest
  → generate_feedback(context)                                  # stats/feedback.py
  → render("stats/index.html", context)
```

**StatsCalculator 책임 (여전히 비대)**
- 날짜 범위 계산 (`start_of_week`, `start_of_month`)
- 태그 정보 추출
- 빈 슬롯 계산 (daily/weekly/monthly/analysis 4 변종)
- 미분류 데이터 주입 (data_type별 분기 4가지)

**피드백 로직**
- `context` dict 내부 구조(`monthly_stats["tag_stats"]`, `tag_weekly_stats`...) 에 강하게 결합
- `prev_weekly_stats`는 `context`에 주입되지 않으므로 2번 비교 피드백은 **항상 dead path**

---

## 3. 의존성 맵 (정방향 기준)

```
views.py (각 앱)
   │
   ├──► 같은 앱 repositories.py / domain_services.py
   │
   ├──► 다른 앱 repositories.py / domain_services.py
   │        - dashboard.views  → tags.repositories (태그 권한)
   │        - tags.views       → dashboard.repositories (태그 사용중 체크)
   │        - users.views      → tags.repositories (queryset 제한)
   │        - users.views      → stats.logic          ← 역방향 섞임
   │        - stats.logic      → users.repositories (GoalRepository)
   │        - stats.logic      → users.domain_services (GoalProgressService)
   │        - stats.logic      → dashboard.repositories (TimeBlockRepository)
   │
   └──► apps/core/utils (상수·날짜·JSON 응답 헬퍼)
```

순환은 없으나 `users ⇄ stats` 간 양방향 호출이 존재한다. Use Case 계층이 없기 때문에 뷰가 다른 앱의 집계 로직을 직접 부르고 있다.

---

## 4. 발견된 개선점 (우선순위별)

### P1 — 동작 위험 또는 데이터 무결성

| # | 항목 | 현상 | 제안 |
|---|------|------|------|
| 1 | `_handle_time_block_create_update` 트랜잭션 누락 | `bulk_create` 후 `bulk_update` 중 하나가 실패하면 부분 반영 | `transaction.atomic()` 블록으로 감싸기 |
| 2 | 주간 비교 피드백 dead path | `generate_feedback`이 `prev_weekly_stats`를 읽지만 `get_stats_context`가 설정하지 않음 | 이전 주 집계 추가 또는 해당 분기 제거 |
| 3 | `bulk_create`가 `full_clean` 우회 | `TimeBlock.clean()`의 "타인 기본태그 방지"가 실제로 동작하지 않음 | 뷰 검증에 이미 `find_by_id_accessible` 있으므로 유지하되, 모델 `clean()` 주석으로 명시 |

### P2 — 구조적 결합 (Phase 3/4 실행 동기)

| # | 항목 | 현상 | 제안 |
|---|------|------|------|
| 4 | Use Case 계층 부재 | 뷰가 검증·권한·조회·쓰기·응답조립을 모두 담당. dashboard `_handle_*` 함수가 사실상 Use Case 역할 | `dashboard/use_cases.py`, `tags/use_cases.py` 신설하여 뷰를 "파싱 + 호출 + 응답" 3줄 수준으로 축소 |
| 5 | `StatsCalculator` 비대 | `fill_empty_slots_*` 4종, `add_unclassified_data` data_type 분기 4종이 한 클래스 안에 공존 | `stats/aggregation/` 하위에 daily/weekly/monthly 별 계산기 분리. `StatsCalculator`는 공통 헬퍼만 유지 |
| 6 | 피드백 입력 결합 | `generate_feedback(context)`가 템플릿 컨텍스트 전체에 결합 | `FeedbackInput`(dataclass 또는 TypedDict) 정의, 필요한 필드만 전달 |
| 7 | `users → stats` 역방향 의존 | `mypage`가 stats 집계를 직접 호출 | `users/use_cases/GetMyPageUseCase`가 stats의 read-only 함수를 조립하도록 이동 |
| 8 | `stats/services.py`가 데이터 셰이프 빌더 수준 | 이름에 비해 책임이 얕음 | 실제 presentation 분리 전까지 `stats/builders.py`로 개명 고려 |

### P3 — 일관성 · 품질

| # | 항목 | 현상 | 제안 |
|---|------|------|------|
| 9 | API 응답 포맷 불일치 | dashboard는 `success_response/error_response`, tags는 직접 dict | `tags/views.py`도 core 헬퍼 사용으로 통일 |
| 10 | 검증 규칙 중복 | `UserGoal.clean()`의 period별 상한(24/100/300) + Form에도 동일 규칙 위험 | 규칙을 한 곳(모델)으로 통일, Form은 Django 기본 `full_clean` 위임 |
| 11 | `TagPolicyService.can_edit/can_delete` 외형 중복 | 내부 `can_manage` 하나를 공유. 현재 코드는 정리되어 있으나 불필요한 퍼사드 3개 | 외부에서 `can_manage` 직접 사용하도록 정리 가능 (선택) |
| 12 | `_get_user_tag_queryset` 얕은 래퍼 | `users/views.py`의 한 줄 함수가 `TagRepository.find_accessible`을 감쌀 뿐 | 래퍼 제거하고 레포지토리 직접 호출 |
| 13 | `NoteRepository.find_by_user`, `find_latest` 정렬 중복 | 두 메서드 모두 `order_by("-created_at")` | 공통 기본 쿼리셋 헬퍼 |
| 14 | `TimeBlock` 시간 변환 상수 하드코딩 | `time_to_slot_index`, `slot_index_to_time`이 `6`, `10`을 그대로 사용 | `core.utils`의 `MINUTES_PER_SLOT`, `SLOTS_PER_HOUR` 활용 |

### P4 — 성능 · 관측성

| # | 항목 | 현상 | 제안 |
|---|------|------|------|
| 15 | 주간 집계 7회 쿼리 | `get_weekly_stats_data`가 `find_by_date(date)` × 7 | `find_by_date_range`로 단일 쿼리 후 그룹핑 |
| 16 | 로깅 메시지 표준화 부재 | `logging.getLogger(__name__).exception("시간 블록 저장 중 오류")` 같은 맥락 없는 문구 다수 | user_id, 요청 데이터 요약 같은 구조화 필드 추가 |
| 17 | 카테고리 변경 권한 | 뷰에서 `category_id` 수용 후 `find_by_id` 조회만 수행 → 일반 사용자가 공용 기본 태그의 카테고리도 변경할 수 있는지 재검증 필요 | `TagPolicyService.validate_category_change` 신설 고려 |

---

## 5. 권장 다음 단계 (Phase 3/4 진입 순서)

원래 Light DDD 계획서의 순서와 위 개선점을 결합하면 다음이 합리적이다.

1. **P1-#1 트랜잭션 보강** — 15분 수준의 surgical fix, 먼저 머지.
2. **P2-#4 Use Case 도입 (dashboard)** — `time_block_api`를 먼저 리팩터링하여 Use Case 패턴 검증.
3. **P2-#4 Use Case 도입 (tags)** — 검증·권한·중복 체크를 `use_cases.py`로 이관, 뷰 응답을 `core` 헬퍼로 통일(P3-#9 동시 해소).
4. **P2-#7 users `mypage` 정리** — Use Case 한 번 더 연습, 역방향 의존 제거.
5. **P2-#5 StatsCalculator 분해** — `stats/aggregation/` 패키지 도입, `daily/weekly/monthly/analysis` 분리 후 `get_stats_context`는 조립만 담당.
6. **P2-#6 피드백 입력 축소** — `FeedbackInput` 도입. 주간 비교 dead path(P1-#2) 결정 (구현 or 삭제).
7. **P3/P4 개선점 마무리** — 규칙 중복 제거, 응답 포맷 통일, 로깅 구조화.

각 단계는 독립 커밋이 가능하도록 모델/URL/템플릿 변경을 최소화하고 테스트는 기존 `apps/*/tests.py`를 기반으로 추가한다.

---

## 6. 검증 체크리스트

리팩터링 중 다음을 수시로 확인한다.

```bash
# 뷰가 models를 직접 import하지 않는지 (0이 목표)
grep -rn "from .models import\|from apps\..*models import" \
  apps/*/views.py apps/stats/logic.py

# views.py가 다른 앱의 logic/views를 import하지 않는지
grep -rn "from apps\.\(stats\|dashboard\|tags\|users\)\.views" apps/*/views.py
grep -rn "from apps\.stats\.logic" apps/*/views.py

# Django 체크 & 전체 테스트
DJANGO_SECRET_KEY=test ./.venv/bin/python manage.py check
DJANGO_SECRET_KEY=test ./.venv/bin/python manage.py test -v 2
```

각 Phase 완료 후 `python manage.py check --deploy`도 함께 수행한다.
