# 2026-04-09 Light DDD 아키텍처 전환 실행 계획

> 작성일시: 2026-04-09 22:55  
> 채택 전략: **레이어 구조 차용 (Light DDD)**  
> Django 앱 구조는 현재대로 유지. 각 앱 내부에 `repositories.py` + `use_cases.py` 추가.  
> 목표: 결합도 낮추기, 응집도 높이기

---

## 채택 근거

| 검토 항목 | Full DDD | Light DDD (채택) |
|-----------|----------|-----------------|
| 앱 디렉터리 구조 변경 | 전면 재편 | 현상 유지 |
| ORM 모델 이중화 | 필요 (Domain Entity 별도) | 불필요 |
| Django 마이그레이션 영향 | 큼 | 없음 |
| 적용 패턴 | Entity, VO, Aggregate, Event 등 전부 | Repository + Use Case + Domain Service 3가지 |
| 현 코드 규모 대비 복잡도 | 오버엔지니어링 | 적절 |

---

## 적용 3원칙

```
1. Repository   — ORM 쿼리를 한 곳에 집중. 다른 레이어는 DB를 직접 보지 않는다.
2. Use Case     — 뷰에서 비즈니스 로직을 분리. 뷰는 파싱 + 응답만 한다.
3. Domain Service — 도메인 계산을 도메인 안에 위치시킨다. core/utils에 흩어지지 않는다.
```

---

## 현재 의존성 문제 (Before)

```
stats/logic.py
  ├── dashboard/models.py (TimeBlock 직접 쿼리)   ← 도메인 경계 침범
  ├── users/models.py (UserGoal 직접 임포트)      ← 도메인 경계 침범
  └── core/utils.py (calculate_goal_percent)      ← 도메인 계산이 유틸에 혼재

users/views.py
  ├── stats/logic.py (get_stats_context)           ← 역방향 의존
  └── tags/models.py (Tag 직접 쿼리)

dashboard/views.py
  └── 슬롯 저장 로직, 태그 권한 검증 모두 뷰에 존재  ← 비즈니스 로직 뷰 혼재
```

---

## 목표 의존성 구조 (After)

```
[Interface Layer]  views.py
        ↓ 호출
[Application Layer]  use_cases.py
        ↓ 호출
[Domain Layer]  domain_services.py (+ 기존 models.py)
        ↓ 호출
[Infrastructure Layer]  repositories.py (ORM 쿼리 전담)
```

각 레이어는 아래 방향만 의존. 위 방향 의존 금지.

---

## Phase별 실행 계획

### Phase 0 — 코드 리뷰 잔여 이슈 7개 (선행 작업)

> docs/refactoring/2026-04-08_code-review.md 참조  
> Light DDD 작업 전에 완료. 기반을 깔끔히 정리한다.

| 순서 | # | 파일 | 내용 |
|------|---|------|------|
| 1 | #16 | `dashboard/views.py:63` | time_headers 공식 → `SLOT_END_MINUTES` 상수 명시화 |
| 1 | #18 | `core/static/core/js/utils.js:114` | `console.error` 제거 |
| 1 | #22 | `settings/dev.py:68` | `[BASE_DIR, "templates"]` → `[BASE_DIR / "templates"]` |
| 2 | #23 | `users/views.py:37` | 회원가입 후 자동 로그인 (`login(..., backend=...)`) |
| 2 | #17 | `users/views.py:82-95` | `\|` queryset union → `Q()` + `_get_user_tag_queryset()` 헬퍼 |
| 3 | #15 | `tags/views.py:157` | is_default 변경 감지 → superuser 전용 검사 명시화 |
| 4 | #21 | `dashboard/models.py:28` | `TextField` → `CharField(max_length=500)` + 마이그레이션 |

> ⚠️ #21 선행 확인: `TimeBlock.objects.filter(memo__regex=r'.{501}').count()` → 0 확인 후 진행

---

### Phase 1 — Repository 도입

**목표**: ORM 쿼리를 각 앱의 `repositories.py`로 이동. `stats/logic.py`가 `TimeBlock`을 직접 임포트하는 구조 제거.

#### 1-A. `dashboard/repositories.py` 신규 생성

```python
# apps/dashboard/repositories.py
class TimeBlockRepository:
    def find_by_date(self, user_id, date) -> QuerySet: ...
    def find_by_slots(self, user_id, date, slot_indexes) -> QuerySet: ...
    def find_daily_counts(self, user_id, start, end) -> dict[date, int]: ...
    def bulk_create(self, blocks: list) -> None: ...
    def bulk_update(self, blocks: list, fields: list) -> None: ...
    def delete_by_slots(self, user_id, date, slot_indexes) -> int: ...
```

현재 `stats/logic.py`의 `TimeBlock.objects.filter(...)` 직접 쿼리 → `TimeBlockRepository` 호출로 교체.

#### 1-B. `tags/repositories.py` 신규 생성

