# 2026-04-20 Architecture Modernization & Cost Optimization Plan

> 작성일: 2026-04-20
> 선행 문서: `docs/refactoring/2026-04-20_backend-flow-and-improvements.md`
> 스택 제약: **Python + Django 5.2 유지** (DRF 전환 없음). Render + Supabase 무료/저가 티어 가정.
> 목표: 결합도를 낮추고 응집도를 높이는 구조 개선을 **서버/DB 비용 증가 없이** 달성한다.

---

## 1. 배경 및 제약

### 1.1 현재 인프라

| 항목 | 구성 | 비용 민감도 |
|------|------|------------|
| 호스팅 | Render (`lifediary.onrender.com`) | Free → Starter $7/월 또는 Free sleep 허용 |
| DB | Supabase PostgreSQL | Free 500MB / 2GB egress/월, Pro $25/월부터 |
| Static | WhiteNoise (Django 프로세스가 직접 서빙) | 무료 |
| Session | Django DB backend (`django_session` 테이블) | **요청당 write** — 숨은 비용 |
| Cache | 미설정 | — |
| App Server | gunicorn (워커 수 명시 없음) | 메모리/CPU 사용량 직결 |

### 1.2 비용 드라이버 식별

현재 코드에서 **요청당 비용**에 영향을 주는 지점:

1. **통계 페이지 (`/stats/`)**: 한 번 로드 시 DB 쿼리 **최소 13회**
   - `find_by_date` × 7 (주간)
   - `find_by_month` × 2 (월간 + 태그분석)
   - `find_daily_counts` × 2 (월간 + 분석)
   - `find_by_period` × 3 (daily/weekly/monthly goals)
   - `find_latest` × 1 (note)
2. **`SESSION_SAVE_EVERY_REQUEST=True`**: 세션 테이블에 매 요청 `UPDATE` — **정적 리소스 요청 제외 전부 쓰기**
3. **`CONN_MAX_AGE` 미설정**: 매 요청 신규 연결 수립 → Supabase pgbouncer 유효 활용 불가
4. **TimeBlock 데이터 누적**: 유저 1명 × 1년 = 최대 52,560 rows. 유저 1,000명이면 5천만 rows → Free 티어 500MB 초과 구간 진입
5. **통계 JSON blob 직렬화**: `daily_stats_json`, `weekly_stats_json`, `monthly_stats_json`, `tag_analysis_json` 4종을 페이지마다 생성 후 HTML에 삽입 → **egress 증가**

이 문서는 구조 개선과 비용 최적화를 **같은 리팩터링 내에서** 달성하는 경로를 정의한다.

---

## 2. 구조 개선 전략 — 3축

### 2.1 축 1. 의존성 역전 (DIP) — `typing.Protocol` 기반 Port

현재 `stats/logic.py`가 `TimeBlockRepository` **구체 클래스**에 의존한다. Protocol을 도입해 역전시킨다.

```python
# apps/dashboard/ports.py  (신규)
from typing import Protocol
from datetime import date

class TimeBlockReader(Protocol):
    def find_by_date(self, user_id: int, day: date) -> list: ...
    def find_by_month(self, user_id: int, start: date, end: date) -> list: ...
    def find_daily_counts(self, user_id: int, start: date, end: date) -> dict: ...

class TimeBlockWriter(Protocol):
    def bulk_create(self, blocks: list) -> None: ...
    def bulk_update(self, blocks: list, fields: list[str]) -> None: ...
    def delete_by_slots(self, user_id: int, day: date, slot_indexes: list[int]) -> int: ...
```

- **스코프 제한**: Protocol은 **앱 경계 크로싱**(stats → dashboard, tags → dashboard)에만 적용. 같은 앱 내부는 구체 클래스로 유지.
- **Read/Write 분리**: stats는 `TimeBlockReader`만 주입 → 실수로 write를 호출할 수 없게 됨 (Interface Segregation).
- **비용 영향**: 없음. 런타임 오버헤드 0.

### 2.2 축 2. 경계 DTO — Pydantic v2 최소 도입

외부 경계에만 도입한다. 내부 집계 구조(dict)는 유지.

```python
# apps/dashboard/commands.py  (신규)
from pydantic import BaseModel, Field, field_validator
from datetime import date

class UpsertTimeBlocksCommand(BaseModel):
    user_id: int
    target_date: date
    slot_indexes: list[int] = Field(min_length=1)
    tag_id: int
    memo: str = Field(default="", max_length=500)

    @field_validator("slot_indexes")
    @classmethod
    def validate_slots(cls, v: list[int]) -> list[int]:
        if not all(0 <= i < 144 for i in v):
            raise ValueError("슬롯 인덱스는 0~143 범위여야 합니다.")
        return v
```

