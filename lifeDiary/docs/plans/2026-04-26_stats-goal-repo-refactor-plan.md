# 통계 컨텍스트의 UserGoal 쿼리 통합 (A1)

- 작성일: 2026-04-26
- 대상: `apps/stats/logic.py`, `apps/users/repositories.py`
- 상태: 사용자 확인됨 — TDD로 진행

## 배경

`get_stats_context`가 `UserGoal`을 period별로 3회 fetch하고 있다.

```python
# apps/stats/logic.py:63-65
user_goals_daily   = _goal_repo.find_by_period(user, "daily")
user_goals_weekly  = _goal_repo.find_by_period(user, "weekly")
user_goals_monthly = _goal_repo.find_by_period(user, "monthly")
```

같은 테이블·같은 사용자에 `WHERE period = ?`만 다른 쿼리 3회. 1회로 통합 가능.

## 목표

- 통계 페이지 쿼리 수: **8 → 6**
- `GoalRepository`에 `find_grouped_by_period(user)` 추가
- `find_by_period`는 다른 호출자가 있을 수 있으니 **유지** (deprecate 안 함)
- 결과 구조와 출력은 변경 없음

## TDD 사이클

### Step 1 — RED
1. `apps/users/test_goal_repository.py` (또는 기존 tests에 추가) — `find_grouped_by_period(user)`가 dict 형태로 모든 period 데이터를 1쿼리로 반환하는 테스트
2. `apps/stats/test_stats_perf.py` — `TARGET_MAX_QUERIES`를 8 → 6으로 강화
3. 두 테스트 모두 실패 확인

### Step 2 — GREEN
1. `GoalRepository.find_grouped_by_period(user)` 구현
   - 단일 쿼리로 fetch 후 Python에서 period별 분리
   - 반환: `{"daily": [...], "weekly": [...], "monthly": [...]}` (없는 period도 빈 리스트 보장)
2. `logic.py`가 새 메서드 사용
3. 모든 테스트 통과 확인

### Step 3 — 회귀 검증
- 전체 테스트 통과 (70+)
- `monthly_and_analysis_results_unchanged_under_caching` 같은 회귀 테스트가 출력 동일성 보장

## 리스크

| 등급 | 항목 | 완화 |
|------|------|------|
| LOW | 다른 호출자가 `find_by_period` 의존 | 기존 메서드 유지, 새 메서드만 추가 |
| LOW | period 누락 (예: monthly만 등록한 사용자) | 빈 리스트 기본값 보장하는 테스트 작성 |

## 복잡도: **LOW** (30–60분)

## 범위 제외
- `find_by_period` 제거 — 별도 분석 후 결정
- 다른 안티패턴 (B 그룹) — 이번 범위 아님
