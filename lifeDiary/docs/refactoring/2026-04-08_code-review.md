# 2026-04-08 Code Review

> Reviewer: Claude (Senior Dev) | Scope: Full project logic code

## Findings (23)

### CRITICAL

| # | File:Line | Issue | Fix | Status |
|---|-----------|-------|-----|--------|
| 1 | users/views:100,116,144,157 | IDOR - `.get()` unhandled 404 | `get_object_or_404()` | DONE |
| 2 | dashboard/views:103 | slot_indexes no type/range validation | validate `int, 0-143` | DONE |
| 3 | dashboard/views:202 | exception msg leaks internals | generic msg + `logger.exception()` | DONE |
| 4 | tags/views:66,131,210,235 | same exception leak pattern | generic msg + logging | DONE |
| 5 | settings/prod.py | missing SSL/HSTS/cookie secure headers | add 5 security settings | DONE |

### HIGH

| # | File:Line | Issue | Fix | Status |
|---|-----------|-------|-----|--------|
| 6 | dashboard/views:135 | memo no length validation at API | validate len<=500 | DONE |
| 7 | stats/logic:114,137 | N+1 query in monthly loop (31x) | single `.values().annotate()` | DONE |
| 8 | users/views:166-233 | mypage goal-calc duplicated (3 copies) | extract shared helper | DONE |
| 9 | stats/logic:427-458 | same goal-calc duplication | merge with #8 | DONE |
| 10 | stats/feedback:13 | `target_hours * total_days` wrong calc | remove `* total_days` | DONE |
| 11 | users/views:115,157 | delete views missing `@require_http_methods` | add `["GET","POST"]` decorator | DONE |
| 12 | settings/dev:53 | WhiteNoise before SecurityMiddleware | swap order | DONE |

### MEDIUM

| # | File:Line | Issue | Status |
|---|-----------|-------|--------|
| 13 | stats/logic (all) | StatsCalculator - mixed concerns, unused `self.user` | TODO |
| 14 | stats/feedback:53 | bare `except: pass` swallows errors | DONE |
| 15 | tags/views:186-189 | is_default flip permission gap risk | TODO |
| 16 | dashboard/views:61 | obscure time header formula | TODO |
| 17 | users/views:82-95 | `|` queryset union instead of `Q()` | TODO |
| 18 | core/js/utils.js:114 | `console.error` in production | TODO |
| 19 | users/models:16 | target_hours no min=0 validator | DONE |
| 20 | stats/feedback:83,113 | hardcoded tag names, not using constants | DONE |

### LOW

| # | File:Line | Issue | Status |
|---|-----------|-------|--------|
| 21 | dashboard/models:28 | TextField ignores max_length in PG | TODO |
| 22 | settings/dev:68 | DIRS includes BASE_DIR (too broad) | TODO |
| 23 | users/views:37 | no auto-login after signup (UX) | TODO |

## Action Items

- [x] **P0 (배포 차단)**: #1-5 CRITICAL 전부 수정
- [x] **P1 (성능/버그)**: #7 N+1 쿼리, #10 월간 목표 계산 버그
- [x] **P2 (코드 품질)**: #8-9 중복 제거, #12 미들웨어 순서
- [ ] **P3 (개선)**: #13,15-18,21-23 남은 이슈들

## Summary

| Severity | Count | Done |
|----------|-------|------|
| CRITICAL | 5 | 5 |
| HIGH | 7 | 7 |
| MEDIUM | 8 | 4 |
| LOW | 3 | 0 |
| **Total** | **23** | **16** |
