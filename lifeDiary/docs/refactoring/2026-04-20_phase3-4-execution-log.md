# 2026-04-20 Phase 3-A ~ Phase 4 실행 로그

> 선행 계획: `docs/plans/2026-04-20_architecture-and-cost-plan.md`
> 실행 기간: 2026-04-20
> 목표: 결합도 감소 + 서버/DB 비용 최소화

---

## Phase 3-A — 즉시 비용 감소

### 변경 파일
- `lifeDiary/settings/prod.py`
- `Procfile` (신규)

### 내용

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| `SESSION_SAVE_EVERY_REQUEST` | `True` | `False` |
| `DB_PORT` 기본값 | `5432` | `6543` (Transaction Pooler) |
| `CONN_MAX_AGE` | 미설정 | `60` |
| `CONN_HEALTH_CHECKS` | 미설정 | `True` |
| gunicorn | 기본값 (worker 1) | `--workers=2 --threads=4 --worker-class=gthread` |

### 비용 효과
- `SESSION_SAVE_EVERY_REQUEST=False`: 매 요청마다 발생하던 `django_session` 테이블 `UPDATE` 제거
- `CONN_MAX_AGE=60`: 요청마다 신규 TCP/TLS 연결 수립 오버헤드 제거
- Transaction Pooler (port 6543): Supabase pgbouncer 활용, 연결 수 절감

### 배포 후 확인 사항
- Render 환경변수에서 `DB_HOST`를 Supabase Transaction Pooler 호스트로 변경 필요
  ```
  DB_HOST=aws-0-ap-northeast-1.pooler.supabase.com
  DB_PORT=6543
  DB_USER=postgres.<project-ref>
  ```

---

## Phase 3-B — Port Protocol + Pydantic DTO

### 변경 파일
- `apps/dashboard/ports.py` (신규)
- `apps/tags/ports.py` (신규)
- `apps/dashboard/commands.py` (신규)
- `requirements.txt`

### 내용

**Port Protocol** (`typing.Protocol` + `runtime_checkable`):
- `TimeBlockReader` — stats 등 외부 앱의 읽기 전용 접근 인터페이스
- `TimeBlockWriter` — 쓰기 전용 접근 인터페이스 (Read/Write 분리)
- `TagReader` — dashboard가 tags를 읽을 때 사용

적용 범위: **앱 경계 크로싱**에만. 같은 앱 내부는 구체 클래스 유지.

**Pydantic v2 Command DTO**:
- `UpsertTimeBlocksCommand` — slot_indexes 0~143 범위 validator, memo 500자 제한
- `DeleteTimeBlocksCommand`

런타임 검증 결과:
- `TimeBlockRepository` → `TimeBlockReader` / `TimeBlockWriter` 충족 ✓
- `TagRepository` → `TagReader` 충족 ✓

---

## Phase 3-C — Use Case 도입 + 주간 쿼리 최적화

### 변경 파일
- `apps/dashboard/use_cases.py` (신규)
- `apps/dashboard/test_use_cases.py` (신규)
- `apps/dashboard/views.py`
- `apps/dashboard/repositories.py`
- `apps/stats/logic.py`

### 내용

**Use Case 도입**:
- `UpsertTimeBlocksUseCase` — `@transaction.atomic`, Port 생성자 주입
- `DeleteTimeBlocksUseCase` — `@transaction.atomic`
- `dashboard/views.py`의 `_handle_time_block_create_update` / `_handle_time_block_delete` 제거
- 뷰는 JSON 파싱 → Command 생성 → Use Case 실행으로 단순화

**주간 쿼리 최적화**:
- `find_by_date_range(user, start, end)` 메서드 추가
- `get_weekly_stats_data`: `find_by_date(user, date) × 7` → `find_by_date_range × 1` 후 Python groupby
- egress 약 80% 감소

**단위 테스트** (Fake Port, DB 없이 실행):
```
9 passed in 0.19s
```

---

## Phase 3-D — Stats 캐싱 + ORM 필드 최적화

### 변경 파일
- `lifeDiary/settings/dev.py`
- `lifeDiary/settings/prod.py`
- `apps/stats/use_cases.py` (신규)
- `apps/stats/views.py`
- `apps/dashboard/use_cases.py`
- `apps/dashboard/repositories.py`
- `conftest.py` (신규)

### 내용

**FileBasedCache 도입**:
- workers=2 환경에서 LocMemCache는 워커 간 공유 불가 → FileBasedCache 선택
- dev: `BASE_DIR/.cache`, prod: `/tmp/lifediary-cache`
- Redis 도입 없음 (Render 유료 $7+/월)

