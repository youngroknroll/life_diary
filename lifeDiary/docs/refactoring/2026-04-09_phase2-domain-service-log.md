# 2026-04-09 Phase 2 — Domain Service 도입 로그

> 작업일시: 2026-04-09 23:37  
> 목표: 도메인 계산/정책 규칙을 Domain Service로 집중. core/utils 슬림화.

---

## 신규 파일 2개

| 파일 | 역할 |
|------|------|
| `apps/users/domain_services.py` | `GoalProgressService` — 목표 달성률 계산 |
| `apps/tags/domain_services.py` | `TagPolicyService` — 태그 접근 정책 판단 |

---

## GoalProgressService

```python
class GoalProgressService:
    def calculate(goal, daily_stats, weekly_stats, monthly_stats) -> (actual, percent)
    def attach_progress(goals, daily_stats, weekly_stats, monthly_stats) -> goals
```

**이전**: `core/utils.py`의 `calculate_goal_percent()` 자유 함수  
**이후**: `users` 도메인 안에서 책임 명확화. ORM/request 없음.

사용처:
- `stats/logic.py` `get_stats_context()` — 3개 목표 리스트에 일괄 적용
- `users/views.py` `mypage()` — 사용자 목표 달성률 계산

---

## TagPolicyService

```python
class TagPolicyService:
    def can_edit(user, tag) -> bool
    def can_delete(user, tag) -> bool
    def validate_create_default(user, is_default) -> None  # PermissionError
    def validate_default_flip(user, tag, requested_is_default) -> None  # PermissionError
```

**이전**: `tags/views.py`에 `if is_default and not request.user.is_superuser` 분산  
**이후**: 정책 판단 한 곳 집중. 뷰는 `PermissionError`만 잡아 응답 변환.

---

## 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `apps/stats/logic.py` | `calculate_goal_percent` 임포트 제거 → `_goal_progress_service.attach_progress()` |
| `apps/users/views.py` | `calculate_goal_percent` 임포트 제거 → `_goal_progress_service.attach_progress()` |
| `apps/tags/views.py` | `is_superuser` 직접 판단 2곳 → `_tag_policy_service.validate_*()` |
| `apps/core/utils.py` | `calculate_goal_percent()` 함수 제거 (32줄 감소) |

---

## 검증

```
python -m py_compile 6개 파일 → syntax OK
python manage.py check → 0 issues

# calculate_goal_percent 잔존 확인 (주석 제외)
→ 없음

# tags/views.py is_superuser 직접 판단 잔존 확인
→ 없음
```

---

## Before / After

**Before**
```
stats/logic.py  → core/utils.calculate_goal_percent()
users/views.py  → core/utils.calculate_goal_percent()
tags/views.py   → if is_default and not request.user.is_superuser (2곳 직접 판단)
```

**After**
```
stats/logic.py  → users/domain_services.GoalProgressService
users/views.py  → users/domain_services.GoalProgressService
tags/views.py   → tags/domain_services.TagPolicyService
core/utils.py   → 목표 계산 로직 제거, 범용 유틸만 잔류
```

목표 계산은 `users` 도메인 안에, 태그 정책은 `tags` 도메인 안에 위치.
