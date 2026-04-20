# 2026-04-21 Architecture & Cost Plan (Post-Phase 4 Snapshot)

> 작성일: 2026-04-21
> 선행 문서: `docs/plans/2026-04-20_architecture-and-cost-plan.md` (Phase 3~4 계획), `docs/refactoring/2026-04-21_backend-flow-and-improvements.md`
> 스택 제약: Python + Django 5.2 유지. Render + Supabase 무료/저가 티어.
> 목표: Phase 3~4 적용 이후의 **현재 상태**를 스냅샷으로 정리하고, 비용 증가 없이 남아 있는 다음 단계를 명시한다.

---

## 1. 현재 인프라 스냅샷

### 1.1 런타임

| 항목 | 구성 | 비고 |
|------|------|------|
| 호스팅 | Render (`lifediary.onrender.com`) | `gunicorn --workers=2 --threads=4 --worker-class=gthread` |
| DB | Supabase PostgreSQL, **Transaction Pooler (port 6543)** | `CONN_MAX_AGE=60`, `CONN_HEALTH_CHECKS=True` |
| Static | WhiteNoise + `CompressedManifestStaticFilesStorage` | 해시 기반 캐시 버스팅 |
| Session | Django DB backend, `SESSION_SAVE_EVERY_REQUEST=False` | 요청당 write 제거 완료 |
| Cache | `FileBasedCache` (`dev: BASE_DIR/.cache`, `prod: /tmp/lifediary-cache`), `MAX_ENTRIES=500` | 워커 간 공유 가능 |
| 인증 | `django-axes 7.0.1` + Django ModelBackend 2단 | `AXES_FAILURE_LIMIT=5`, `AXES_COOLOFF_TIME=1h` |
| i18n | `LANGUAGE_CODE="ko-kr"`, `LANGUAGES=[ko, en]`, `USE_I18N=True` | `locale/en` 스캐폴드 완료 |

### 1.2 운영 보안 설정

| 항목 | 상태 |
|------|------|
| `SECURE_SSL_REDIRECT` | True (prod) |
| `SECURE_HSTS_SECONDS` | 31536000 (1년) + INCLUDE_SUBDOMAINS + PRELOAD |
| `SESSION_COOKIE_SECURE` | True (prod) |
| `CSRF_COOKIE_SECURE` | True (prod) |
| `SESSION_EXPIRE_AT_BROWSER_CLOSE` | True (prod), `SESSION_COOKIE_AGE=3600` |
| CSP 헤더 | **미도입** |
| `SESSION_COOKIE_HTTPONLY/SAMESITE` | 명시 미설정 (Django 기본 의존) |
| `prod.py` `DEBUG` | **현재 True** — `3c19106 production debug` 커밋으로 임시 켜져 있음. 배포 전 반드시 `False` 복구 필요 |

### 1.3 프론트엔드 공급망

| 라이브러리 | 버전 | SRI |
|-----------|------|-----|
| Chart.js | 3.9.1 | sha384 |
| chartjs-adapter-date-fns | 2.0.0 | sha384 |
| htmx | 1.9.12 | sha384 |
| Alpine.js | 3.14.9 (고정) | sha384 |

---

## 2. 적용된 구조 개선

선행 계획 문서가 제시한 3축이 모두 코드에 반영됨.

### 2.1 축 1 — Port 기반 의존성 역전

- `apps/dashboard/ports.py`: `TimeBlockReader`, `TimeBlockWriter`
- `apps/tags/ports.py`: `TagReader`
- `stats` 경로가 `dashboard.repositories.TimeBlockRepository` **구체 클래스**에 의존하지 않고 Protocol 경유
- Use Case 생성자 주입(테스트에서 가짜 Port 주입 가능)

### 2.2 축 2 — 경계 DTO (Pydantic v2)

- `apps/dashboard/commands.py`: `UpsertTimeBlocksCommand`, `DeleteTimeBlocksCommand`
- 슬롯 범위(0~143), `min_length=1`, memo `max_length=500`를 모델 밖 경계에서 보장
- 내부 집계는 여전히 dict 기반 — 도입 scope 최소화

### 2.3 축 3 — Use Case + 생성자 주입