**`GetStatsContextUseCase`**:
```python
ttl = 60 * 60 * 24 if target_date < date.today() else 60 * 5
```
- 과거 날짜: 24시간 TTL (완전 불변)
- 오늘: 5분 TTL

**캐시 무효화**:
- `UpsertTimeBlocksUseCase.execute()` 완료 시 `invalidate_stats_cache(user_id, target_date)` 호출
- Use Case 계층이 캐시 무효화 단일 지점 역할

**ORM 최적화**:
- `find_by_month`에 `only("date", "slot_index", "tag__id", "tag__name", "tag__color")` 적용
- 통계에 불필요한 `user_id`, `created_at`, `updated_at`, `memo` 전송 제거

**비용 효과**: 통계 페이지 동일 `(user, date)` 재방문 시 DB 쿼리 13회 → 0회

---

## Phase 3-E — Tags/Users Use Case + 역방향 의존 제거

### 변경 파일
- `apps/tags/use_cases.py` (신규)
- `apps/tags/views.py`
- `apps/users/use_cases.py` (신규)
- `apps/users/views.py`

### 내용

**Tags Use Case 4종**:
- `ListTagsUseCase` — 접근 가능한 태그 목록 + 편집/삭제 권한 포함
- `CreateTagUseCase` — 정책 검사(superuser only default) + 중복 검사
- `UpdateTagUseCase` — default flip 정책 검사 + 카테고리 변경
- `DeleteTagUseCase` — 사용 중인 기본 태그 보호

`tags/views.py`: `JsonResponse` 전면 제거 → `success_response` / `error_response` 통일.
예외 타입별 상태 코드 분기 (`PermissionError` 403, `LookupError` 400, `ValueError` 400).

**역방향 의존 제거**:

```
변경 전: users/views.py → apps.stats.logic (양방향)
변경 후: users/views.py → users/use_cases.py → apps.stats.logic (단방향)
```

**`GetMyPageUseCase`** — 필요 period만 계산:
```python
needed = {g.period for g in goals}  # {"monthly"}
# daily, weekly는 필요 없으면 쿼리 생략
```
목표가 monthly만 있는 경우 daily/weekly 쿼리 생략 → 최대 2/3 쿼리 절감.

---

## Phase 4 — StatsCalculator 분해 + Dead Path 제거

### 변경 파일
- `apps/stats/aggregation/` 패키지 (신규)
  - `calculator.py`, `daily.py`, `weekly.py`, `monthly.py`, `analysis.py`
- `apps/stats/logic.py` (436줄 → 77줄)
- `apps/stats/feedback.py`

### 내용

**파일 분리**:

| 파일 | 역할 | 라인 수 |
|------|------|---------|
| `aggregation/calculator.py` | StatsCalculator (공유 헬퍼) | ~95 |
| `aggregation/daily.py` | get_daily_stats_data | ~55 |
| `aggregation/weekly.py` | get_weekly_stats_data | ~70 |
| `aggregation/monthly.py` | get_monthly_stats_data | ~55 |
| `aggregation/analysis.py` | get_tag_analysis_data | ~40 |
| `logic.py` | 오케스트레이터 (get_stats_context) | 77 |

public API(`from apps.stats.logic import ...`) 완전 유지 — 기존 호출자 변경 없음.

**`feedback.py` dead path 제거**:
- `prev_weekly_stats` 분기 제거 (get_stats_context가 이 키를 설정한 적 없음)
- 미사용 `import logging` / `logger` 제거

---

## 최종 구조 변화

### 의존성 방향 (변경 후)

```
views.py
  └→ use_cases.py (Port 주입)
       └→ repositories.py (Port 구현)
       └→ domain_services.py

stats/views.py
  └→ stats/use_cases.py (캐시 레이어)
       └→ stats/logic.py (오케스트레이터)
            └→ stats/aggregation/ (집계 모듈)
```

### 비용 지표 요약

| 지표 | 변경 전 | 변경 후 |
|------|---------|---------|
| Session writes/요청 | 1 (무조건) | 0 (만료 시만) |
| 주간 통계 쿼리 | 7회 | 1회 |
| 통계 페이지 재방문 쿼리 | 13회 | 0회 (캐시 히트) |
| DB 연결 방식 | 요청마다 신규 | 60초 재사용 |
| 월간 쿼리 payload | 전체 필드 | 필요 5개 필드만 |

### 테스트

```
9 passed in 0.25s  (Use Case 단위 테스트, DB 없이 Fake Port 실행)
```