```python
# apps/tags/repositories.py
class TagRepository:
    def find_accessible(self, user_id) -> QuerySet: ...
    def find_by_id(self, tag_id) -> Tag | None: ...
    def create(self, user, name, color, is_default) -> Tag: ...
    def update(self, tag, **fields) -> Tag: ...
    def delete(self, tag) -> None: ...
    def is_in_use(self, tag) -> bool: ...
```

현재 `tags/views.py`의 `Tag.objects.*` 직접 쿼리 → `TagRepository` 호출로 교체.  
현재 `users/views.py`의 `Tag.objects.filter(Q(...) | Q(...))` → `TagRepository.find_accessible()` 호출.

#### 1-C. `users/repositories.py` 신규 생성

```python
# apps/users/repositories.py
class GoalRepository:
    def find_by_user(self, user_id, period=None) -> QuerySet: ...
    def find_by_id(self, goal_id, user_id) -> UserGoal: ...
    def create(self, user, tag, period, target_hours) -> UserGoal: ...
    def update(self, goal, **fields) -> UserGoal: ...
    def delete(self, goal) -> None: ...

class NoteRepository:
    def find_by_user(self, user_id) -> QuerySet: ...
    def find_by_id(self, note_id, user_id) -> UserNote: ...
    def create(self, user, note) -> UserNote: ...
    def update(self, note, **fields) -> UserNote: ...
    def delete(self, note) -> None: ...
```

**변경되는 파일**:
- `apps/dashboard/repositories.py` (신규)
- `apps/tags/repositories.py` (신규)
- `apps/users/repositories.py` (신규)
- `apps/stats/logic.py` (임포트 교체: `TimeBlock.objects.*` → `TimeBlockRepository`)
- `apps/tags/views.py` (임포트 교체)
- `apps/users/views.py` (임포트 교체)

---

### Phase 2 — Domain Service 도입

**목표**: 도메인 계산 로직을 `core/utils.py`에서 해당 도메인으로 이동.

#### 2-A. `users/domain_services.py` 신규 생성

```python
# apps/users/domain_services.py
class GoalProgressService:
    """
    Goal 도메인의 달성률 계산. ORM 없음, request 없음.
    현재 core/utils.py의 calculate_goal_percent() 이전.
    """
    def calculate(self, goal: UserGoal, tag_hours: dict[str, float]) -> tuple[float, int | None]:
        actual = tag_hours.get(goal.tag.name, 0)
        percent = int(actual / goal.target_hours * 100) if goal.target_hours > 0 else None
        return actual, percent

    def attach_progress(self, goals, tag_hours: dict[str, float]) -> list:
        """목표 리스트에 actual, percent 주입 후 반환"""
        for goal in goals:
            goal.actual, goal.percent = self.calculate(goal, tag_hours)
        return goals
```

`core/utils.py`의 `calculate_goal_percent()` 제거 또는 `GoalProgressService`로 위임하는 thin wrapper 유지.

#### 2-B. `tags/domain_services.py` 신규 생성

```python
# apps/tags/domain_services.py
class TagPolicyService:
    """
    태그 정책 검증. 현재 tags/views.py에 분산된 권한 규칙 집중.
    is_default flip 권한(#15), 소유권, 삭제 가능 여부 포함.
    """
    def can_create_default(self, user) -> bool: ...
    def can_modify(self, user, tag) -> bool: ...
    def can_delete(self, user, tag) -> bool: ...
    def validate_default_flip(self, user, tag, requested_is_default) -> None:
        """is_default 변경 시 superuser 여부 검증. 위반 시 PermissionError."""
```

**변경되는 파일**:
- `apps/users/domain_services.py` (신규)
- `apps/tags/domain_services.py` (신규)
- `apps/core/utils.py` (`calculate_goal_percent` 제거, Domain Service로 이전)
- `apps/stats/logic.py` (`GoalProgressService` 사용으로 교체)
- `apps/tags/views.py` (`TagPolicyService` 사용으로 교체)

---

### Phase 3 — Use Case 도입

**목표**: 뷰에서 비즈니스 로직 제거. 뷰는 파싱 + Use Case 호출 + 응답 반환만 담당.

#### 3-A. `dashboard/use_cases.py` 신규 생성

```python
# apps/dashboard/use_cases.py
class GetDailySlotsUseCase:
    """대시보드 뷰용 144슬롯 데이터 조회"""
    def __init__(self, time_block_repo: TimeBlockRepository): ...
    def execute(self, user_id, date) -> dict: ...

class UpsertTimeBlocksUseCase:
    """슬롯 배열 저장 (create + update)"""
    def __init__(self, time_block_repo, tag_repo): ...
    def execute(self, user_id, date, slot_indexes, tag_id, memo) -> dict: ...
    # 태그 접근 권한 검증, 슬롯 범위 검증, bulk upsert 포함

class DeleteTimeBlocksUseCase:
    def __init__(self, time_block_repo): ...
    def execute(self, user_id, date, slot_indexes) -> int: ...
```

#### 3-B. `tags/use_cases.py` 신규 생성

