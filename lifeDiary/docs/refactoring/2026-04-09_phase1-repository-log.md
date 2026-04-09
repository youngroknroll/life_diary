# 2026-04-09 Phase 1 — Repository 도입 로그

> 작업일시: 2026-04-09 23:32  
> 목표: ORM 쿼리를 Repository 계층으로 격리. 뷰/logic에서 models 직접 임포트 제거.

---

## 신규 파일 3개

| 파일 | 역할 |
|------|------|
| `apps/dashboard/repositories.py` | `TimeBlockRepository` — TimeBlock ORM 전담 |
| `apps/tags/repositories.py` | `TagRepository` — Tag ORM 전담 |
| `apps/users/repositories.py` | `GoalRepository`, `NoteRepository` — UserGoal/UserNote ORM 전담 |

---

## TimeBlockRepository 메서드

| 메서드 | 이전 코드 위치 |
|--------|--------------|
| `find_by_date(user, date)` | `stats/logic.py`, `dashboard/views.py` |
| `find_by_slots(user, date, slot_indexes)` | `dashboard/views.py` |
| `find_daily_counts(user, start, end)` | `stats/logic.py` (fill_empty_slots_*) |
| `find_by_month(user, start, end)` | `stats/logic.py` (monthly/analysis) |
| `build(user, date, slot_index, tag, memo)` | `dashboard/views.py` (`TimeBlock(...)` 직접 생성) |
| `bulk_create(blocks)` | `dashboard/views.py` |
| `bulk_update(blocks, fields)` | `dashboard/views.py` |
| `delete_by_slots(user, date, slot_indexes)` | `dashboard/views.py` |
| `is_tag_in_use(tag)` | `tags/views.py` |

## TagRepository 메서드

| 메서드 | 이전 코드 위치 |
|--------|--------------|
| `find_accessible(user)` | `dashboard/views.py`, `tags/views.py`, `users/views.py` |
| `find_accessible_ordered(user)` | `dashboard/views.py`, `tags/views.py` |
| `find_by_id_accessible(tag_id, user)` | `dashboard/views.py` |
| `get_for_owner_or_404(tag_id, user)` | `tags/views.py` (superuser 분기 포함) |
| `exists_duplicate(user, name, exclude_id)` | `tags/views.py` (생성/수정 중복 확인) |
| `create(user, name, color, is_default)` | `tags/views.py` |
| `save(tag)` | `tags/views.py` |
| `delete(tag)` | `tags/views.py` |

## GoalRepository / NoteRepository 메서드

| 메서드 | 이전 코드 위치 |
|--------|--------------|
| `GoalRepository.find_by_user(user)` | `users/views.py` |
| `GoalRepository.find_by_period(user, period)` | `stats/logic.py` |
| `GoalRepository.get_or_404(pk, user)` | `users/views.py` |
| `NoteRepository.find_by_user(user)` | `users/views.py` |
| `NoteRepository.find_latest(user)` | `stats/logic.py` |
| `NoteRepository.get_or_404(pk, user)` | `users/views.py` |

---

## 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `apps/stats/logic.py` | `TimeBlock`, `UserGoal`, `UserNote` 직접 임포트 → Repository 호출. `Count` 임포트 제거 |
| `apps/dashboard/views.py` | `TimeBlock`, `Tag` 직접 임포트 → Repository 호출. `Q` 임포트 제거 |
| `apps/tags/views.py` | `Tag`, `TimeBlock` 직접 임포트 → Repository 호출. `Q`, `models`, `get_object_or_404` 임포트 제거 |
| `apps/users/views.py` | `UserGoal`, `UserNote`, `Tag` 직접 임포트 → Repository 호출. `Q`, `get_object_or_404` 임포트 제거 |

---

## 검증

```
python -m py_compile 7개 파일 → syntax OK
python manage.py check → 0 issues

# 뷰/logic models 직접 임포트 확인
grep -rn "from apps.*models import|from .models import" \
  apps/dashboard/views.py apps/tags/views.py apps/users/views.py apps/stats/logic.py
→ 없음
```

---

## Before / After 의존성 비교

**Before**
```
stats/logic.py → dashboard/models.py (TimeBlock 직접)
stats/logic.py → users/models.py (UserGoal, UserNote 직접)
tags/views.py  → dashboard/models.py (TimeBlock 직접)
users/views.py → tags/models.py (Tag 직접)
```

**After**
```
stats/logic.py → dashboard/repositories.py (TimeBlockRepository)
stats/logic.py → users/repositories.py (GoalRepository, NoteRepository)
tags/views.py  → dashboard/repositories.py (TimeBlockRepository)
users/views.py → tags/repositories.py (TagRepository)
```

도메인 경계 침범 해소. stats가 dashboard 모델을 직접 보지 않는다.