- `dashboard/use_cases.py`: `UpsertTimeBlocksUseCase`, `DeleteTimeBlocksUseCase`
- `tags/use_cases.py`: `List/Create/Update/Delete` 4종
- `users/use_cases.py`: `SaveGoalUseCase`, `DeleteGoalUseCase`, `SaveNoteUseCase`, `DeleteNoteUseCase`, `GetMyPageUseCase`
- `stats/use_cases.py`: `GetStatsContextUseCase`, `invalidate_stats_cache`
- `@transaction.atomic`이 쓰기 Use Case에 일괄 적용 → 부분 반영 위험 제거
- 캐시 무효화가 쓰기 Use Case 내부 단일 지점에서 발생

---

## 3. 적용된 비용 최적화

### 3.1 요청당 DB write 제거

- `SESSION_SAVE_EVERY_REQUEST=False` (prod) — 세션 테이블에 요청당 UPDATE 중단

### 3.2 연결 풀

- `CONN_MAX_AGE=60`, `CONN_HEALTH_CHECKS=True`
- Supabase Transaction Pooler(port 6543) — prepared statement 미사용(Django 기본 OFF) 확인됨

### 3.3 쿼리 수 축소

- `find_by_date_range` 도입으로 주간 집계 7쿼리 → 1쿼리
- `find_daily_counts`는 `values_list` 기반으로 유지
- 집계 쿼리에 `select_related("tag")` + 필요한 필드만 조회

### 3.4 통계 응답 캐시

- `FileBasedCache`에 `stats:{uid}:{date}` 키로 저장
- TTL: 과거 날짜 24h, 오늘 5min
- 쓰기 시 `invalidate_stats_cache(user_id, target_date)` 단일 호출로 무효화
- Redis/Memcached 미도입 — 비용 0

### 3.5 마이페이지 계산 범위 축소

- `GetMyPageUseCase`가 사용자의 목표 period 집합만 계산 (`daily`만 있으면 weekly/monthly 집계 생략)
- AJAX partial(`mypage_goals_partial`)로 목표 저장 후 목록만 갱신 — 전체 페이지 리렌더 생략

### 3.6 gunicorn 워커 구성

- `--workers=2 --threads=4 --worker-class=gthread` — Render Starter 512MB 환경에 맞춘 동시성

### 3.7 과엔지니어링 방지(의도적 제외 항목, 유지)

| 기법 | 제외 이유 |
|------|----------|
| Redis/Memcached | Render 유료 $7+/월. 단일 워커·FileBasedCache로 충분 |
| Celery/RQ | 백그라운드 작업 없음 |
| `dependency-injector` | 수동 생성자 주입으로 충분 |
| DRF / django-ninja | SSR 지배 + API 15개 미만 |
| Domain Events / Signals | 쓰기 후 side effect는 캐시 무효화뿐 (Use Case 내부 호출) |
| CQRS / Read Replica | 트래픽 규모 미달 |
| Async Views | ORM async 미성숙 |
| TimeBlock 샤딩/파티셔닝 | 단일 테이블 1억 rows까지 정상 |
| Result/Either 타입 | 학습 비용 > 이득 |
| `FeedbackInput` DTO | 현재 피드백 규모에서 오버엔지니어링 |

---

## 4. 남은 우선순위

### 4.1 P1 — 운영 전 반드시

| 항목 | 조치 |
|------|------|
| `prod.py` `DEBUG = True` | `False`로 복구. settings 변경은 독립 PR 권장 |
| 배포 체크 | `DJANGO_SETTINGS_MODULE=lifeDiary.settings.prod python manage.py check --deploy` 실행 후 로그 첨부 |

### 4.2 P2 — 측정 기반 검증

지금까지의 최적화 효과는 **실측 없이 가설 상태**다.

- `apps/core/middleware.py`의 `MetricsMiddleware` 도입
  - `duration_ms`, `path`, `method`, `status`, `user_id` 구조화 로그
  - Render 로그에서 배포 전/후 `/stats/` 응답 시간 비교 가능
- Supabase 대시보드: 세션 writes, DB egress, 쿼리 수 일일 추이
- Django 측 캐시 히트율: `cache.get_many` 결과 카운트 로깅

측정 후 이 문서의 §3을 실측 수치로 업데이트한다.

### 4.3 P3 — 보안 후속