```python
# apps/tags/use_cases.py
class ListTagsUseCase:
    def execute(self, user_id) -> list: ...

class CreateTagUseCase:
    def __init__(self, tag_repo, policy_service): ...
    def execute(self, user, name, color, is_default) -> Tag: ...

class UpdateTagUseCase:
    def __init__(self, tag_repo, policy_service): ...
    def execute(self, user, tag_id, name, color, is_default) -> Tag: ...

class DeleteTagUseCase:
    def __init__(self, tag_repo, policy_service): ...
    def execute(self, user, tag_id) -> None: ...
```

#### 3-C. `stats/use_cases.py` 신규 생성

```python
# apps/stats/use_cases.py
class GetStatsContextUseCase:
    """
    현재 get_stats_context() 함수 이관.
    stats/logic.py의 StatsCalculator 분해 결과를 조합.
    """
    def __init__(self, time_block_repo, goal_repo, goal_progress_service): ...
    def execute(self, user_id, date) -> dict: ...
```

#### 뷰 변환 예시

```python
# dashboard/views.py (After)
def time_block_api(request):
    data = json.loads(request.body)
    slot_indexes = data.get("slot_indexes", [])
    tag_id = data.get("tag_id")
    memo = data.get("memo", "")
    selected_date = safe_date_parse(data.get("date"))

    use_case = UpsertTimeBlocksUseCase(TimeBlockRepository(), TagRepository())
    try:
        result = use_case.execute(request.user.id, selected_date, slot_indexes, tag_id, memo)
        return success_response("저장 완료", result)
    except PermissionError as e:
        return error_response(str(e), "PERMISSION_DENIED", 403)
    except ValueError as e:
        return error_response(str(e), "VALIDATION_ERROR", 400)
```

**변경되는 파일**:
- `apps/dashboard/use_cases.py` (신규)
- `apps/tags/use_cases.py` (신규)
- `apps/stats/use_cases.py` (신규)
- `apps/users/use_cases.py` (신규, 목표/노트 CRUD)
- `apps/dashboard/views.py` (로직 → Use Case 호출로 교체, 대폭 축소)
- `apps/tags/views.py` (대폭 축소)
- `apps/users/views.py` (대폭 축소)
- `apps/stats/views.py` (소폭 수정)
- `apps/stats/logic.py` (StatsCalculator 역할 분산 후 슬림화)

---

### Phase 4 — stats/logic.py 분해 (별도 추적)

현재 452줄의 `stats/logic.py`는 Phase 1~3 완료 후 자연스럽게 축소됨.  
남은 집계 로직은 `stats/aggregation.py`로 이름 변경 및 정리.

```
stats/logic.py (452줄) → stats/aggregation.py (~200줄)
                          stats/use_cases.py (신규)
                          (ORM 쿼리 → TimeBlockRepository)
                          (Goal 계산 → GoalProgressService)
```

---

## 최종 파일 구조 (After)

```
apps/
├── dashboard/
│   ├── models.py          (변경 없음)
│   ├── repositories.py    ★ 신규
│   ├── use_cases.py       ★ 신규
│   └── views.py           ↓ 대폭 축소
│
├── tags/
│   ├── models.py          (변경 없음)
│   ├── repositories.py    ★ 신규
│   ├── domain_services.py ★ 신규
│   ├── use_cases.py       ★ 신규
│   └── views.py           ↓ 대폭 축소
│
├── users/
│   ├── models.py          (변경 없음)
│   ├── repositories.py    ★ 신규
│   ├── domain_services.py ★ 신규
│   ├── use_cases.py       ★ 신규
│   └── views.py           ↓ 대폭 축소
│
├── stats/
│   ├── aggregation.py     ★ logic.py 슬림화/개명
│   ├── use_cases.py       ★ 신규
│   ├── feedback.py        (변경 없음)
│   └── views.py           ↓ 소폭 수정
│
└── core/
    └── utils.py           ↓ calculate_goal_percent 제거 후 슬림화
```

신규 파일 9개, 수정 파일 8개. 기존 구조(마이그레이션, URL, 템플릿) 변경 없음.

---

## 진행 순서 요약

```
Phase 0  코드 리뷰 잔여 7개 정리
   ↓
Phase 1  Repository 도입 (ORM 격리)
   ↓
Phase 2  Domain Service 도입 (도메인 계산 집중)
   ↓
Phase 3  Use Case 도입 (뷰 슬림화)
   ↓
Phase 4  stats/logic.py 분해 정리
```

각 Phase는 독립적으로 커밋 가능. Phase 1만 해도 stats → dashboard 도메인 경계 침범이 해소됨.

---

## 검증 기준

각 Phase 완료 후:
- `python manage.py check` → 0 errors
- 기존 뷰 URL이 동일하게 응답하는지 수동 확인
- Phase 3 이후: `views.py`가 `models.py`를 직접 임포트하지 않는지 grep 확인

```bash
# 뷰가 모델을 직접 참조하는지 확인 (0이 목표)
grep -rn "from apps.*models import" apps/*/views.py
```