- **스코프**: Command(쓰기 입력), Query 응답의 **경계**에만. `StatsContext` 전체를 모델링하지 않음.
- **비용 영향**: Pydantic v2는 Rust 코어. 검증 자체 비용은 µs 단위. 오히려 **검증 분산 제거**로 전체 CPU 감소.

### 2.3 축 3. Use Case + 생성자 주입 — 모듈 싱글턴 철폐

현재 `_time_block_repo = TimeBlockRepository()` 전역 싱글턴은 테스트·교체 불가하다.

```python
# apps/dashboard/use_cases.py  (신규)
from dataclasses import dataclass
from django.db import transaction

@dataclass(frozen=True)
class UpsertResult:
    created: int
    updated: int
    tag_id: int

class UpsertTimeBlocksUseCase:
    def __init__(self, reader, writer, tags):
        self._reader = reader
        self._writer = writer
        self._tags = tags

    @transaction.atomic
    def execute(self, cmd: UpsertTimeBlocksCommand) -> UpsertResult:
        tag = self._tags.find_by_id_accessible(cmd.tag_id, cmd.user_id)
        if not tag:
            raise PermissionError("태그 접근 권한 없음")

        existing = {b.slot_index: b for b in self._reader.find_by_slots(...)}
        # ... 분류, bulk_create, bulk_update ...
        return UpsertResult(created=..., updated=..., tag_id=tag.id)
```

- **DI 라이브러리 도입 ❌**: `dependency-injector`는 이 규모에서 오버킬. **뷰 함수 최상단에서 수동 와이어링**이 최선.
- **비용 영향**: 없음. 오히려 `@transaction.atomic` 보강으로 **부분 반영 롤백 쿼리 감소**.

### 2.4 3축이 비용에 주는 효과

| 축 | 비용 영향 | 이유 |
|----|----------|------|
| Protocol | 중립 | 정적 타입 검사용, 런타임 동일 |
| DTO | 감소 | 검증 중복 제거 + 응답 크기 명시화 → egress 예측 가능 |
| Use Case | 감소 | 트랜잭션 경계 명확화 + 캐시 삽입 지점 단일화 |

특히 Use Case 계층은 **캐시를 끼워 넣기 최적의 레이어**다. 뷰(HTTP 캐시)와 Repository(쿼리 캐시) 사이의 비어 있는 자리.

---

## 3. 비용 최적화 전략 — 7개

우선순위는 **효과 대비 구현 비용** 기준으로 정렬.

### 3.1 P1. `SESSION_SAVE_EVERY_REQUEST` 해제 ★ (5분, 즉시 감소)

현재 `prod.py:41`에 `SESSION_SAVE_EVERY_REQUEST = True`가 설정돼 있다. 이 옵션은 **모든 요청마다 세션 테이블에 UPDATE**를 발생시킨다.

**영향 측정**:
- 활성 유저 100명 × 페이지 10개 = 1,000 session writes/day (보수적)
- 실제 페이지 내 fetch까지 고려하면 5~10배
- Supabase Free egress 2GB/월 한계에 빠르게 접근

**조치**:
```python
# prod.py
SESSION_SAVE_EVERY_REQUEST = False  # 기본값
# SESSION_COOKIE_AGE = 3600는 유지. Django는 만료 시점이 가까워지면 자동 갱신
```

세션 만료 갱신이 필요하면 `SESSION_COOKIE_AGE`에 의존하지 말고 **signed cookie 기반 세션**으로 전환:

```python
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
```

- DB 완전 제거 (write 0, read 0)
- 트레이드오프: 세션 데이터 크기 4KB 제한, 서버 측 무효화 불가
- 이 프로젝트는 user_id만 세션에 저장되므로 적합

### 3.2 P1. `CONN_MAX_AGE` + Supabase Transaction Pooler (10분)

현재 매 요청 **신규 TCP + TLS + psycopg 연결** 수립. Render↔Supabase 왕복 100ms+.

```python
# prod.py
DATABASES["default"]["CONN_MAX_AGE"] = 60       # 60초 재사용
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DATABASES["default"]["OPTIONS"] = {
    "pool": {"min_size": 0, "max_size": 4},     # psycopg3 내장 pool
}
```