| 항목 | 조치 |
|------|------|
| CSP 헤더 | `django-csp` 도입 검토 (`default-src 'self'` + CDN 도메인 허용리스트) |
| 세션 쿠키 플래그 | `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"` 명시 |
| CSRF 쿠키 플래그 | `CSRF_COOKIE_HTTPONLY=True` 명시 |
| axes 이벤트 | 잠금 발생 시 로깅/알림 연결 |
| 비밀번호 정책 | 최소 길이 8→10, 특수문자 요구 재검토 |

### 4.4 P4 — 장기

| 항목 | 조건 | 조치 |
|------|------|------|
| TimeBlock 아카이빙 | Supabase DB 400MB 도달 시 | `TimeBlockDailyAggregate` 테이블 + `manage.py compact_history` 명령. 현 시점 착수 금지(과엔지니어링) |
| i18n Phase 1+ | 외부 사용자 확보 후 | 45 파일 · 507+ 문자열의 gettext 적용, en 번역 |

---

## 5. 성공 지표

구현이 끝나도 수치로 검증되기 전까지는 모든 §3은 가설이다.

### 5.1 비용 지표 (Supabase)

| 지표 | Phase 3-A 이전 추정 | 현재(목표) | 측정 수단 |
|------|--------------------|-----------|-----------|
| Session writes/일 | 100+ | **0** (DB 세션 유지하되 write-on-change) | Supabase 대시보드 |
| 통계 페이지 평균 쿼리 수 | 13 | 캐시 히트 0 / 미스 5 | debug-toolbar 또는 MetricsMiddleware |
| DB egress/월 | 측정 필요 | 40% 이하 | Supabase 대시보드 |

### 5.2 성능 지표

| 지표 | 측정 방법 |
|------|----------|
| `/stats/` 평균 응답 시간 | `MetricsMiddleware`의 `duration_ms` |
| 캐시 히트율 | `cache.get` 결과 카운트 |
| 테스트 수 | `pytest` 실행 결과 |

### 5.3 구조 지표 (grep)

```bash
# 뷰 → models 직접 import (0 유지)
grep -rn "from .models import\|from apps\..*models import" \
  apps/*/views.py apps/stats/logic.py

# 뷰 → 다른 앱 logic/views (0 유지, Phase 3-E 이후)
grep -rn "from apps\.stats\.logic\|from apps\.\(stats\|dashboard\|tags\|users\)\.views" apps/*/views.py

# Use Case 생성자 주입 일관성
grep -rn "def __init__(self" apps/*/use_cases.py
```

---

## 6. 리스크 체크리스트

- [ ] `prod.py` `DEBUG=True` 상태 — 배포 전 복구 확인
- [ ] FileBasedCache는 `/tmp` 기반이므로 Render 배포 시마다 휘발. 이는 의도된 동작 (캐시는 재생성 가능)
- [ ] Transaction Pooler 제약: LISTEN/NOTIFY, prepared statement, session-level 기능 금지 — 현재 프로젝트 미사용 재확인됨
- [ ] django-axes 테스트 호환: `conftest.py`에서 `AXES_ENABLED=False`, `AUTHENTICATION_BACKENDS`를 `ModelBackend` 단일로 치환 중. 잠금 경로 자체의 회귀 테스트 부재
- [ ] FileBasedCache와 `--workers=2`의 상호작용: 현재 구성은 각 워커가 동일 파일을 읽음 → 쓰기 경쟁 시 Lock 의존. 문제 발생 시 `--workers=1` + `threads` 증가로 회피
- [ ] 마이페이지 AJAX partial이 서버 에러(5xx) 시 클라이언트 피드백이 alert 수준 — 추후 토스트 UI 고려

---

## 7. 요약

- 선행 계획(2026-04-20)의 Phase 3-A ~ Phase 4 **모두 코드에 반영 완료**.
- 추가 비용 없이 Use Case / Port / DTO / 캐시 / 연결 풀 / 세션 write 제거까지 적용.
- 남은 핵심 과제는 **운영 복구**(DEBUG False) 및 **실측**(MetricsMiddleware). 구조 개선은 P3 수준의 정리만 남음.
- CSP·세션 쿠키 플래그·비밀번호 정책은 보안 후속 사이클에서 처리 예정.
