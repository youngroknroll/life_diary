# 통계 페이지 Server-Timing 헤더 계획 (2026-09-30)

- 선행 트랙: `docs/plans/2026-09-29-stats-performance-measurement-plan.md` (PR #74 머지)
- 근거 기록: `docs/refactoring/2026-09-29-stats-performance-measurement.md`
- 브랜치: `perf/stats-measurement-verification`

## 배경

측정 트랙에서 두 가지가 남았다.

1. 운영 브라우저 측정에서 "처음 연 날짜는 서버 캐시 미스"라고 분류했지만, 서버 쪽에서 확인하지 않았다. TTFB 차이로 추정했을 뿐이다.
2. 운영 캐시 미스 TTFB 약 2.8초 가운데 로컬로 설명되는 몫은 일부다. 로컬 SQLite cold는 0.3초, 로컬 PostgreSQL 14 cold는 0.85초다. 나머지가 DB 왕복인지 서버 CPU인지 모른다(백로그 B-6).

사용자가 2026-09-30에 통계 페이지 응답에 `Server-Timing` 헤더를 붙이기로 결정했다. 브라우저 DevTools와 `PerformanceNavigationTiming.serverTiming`으로 요청마다 캐시 hit/miss, 통계 데이터 생성 시간, DB 시간, 쿼리 수를 직접 본다.

운영 엣지는 Cloudflare다. `/stats/`는 `cf-cache-status: DYNAMIC`, `Vary: Cookie`로 캐시되지 않는다. Cloudflare는 이미 `Server-Timing: cfExtPri`를 붙이고 있고, 브라우저가 이를 `serverTiming`으로 노출한다(2026-09-30 실측).

## 범위

포함:

- `GET /stats/`(`apps/stats/views.py:index`) 응답에 `Server-Timing` 헤더를 붙인다. 로그인한 사용자의 200 응답에만 붙인다.
- `GetStatsContextUseCase.execute`가 캐시 hit/miss를 함께 돌려준다.
- 운영 설정에 킬 스위치 `STATS_SERVER_TIMING_ENABLED`를 둔다. 환경변수로 켜고 기본값은 꺼짐이다.
- 배포 후 운영 브라우저 측정으로 캐시 미스를 서버 쪽에서 확인하고 B-6을 분해한다.

제외:

- 통계 외 다른 화면, 미들웨어, `apps/core` 공용 헬퍼.
- 측정값을 서버에 로그나 지표로 저장하는 일.
- 명시적 `Cache-Control` 부여(백로그 A-7), 폰트 경량화(C-6), 성능 최적화.
- 데스크톱 빌드에서 켜는 일.

이전 설계문서는 "운영 미들웨어를 두지 않는다"고 결정했다(`docs/plans/2026-09-29-stats-performance-measurement-design.md` Decision). 이 계획은 그 결정을 좁게 대체한다. 미들웨어가 아니라 통계 뷰 한 곳에만 두고, 운영 설정으로 켜고 끈다.

## 헤더 형식

```
Server-Timing: cache;desc="miss", ctx;dur=2650.1, db;dur=812.4, db-count;desc="21 queries"
```

- `cache`: `desc="hit"` 또는 `desc="miss"`. 시간 값은 없다.
- `ctx`: 통계 데이터 생성, 즉 유스케이스 호출에 걸린 전체 시간(ms, 소수 1자리). 검토자들이 합의한 세 지표에 계획 작성 중 추가했다. `ctx`에서 `db`를 빼야 파이썬 계산 몫이 나오고, 그래야 B-6을 분해할 수 있다.
- `db`: 유스케이스 호출 동안 `cursor.execute()` 안에서 쓴 시간의 합(ms, 소수 1자리). PostgreSQL 클라이언트 커서에서는 DB 왕복과 전송까지 포함한다. 뜻은 설계문서의 DB별 설명을 따른다.
- `db-count`: 같은 구간에서 실행된 쿼리 수.
- 넣지 않는 것: SQL 문, 바인드 값, 캐시 키, 사용자 ID·이름·이메일, 조회 날짜, 기록 내용, 예외 메시지.
- `Timing-Allow-Origin`은 붙이지 않는다.

## 인수 기준

1. 스위치가 켜져 있으면, 로그인한 사용자의 `/stats/` 200 응답에 위 형식의 헤더가 붙는다. 첫 조회는 `miss`, 같은 조건의 재조회는 `hit`이다.
2. 스위치가 꺼져 있거나 없으면 헤더가 없다. 개발 설정과 데스크톱 설정은 항상 꺼져 있다.
3. 익명 요청(302 리다이렉트)과 200이 아닌 응답에는 헤더가 없다.
4. 헤더 값에 사용자·조회·쿼리 내용이 들어가지 않는다.
5. 측정 코드가 실패해도 페이지는 200으로 정상 렌더되고 헤더만 빠진다.
6. 통계 데이터 생성 중 실제 오류(DB 오류 등)는 측정 코드가 삼키지 않고 그대로 전파된다.
7. 운영 설정은 환경변수 `STATS_SERVER_TIMING_ENABLED`가 `true`일 때만 켜진다.
8. `connection.queries`나 `force_debug_cursor`를 쓰지 않는다. 측정 코드가 `apps/stats/conftest.py`를 import하지 않는다.
9. 배포 후 운영 브라우저에서 헤더가 Cloudflare의 `cfExtPri`와 함께 `serverTiming`에 나타나는 것을 확인한다. 처음 연 날짜 5개와 재조회 5개의 hit/miss와 시간을 기록한다.

## Activated Roles

- Backend TDD Coach: Test List와 Red/Green 판정.
- Backend & Integration Engineer: 구현과 증거 기록.
- Quality Verification Lead: 회귀 위험과 최종 증거 평가.
- Domain Architecture Reviewer: hit/miss를 어디서 알고 헤더를 어디서 붙일지 결정(2026-09-30 검토 완료).
- Security & Resilience Reviewer: 노출 범위와 실패 안전성 요구(2026-09-30 검토 완료).
- Deployment & Operations Reviewer: 스위치, 데스크톱 제외, 배포와 롤백 절차(2026-09-30 검토 완료).

## Not Activated

- Product Scope Owner: 사용자가 기능과 범위를 직접 결정했다.
- Web Experience Designer, Browser Interaction Reviewer, Frontend Implementation Engineer: 템플릿, CSS, 브라우저 JS를 바꾸지 않는다.
- AI Automation Architect: 해당 없음.

## Domain Boundary and Dependency Direction

- 캐시 정책(키, TTL, hit/miss 판단)은 지금처럼 `apps/stats/use_cases.py`가 소유한다. 유스케이스는 이미 알고 있는 hit/miss 사실을 결과에 담아 돌려줄 뿐이다. 조회를 한 번 더 하지 않는다.
- HTTP 헤더 형식과 DB 측정은 `apps/stats/views.py:index`가 맡는다. 유스케이스는 `HttpResponse`나 헤더를 모른다.
- 의존 방향은 `views -> use_cases` 그대로다. 앱 사이의 새 의존은 없다. 뷰는 Django의 `settings`와 `connection`만 새로 쓴다.
- 뷰는 `_cache_key`를 다시 계산하지 않는다. `apps/stats/conftest.py`도 import하지 않는다.

## Coupling and Cohesion Review

1. 결합도는 늘지 않는다. 뷰는 기존의 유스케이스 의존 하나만 유지하고, 결과 타입은 표준 라이브러리 데이터클래스다. `apps/core`와의 새 연결을 만들지 않으려고 공용 헬퍼 안(C안)은 기각했다.
2. 응집도는 유지되거나 나아진다. 캐시 hit/miss 사실이 소유자인 유스케이스에서 나오고, 뷰는 HTTP 표현만 맡는다.

측정 래퍼는 테스트 픽스처(`apps/stats/conftest.py`)와 비슷하지만 공유하지 않는다. 운영용은 10줄 남짓이고 목적과 수명이 다르다. 호출처가 하나뿐인데 추상화를 만드는 것은 Over-Engineering 규칙에 어긋난다.

## Pythonic Code Design

- `StatsContextResult(context: dict, cache_hit: bool)`: 불변 데이터클래스로 `apps/stats/use_cases.py`에 둔다.
- 뷰:
  - 유스케이스 호출만 `connection.execute_wrapper` 컨텍스트로 감싸 쿼리 수와 execute 시간을 모은다.
  - 호출 전후 `perf_counter_ns()`로 `ctx` 시간을 잰다.
  - `getattr(settings, "STATS_SERVER_TIMING_ENABLED", False)`가 거짓이면 측정하지 않는다.
- 실패 안전성:
  - 측정 준비(래퍼 진입)가 실패하면 측정 없이 유스케이스를 호출한다.
  - 헤더 조립이 실패하면 헤더를 생략한다.
  - 유스케이스 자체가 던지는 예외는 잡지 않는다.
- 운영 설정: `STATS_SERVER_TIMING_ENABLED = os.getenv("STATS_SERVER_TIMING_ENABLED", "").lower() == "true"`. `lifeDiary/settings/prod.py`에만 둔다.

## Test List and TDD checkpoints

새 파일 `apps/stats/test_server_timing.py`에 둔다. 설정 계약 테스트는 `lifeDiary/test_prod_settings.py` 방식을 따른다. 캐시와 스위치는 각 테스트 본문에서 보이게 설정한다. 루트 conftest가 모든 테스트를 DummyCache(항상 미스)로 돌리므로, hit/miss를 구분하는 테스트는 본문에서 `LocMemCache`로 바꾼다. 새 자동 적용 픽스처는 만들지 않는다.

기존 테스트 영향: 유스케이스를 부르는 테스트는 없다. 호출처는 `apps/stats/views.py:25` 하나뿐이다. 뷰를 통해 HTML을 확인하는 `apps/stats/tests.py`의 테스트는 뷰가 `.context`를 쓰도록 바뀌면 그대로 통과한다.

Backend TDD Coach가 정한 순서는 ST-01 → ST-08 → ST-09 → ST-10 → ST-02 → ST-03 → ST-04 → ST-05 → ST-06 → ST-07 → ST-11이다. ST-02는 그 시나리오가 요구하는 만큼만 구현한다. 그래야 뒤의 시나리오가 제 몫의 Red를 낼 수 있다. 첫 실행부터 Green인 시나리오는 돌연변이 검사로 증거를 대신한다. 결함을 일부러 넣어 그 테스트만 실패하는지 확인하고 되돌린다.

| ID | 동작 | Given | When | Then | 경계 | 테스트 | 예상 Red | 상태 |
|---|---|---|---|---|---|---|---|---|
| ST-01 | 유스케이스가 자기 답이 캐시에서 왔는지 알려 준다 | LocMemCache, 캐시 비움, 기록이 조금 있는 사용자 | 같은 인자로 `execute` 두 번 | 첫 번째 `cache_hit` False, 두 번째 True, `context` 동일 | domain | `test_second_stats_context_lookup_is_a_cache_hit` | `AttributeError: 'dict' object has no attribute 'cache_hit'` | Green |
| ST-08 | 운영 스위치는 기본 꺼짐이고 환경변수로만 켜진다 | 운영 설정 재로드. 환경변수 없음 / `true` | 설정 import | 각각 False / True | contract | `test_prod_settings_server_timing_flag_follows_env_var[default_off, explicitly_on]` | 속성 없음으로 실패 | Green |
| ST-09 | 개발 설정은 헤더를 켜지 않는다 | pytest의 dev 설정 | 설정 읽기 | False | contract | `test_dev_settings_leave_server_timing_disabled` | Red 없음(회귀 방지용) | Green |
| ST-10 | 데스크톱 설정은 헤더를 켜지 않는다 | desktop 설정 재로드 | 설정 import | False | contract | `test_desktop_settings_leave_server_timing_disabled` | Red 없음(회귀 방지용) | Green |
| ST-02 | 켜진 통계 페이지가 자기 비용을 표준 헤더로 알린다 | 로그인, 첫 조회(미스), 스위치 켬 | `GET /stats/?date=...` | 헤더가 `cache;desc="miss"`, `ctx;dur=`, `db;dur=`, `db-count;desc="<n> queries"` 형식. 수치 값은 단언하지 않음 | web | `test_stats_response_reports_server_timing_when_enabled` | 헤더 없음 | Green |
| ST-03 | 같은 페이지 재조회는 hit으로 알린다 | ST-02와 같음, LocMemCache | 같은 요청 두 번째 | `cache;desc="hit"` | web | `test_stats_response_server_timing_reports_cache_hit_on_repeat_view` | ST-02 구현에 따라 Red 또는 돌연변이 검사 | Green |
| ST-04 | 스위치를 끄면 헤더가 사라진다 | 로그인, 스위치 끔 | 같은 요청 | 헤더 없음 | web | `test_stats_response_omits_server_timing_when_disabled` | ST-02 구현에 따라 Red 또는 돌연변이 검사 | Green |
| ST-05 | 익명 리다이렉트에는 헤더가 없다 | 익명, 스위치 켬 | 같은 요청 | 302, 헤더 없음 | web | `test_anonymous_stats_redirect_omits_server_timing` | 돌연변이 검사 예상 | Green |
| ST-06 | 헤더에 사용자·조회·쿼리 내용이 없다 | 눈에 띄는 사용자명·이메일, 특정 날짜, 스위치 켬 | 같은 요청 | 헤더에 사용자 ID·이름·이메일, 날짜, `SELECT`/`FROM`, `stats:` 없음 | contract | `test_server_timing_header_excludes_user_and_query_content` | Red 없음(개인정보 누출 방지 계약) | Green |
| ST-07 | 측정 코드가 깨져도 페이지는 정상 렌더된다 | 스위치 켬, `connection.execute_wrapper`가 예외를 던지도록 주입 | 같은 요청 | 200, 페이지 정상, 헤더 없음 | web | `test_stats_page_still_renders_when_server_timing_measurement_fails` | 주입한 예외가 전파됨 | Green |
| ST-11 | 통계 데이터 생성의 실제 오류는 숨기지 않는다 | 스위치 켬, 유스케이스가 부르는 `get_stats_context`(`apps.stats.use_cases`에서 참조하는 이름)가 예외를 던지도록 주입 | 같은 요청 | 주입한 예외가 전파됨 | web | `test_stats_page_propagates_real_database_errors` | ST-07 구현이 맞으면 처음부터 Green, 기록 | Green |

실패 주입은 Django 공개 API(`connection.execute_wrapper`)와 이미 공개된 함수(`get_stats_context`)에서만 한다. 뷰 내부 구조나 비공개 이름은 고정하지 않는다(Result-Oriented Verification의 실패 주입 허용 범위).

구현 중 결정 (2026-09-30):

- ST-05: 명시적 `response.status_code == 200` 확인을 두지 않았다. 헤더는 뷰 끝의 `render()` 응답에만 붙고, `@login_required`가 익명 302를 뷰 본문 전에 돌려주기 때문이다.
  - Backend TDD Coach는 "명시적 확인 추가" 또는 "Security & Resilience Reviewer의 구조적 보장 승인" 중 하나를 요구했다.
  - Security & Resilience Reviewer가 구조적 보장을 승인했다(기준 1·2 충족, 비차단 권고로 명시적 확인 제안).
  - 명시적 확인은 가상의 향후 분기에 대비한 코드이므로 Over-Engineering 규칙에 따라 넣지 않고 Deferred에 둔다.
- ST-06: 사용자 ID 부분 문자열 검사를 뺐다. 짧은 ID(`3` 등)가 시간 값 안에 우연히 나타나 테스트가 흔들릴 수 있다. 헤더 전체가 허용된 네 지표 형식과 정확히 일치하는지로 검사한다. Coach는 이것이 더 강한 보장이라며 승인했다.
- ST-08: 새 파일 대신 기존 `lifeDiary/test_prod_settings.py`에 두었다. Coach 승인.
- ST-11: 주입 지점을 `apps.stats.use_cases.get_stats_context`로 했다. 유스케이스가 `from .logic import get_stats_context`로 이름을 가져와 쓰므로, `apps.stats.logic` 쪽 이름을 바꾸면 유스케이스에 닿지 않는다.
- 헤더 조립 실패 보호는 넣지 않았다. 위 "실패 안전성"에는 "헤더 조립이 실패하면 헤더를 생략한다"고 적었지만, 조립은 정수와 불리언을 문자열로 만드는 일이라 실패 경로가 없다. 이를 요구하는 시나리오도 Test List에 없다.

## 파일과 단계

1. `apps/stats/test_server_timing.py`(신규), `apps/stats/use_cases.py`, `apps/stats/views.py`: Test List 순서대로 한 시나리오씩 진행한다. 각 단계는 Red(또는 돌연변이 Red), Green, 회귀 범위(`apps/stats/`)를 거친다.
2. `lifeDiary/settings/prod.py`, `lifeDiary/test_prod_settings.py`: ST-08.
3. `apps/stats/test_server_timing.py`: ST-09와 ST-10(회귀 방지 계약).
4. 전체 회귀, Django 점검, 운영 배포 점검.
5. 작업 로그와 `docs/project-status.md` 갱신, PR.
6. 배포와 운영 측정(아래 절차).

## 배포와 운영 측정

1. PR 머지. 머지는 사용자가 한다.
2. `deploy.yml`을 `dry_run: true`로 실행해 바뀌는 파일 목록을 검토한다. 이어 `dry_run: false`로 실제 배포한다. 배포 실행은 사용자가 하거나 명시적으로 승인한다.
3. 스위치가 꺼진 채로 `/stats/`가 정상 동작하는지, 헤더가 없는지 확인한다.
4. 사용자가 Render 대시보드에서 `STATS_SERVER_TIMING_ENABLED=true`를 설정한다(재시작 동반).
5. 운영 브라우저에서 확인한다.
   - `serverTiming`에 `cache`, `ctx`, `db`, `db-count`가 `cfExtPri`와 함께 나타나는지.
   - 오늘 처음 여는 날짜 5개가 `miss`, 같은 날짜 재조회 5개가 `hit`인지.
   - 각 로드의 TTFB, `ctx`, `db`, `db-count`를 기록한다.
6. 측정이 끝나면 스위치를 켜 둘지 끌지 사용자가 정한다. 켜 둔다면 보존 검토를 한다(Deferred).
7. 롤백: `deploy.yml`의 `ref`에 직전 정상 SHA를 넣어 다시 배포하거나, 스위치를 끈다.

## 검증 명령과 기대 증거

- 대상: `conda run -n knou-life-diary pytest apps/stats/test_server_timing.py --tb=short`
- 회귀 범위: `conda run -n knou-life-diary pytest apps/stats lifeDiary/test_prod_settings.py --tb=short`
- 전체 회귀: `conda run -n knou-life-diary pytest`
- `conda run -n knou-life-diary python manage.py check`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run`
- `git diff --check`

## Deferred

- 헤더 부착에 명시적 `status_code == 200` 확인 추가. 트리거: 통계 뷰에 두 번째 응답 분기(오류, 빈 상태 조기 반환 등)가 생길 때 (Security & Resilience Reviewer 비차단 권고).
- 스위치를 오래 켜 둘 경우의 보존 검토. 트리거: 측정 이후에도 켜 두기로 할 때. 보안과 운영 검토를 다시 한다.
- DB 측정 래퍼를 `apps/core`로 추출하는 일. 트리거: 두 번째 운영 화면이 같은 헤더를 필요로 할 때.
- 로그인 후 화면의 명시적 `Cache-Control` (백로그 A-7).
- 백로그 A-1과 A-6 문구 재확인. 두 항목은 "통계 캐시 키에 버전이 없다"고 적었지만, 현재 코드의 키에는 `:v2`가 붙어 있다(`apps/stats/use_cases.py:21`). 운영 검토에서 발견했고, 이 트랙 범위 밖이다.