**Supabase 연결 문자열**:
- Direct connection (port 5432): 느림, long-lived connection 권장 안 함
- **Transaction Pooler (port 6543)**: 이 프로젝트에 최적. 단 `prepared statements` 사용 금지 (Django 기본 OFF)

```bash
DB_HOST=aws-0-ap-northeast-1.pooler.supabase.com
DB_PORT=6543
DB_USER=postgres.<project-ref>
```

**비용 효과**: 요청당 DB 연결 오버헤드 제거 → 응답 속도 ~30% 감소 → Render CPU time 감소.

### 3.3 P1. `get_weekly_stats_data` 7쿼리 → 1쿼리 (30분)

현재 주간 통계는 `find_by_date(date)` × 7을 순차 호출한다. Supabase egress와 지연 모두에 불리.

```python
# apps/dashboard/repositories.py — 추가
def find_by_date_range(self, user_id: int, start: date, end: date):
    return (
        TimeBlock.objects
        .filter(user_id=user_id, date__range=[start, end])
        .select_related("tag")
        .only("id", "date", "slot_index", "tag__id", "tag__name", "tag__color")
    )
```

이후 `get_weekly_stats_data`에서 Python 측에서 date별로 그룹핑. **쿼리 7회 → 1회**, egress 80% 감소.

### 3.4 P2. 통계 결과 캐싱 — Django LocMemCache + ETag (2시간)

통계 페이지의 DB 쿼리 13회는 **동일 (user, date) 조합에서 결과 불변**이다. 특히 **과거 날짜는 완전 불변**이므로 장기 캐싱 가능.

```python
# prod.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "stats-cache",
        "OPTIONS": {"MAX_ENTRIES": 500},
    }
}
```

**Redis 도입 금지**: Render 유료 Redis $7/월부터. 단일 워커 gunicorn이면 LocMemCache면 충분.

```python
# apps/stats/use_cases.py
from django.core.cache import cache
import hashlib

class GetStatsContextUseCase:
    def execute(self, user_id: int, target_date: date):
        is_past = target_date < date.today()
        cache_key = f"stats:{user_id}:{target_date.isoformat()}"
        ttl = 60 * 60 * 24 if is_past else 60 * 5  # 과거 24h, 오늘 5min

        if cached := cache.get(cache_key):
            return cached

        context = self._build_context(user_id, target_date)
        cache.set(cache_key, context, ttl)
        return context
```

**무효화 지점**: `UpsertTimeBlocksUseCase.execute()` 성공 시 `cache.delete_many([f"stats:{uid}:{d}"])` 호출. Use Case 계층이 있어야 이 패턴이 깔끔해지는 이유.

**HTTP 캐시 추가 (무료)**:
```python
# apps/stats/views.py
from django.views.decorators.cache import cache_control
from django.views.decorators.http import last_modified

@cache_control(private=True, max_age=300)
def index(request): ...
```

### 3.5 P2. ORM `only()` / `values_list()` 도입 — egress 감소 (1시간)

현재 `TimeBlock.objects.filter(...)`는 `user_id`, `created_at`, `updated_at`, `memo` 등 **통계에 쓰지 않는 필드를 전부 가져온다**. 월간 4,320 rows 기준 수십 KB 불필요 egress.

```python
# 집계용 쿼리는 필요한 필드만
def find_by_month_for_stats(self, user_id: int, start, end):
    return (
        TimeBlock.objects
        .filter(user_id=user_id, date__range=[start, end])
        .select_related("tag")
        .only("date", "slot_index", "tag__name", "tag__color")
    )
```

`find_daily_counts`는 이미 `values_list` 기반이므로 양호.

**측정**: `django-debug-toolbar`로 쿼리당 row size 확인 → 쿼리 payload 30~50% 감소 예상.

### 3.6 P3. `mypage`의 불필요 통계 계산 제거 (30분)

현재 `mypage`는 목표 period와 무관하게 **daily+weekly+monthly 3종 모두 계산**한다. 사용자 목표가 monthly뿐이어도 일간 주간 집계가 돌아간다.

```python
# apps/users/use_cases.py
class GetMyPageUseCase:
    def execute(self, user_id: int):
        goals = self._goals.find_by_user(user_id)
        needed_periods = {g.period for g in goals}  # {"monthly"}
        stats_bundle = self._stats.compute_only(user_id, periods=needed_periods)
        self._progress.attach_progress(goals, **stats_bundle)
        return MyPageView(goals=goals, note=self._notes.find_latest(user_id))
```

**효과**: 목표가 1개 period만 있는 일반적인 경우 DB 쿼리 2/3 감소.

### 3.7 P3. 오래된 데이터 집계 및 원본 정리 (2일, 나중)

TimeBlock 누적 속도가 Supabase Free 500MB에 접근할 때 착수.

- `TimeBlockDailyAggregate(user, date, tag, minutes)` 테이블 추가
- 6개월 지난 데이터를 일별 집계 후 원본 `TimeBlock` 삭제
- 통계 조회 시 "최근 6개월은 원본, 그 이상은 집계" 분기
- Django management command로 `manage.py compact_history` 수동 실행 (cron 대신)

**현 시점 착수 금지**: 사용자 수 1,000명 돌파 후 재평가. 지금은 과엔지니어링.

---

## 4. 기타 설정 튜닝 (단발성)

| 항목 | 조치 | 효과 |
|------|------|------|
| `gunicorn` 워커 수 | `--workers=2 --threads=4 --worker-class=gthread` | Render Starter 512MB에 최적. 현재 기본값(1 worker)은 동시 요청 처리 불가 |
| `WhiteNoise` 압축 | `CompressedManifestStaticFilesStorage` 이미 사용 ✓ | — |
| 정적 파일 `Cache-Control` | `WHITENOISE_MAX_AGE = 31536000` 추가 | 브라우저 캐싱 1년 |
| DB 인덱스 | 현재 `idx_user_date`, `idx_user_tag`, `idx_date_slot` 3개 | 적절. 추가 불필요 |
| `DEFAULT_AUTO_FIELD` | `BigAutoField` 유지 | 4B 차이는 무시 가능 |
| `psycopg` | 이미 v3 사용 ✓ | — |

---

## 5. Phase 실행 순서

구조 축(§2)과 비용 축(§3)을 **교차 진행**한다. 리팩터링만 먼저 하면 비용 개선이 늦어지고, 비용 튜닝만 하면 코드가 그대로 남는다.

### Phase 3-A — 즉시 비용 감소 ✅ 완료 (2026-04-20)

| 순서 | 작업 | 효과 |
|------|------|------|
| 1 | `SESSION_SAVE_EVERY_REQUEST=False` (§3.1) | Supabase write 즉시 감소 |
| 2 | `CONN_MAX_AGE=60` + Transaction Pooler (§3.2) | 연결 오버헤드 제거 |
| 3 | `gunicorn --workers=2 --threads=4` (§4) | 동시 요청 처리 |

**효과 측정**: Supabase 대시보드에서 일일 DB egress/writes 추이 확인.

### Phase 3-B — Port + DTO 도입 ✅ 완료 (2026-04-20)

| 순서 | 작업 | 파일 |
|------|------|------|
| 1 | Port Protocol 작성 | `apps/{dashboard,tags}/ports.py` |
| 2 | 기존 Repository가 Port를 구현하도록 타입 힌트 추가 | 기존 `repositories.py` |
| 3 | `UpsertTimeBlocksCommand` Pydantic 모델 | `apps/dashboard/commands.py` |
| 4 | `requirements.txt`에 `pydantic>=2.7` 추가 | `requirements.txt` |

### Phase 3-C — 첫 Use Case + 캐시 배선 ✅ 완료 (2026-04-20)

| 순서 | 작업 |
|------|------|
| 1 | `UpsertTimeBlocksUseCase` 구현 (§2.3) + `@transaction.atomic` |
| 2 | `dashboard/views.py`의 `_handle_*` 제거, Use Case 호출로 교체 |
| 3 | pytest 기반 Use Case 단위 테스트 (fake Port 주입) |
| 4 | `find_by_date_range` 추가, `get_weekly_stats_data` 1쿼리화 (§3.3) |

### Phase 3-D — Stats Use Case + 캐싱 ✅ 완료 (2026-04-20)

| 순서 | 작업 |
|------|------|
| 1 | `GetStatsContextUseCase` 추출 (§3.4) |
| 2 | `CACHES` 설정 + LocMemCache |
| 3 | 과거/현재 TTL 분리 캐싱 |
| 4 | `UpsertTimeBlocksUseCase`에 cache invalidation 추가 |
| 5 | `only()` / `values_list()` 적용 (§3.5) |

### Phase 3-E — Tags + Users 확산 ✅ 완료 (2026-04-20)

| 순서 | 작업 |
|------|------|
| 1 | Tags Use Case 4종 (List/Create/Update/Delete) |
| 2 | `tags/views.py` 응답을 `success_response/error_response`로 통일 |
| 3 | `GetMyPageUseCase` + 필요 period만 계산 (§3.6) |
| 4 | `users → stats` 역방향 의존 제거 |

### Phase 4 — StatsCalculator 분해 ✅ 완료 (2026-04-20)

`stats/aggregation/{daily,weekly,monthly,analysis}.py`로 분리.
`prev_weekly_stats` dead path 제거 (get_stats_context가 이 키를 설정한 적 없음 확인).
FeedbackInput DTO는 현재 규모에서 불필요 → 도입 안 함.

---

## 6. 성공 지표

구현이 끝나면 다음 수치로 검증한다.

### 6.1 비용 지표 (Supabase 대시보드)

| 지표 | Before (예상) | After 목표 |
|------|--------------|------------|
| Session writes/일 | 세션당 100+ | 0 (cookie 세션) 또는 2~5 (DB 세션 유지 시) |
| 통계 페이지 평균 쿼리 수 | 13회 | 캐시 히트 0회 / 미스 시 5회 |
| DB egress/월 | 측정 필요 | 현재의 40% 이하 |

### 6.2 성능 지표 (Django debug toolbar / 로그)

| 지표 | 측정 방법 |
|------|----------|
| `/stats/` 평균 응답 시간 | `logger.info("stats response", duration_ms=...)` 추가 |
| 쿼리당 row 크기 | `django-debug-toolbar` |
| 캐시 히트율 | `cache.get_many` 결과 카운트 |

### 6.3 구조 지표 (grep 기반)

```bash
# 뷰가 models를 직접 import하지 않는지 (0)
grep -rn "from .models import\|from apps\..*models import" \
  apps/*/views.py apps/stats/logic.py

# 뷰가 logic/계산 모듈을 직접 호출하지 않는지 (Phase 3-E 이후 0)
grep -rn "from apps\.stats\.logic" apps/*/views.py

# Use Case 단위 테스트가 DB 없이 돌아가는지
pytest apps/ --no-cov -m "unit"  # Django TestCase 제외
```

---

## 7. 과엔지니어링 금지 리스트

이 계획에서 **의도적으로 제외한 항목**과 제외 이유.

| 기법 | 제외 이유 |
|------|----------|
| Redis / Memcached | Render 유료 요금 $7+/월. LocMemCache + single worker로 충분 |
| Celery / RQ | 현재 백그라운드 작업 없음. 통계 캐시는 lazy 계산으로 족함 |
| `dependency-injector` 라이브러리 | 수동 생성자 주입이 충분 |
| DRF | §이전 검토 참조. SSR 지배 프로젝트에 부적합 |
| django-ninja | API 5개 내외에선 불필요. 15개+ 되면 재검토 |
| Domain Events / Signals | TimeBlock 저장 후 side effect 거의 없음 (캐시 invalidation은 Use Case 내부) |
| Read Replica / CQRS 본격 도입 | 트래픽 규모 미달 |
| Async Views | Django ORM async가 `select_related` 쓰기에 미성숙 |
| TimeBlock 샤딩/파티셔닝 | Postgres 단일 테이블 1억 rows까지 정상 |
| Result / Either 타입 | 팀 학습 비용 > 이득 |

---

## 8. 리스크 체크리스트

- [ ] Signed cookie 세션 전환 시, 기존 세션 전부 무효화됨. **배포 공지** 필요
- [ ] Transaction Pooler (port 6543)는 `LISTEN/NOTIFY`, `prepared statements`, `session-level` 기능 불가. 현재 프로젝트는 사용 안 함 확인
- [ ] LocMemCache는 **워커 간 공유 불가**. `--workers=2` 설정 시 각 워커별 캐시 → invalidation 누락 가능. 해결책: (a) worker=1 유지하거나 (b) `filebased.FileBasedCache` 사용
- [ ] Use Case 도입 시 기존 테스트가 Django TestCase 기반이라 **pytest 전환 비용** 발생. Phase 3-C에서 결정
- [ ] Pydantic v2는 Python 3.8+ 필요. 현재 환경 확인됨 (Django 5.2는 Python 3.10+)

---

## 9. 참고: 측정 우선 원칙

이 계획의 효과는 **배포 후 측정**으로 검증되기 전까지는 가설이다.

```python
# apps/core/middleware.py  (신규, 선택적)
import time, logging

logger = logging.getLogger("metrics")

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "request",
            extra={
                "path": request.path,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 1),
                "user_id": getattr(request.user, "id", None),
            },
        )
        return response
```

Render 로그 → `duration_ms` 집계. Phase 3-A 전후 비교 가능.
