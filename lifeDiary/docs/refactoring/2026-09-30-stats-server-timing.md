# 통계 페이지 Server-Timing 헤더 실행 로그 (2026-09-30)

- 계획: `docs/plans/2026-09-30-stats-server-timing-plan.md`
- 선행 트랙: `docs/refactoring/2026-09-29-stats-performance-measurement.md`
- 브랜치: `perf/stats-measurement-verification`

## 요약

`GET /stats/` 응답에 `Server-Timing` 헤더를 붙였다. 헤더는 운영 설정 스위치가 켜져 있고 로그인한 사용자의 정상 응답일 때만 붙으며, 다음 네 가지를 알려 준다.

- 캐시 hit/miss
- 통계 데이터 생성 시간(`ctx`)
- DB execute 시간(`db`)
- 쿼리 수(`db-count`)

목적은 두 가지다. 운영 브라우저 측정에서 추정으로 남은 "캐시 미스" 분류를 서버 쪽에서 확인하고, 운영 캐시 미스 약 2.7초의 내역을 나누는 것이다(백로그 B-6).

```
Server-Timing: cache;desc="miss", ctx;dur=2650.1, db;dur=812.4, db-count;desc="21 queries"
```

## 변경 내용

- `apps/stats/use_cases.py`: `GetStatsContextUseCase.execute`가 `StatsContextResult(context, cache_hit)`를 돌려준다. hit/miss는 기존 `cache.get()` 결과에서 나오고, 조회를 한 번 더 하지 않는다.
- `apps/stats/views.py`:
  - `index`가 결과의 `.context`로 렌더한다.
  - 스위치가 켜져 있으면 유스케이스 호출만 `connection.execute_wrapper`로 감싸 쿼리 수와 execute 시간을 모으고, 호출 전체 시간을 잰다.
  - 헤더는 `render()` 응답에만 붙인다.
  - 계측 준비가 실패하면 측정 없이 호출하고 헤더를 생략한다. 유스케이스가 던지는 예외는 잡지 않는다.
- `lifeDiary/settings/prod.py`: `STATS_SERVER_TIMING_ENABLED`는 환경변수 `STATS_SERVER_TIMING_ENABLED`가 `true`일 때만 참이다. dev와 desktop 설정에는 두지 않는다.
- 테스트:
  - `apps/stats/test_server_timing.py`(신규, 10개)
  - `lifeDiary/test_prod_settings.py`(파라미터 케이스 2건 추가)

## 역할과 검토

- 계획 단계:
  - Domain Architecture Reviewer: hit/miss는 유스케이스, 헤더와 측정은 뷰, 미들웨어와 `apps/core` 헬퍼는 기각.
  - Security & Resilience Reviewer: 노출 범위를 분석하고 9개 인수 기준을 제시.
  - Deployment & Operations Reviewer: 운영 전용 스위치, 기본값 꺼짐, 데스크톱 제외, dry run 뒤 실제 배포, 롤백 절차.
  - Backend TDD Coach: Test List ST-01~ST-11.
- 사용자가 계획을 승인했다. `ctx` 지표는 계획 작성 중 추가한 것으로, 승인 받을 때 이 점을 함께 알렸다.
- 구현 후:
  - Backend TDD Coach: 11개 시나리오 모두 Green, 과잉 구현 없음. 헬퍼를 `views.py` 밖으로 옮기는 리팩터링은 합의된 설계에 어긋나 불허했다.
  - Security & Resilience Reviewer: 9개 기준 모두 충족, 차단 결함 없음.
  - Quality Verification Lead: 조건부 준비.
    - 인수 기준 1~8에 증거가 대응된다.
      - 기준 3은 ST-05와 구조적 보장으로 충족한다.
      - 기준 8은 테스트가 아니라 코드를 직접 읽어 확인했다.
    - 기준 9는 의도적으로 검증하지 않았고, 문서에 그렇게 기록했다.
    - 유스케이스 반환 타입 변경의 호출처는 통계 뷰와 신규 테스트뿐이다. 저장소 전체를 검색해 확인했다.
    - 유스케이스 예외 뒤에 래퍼가 빠지는지는 Django 소스(`try/finally`)로만 뒷받침되고, 테스트는 없다.
    - PR 조건은 이번 세션에서 새로 돌린 전체 회귀 결과로 문서를 채우는 것이었다. 아래 "검증"에 그 결과를 적었다.
- 운영 측정 기록 후 Quality Verification Lead가 다시 보았다.
  - 판정은 "커밋 가능"이다. 모든 수치를 원시 값과 대조했고, 추정과 사실이 나뉘어 있다고 보았다.
  - 비차단 권고 두 가지(로컬 대비 배수 표기, 05-08 재조회 이상치 설명)를 반영했다.

## TDD 증거

모든 명령은 `conda run -n knou-life-diary python -m pytest ... -o cache_dir=/tmp/lifediary-pytest-cache`로 실행했다. 시나리오마다 따로 커밋했다.

| 시나리오 | 커밋 | Red 또는 대체 증거 | Green |
|---|---|---|---|
| ST-01 유스케이스가 hit/miss를 알려 줌 | `e29f073` | `AttributeError: 'dict' object has no attribute 'cache_hit'` | 1 passed. 통계 뷰·유스케이스 범위 26 passed |
| ST-08 운영 스위치 | `5a79bb1` | 두 케이스 모두 `AttributeError: module 'lifeDiary.settings.prod' has no attribute 'STATS_SERVER_TIMING_ENABLED'` | 2 passed. 운영 설정 계약 9 passed |
| ST-09 개발 설정은 꺼짐 | `199112f` | Red 없음(회귀 방지). 돌연변이 검사: dev.py에 스위치 `True` 추가 시 `assert True is False`. 되돌림(diff 0줄) | 통과 |
| ST-10 데스크톱 설정은 꺼짐 | `511fc32` | Red 없음. 돌연변이 검사: desktop.py에 스위치 `True` 추가 시 실패. 되돌림 | 통과 |
| ST-02 헤더 추가 | `3592ed5` | `assert 'Server-Timing' in <HttpResponse status_code=200 ...>` | 최소 구현(헤더 항상 부착, cache는 `miss` 고정). 범위 20 passed |
| ST-03 재조회는 hit | `dfcca59` | `AssertionError: assert 'miss' == 'hit'` | 실제 `cache_hit` 사용. 파일 5 passed |
| ST-04 스위치 끄면 헤더 없음 | `70f35b1` | `assert 'Server-Timing' not in <HttpResponse status_code=200 ...>` | 스위치 확인 추가. 범위 22 passed |
| ST-05 익명 302에는 헤더 없음 | `509a341` | 처음부터 Green. 돌연변이 검사: `login_required` 바깥에서 모든 응답에 헤더를 붙이는 래퍼를 넣으면 302에서 실패. 되돌림 | 통과 |
| ST-06 사용자·조회·쿼리 내용 없음 | `bf2caf2` | 처음부터 Green. 돌연변이 검사: 헤더에 `user;desc="<사용자명>"`을 덧붙이면 전체 형식 검사에서 실패. 되돌림 | 통과 |
| ST-07 계측 실패에도 화면 렌더 | `88fa09a` | 주입한 `RuntimeError: query instrumentation unavailable`이 뷰 밖으로 전파됨 | 계측 준비만 보호. 범위 25 passed |
| ST-11 실제 오류는 숨기지 않음 | `226be13` | 처음부터 Green. 돌연변이 검사: 뷰에서 예외를 넓게 잡아 빈 200을 돌려주면 `Failed: DID NOT RAISE`. 되돌림 | 통과 |

ST-02는 계획대로 그 시나리오가 요구하는 만큼만 구현했다. 그래서 ST-03과 ST-04가 각자 Red를 냈다.

처음부터 Green인 시나리오(ST-05, ST-06, ST-09, ST-10, ST-11)는 돌연변이 검사로 증거를 대신했다. 결함을 일부러 넣으면 해당 테스트만 실패하는지 확인했고, 넣은 결함은 모두 되돌렸으며 커밋하지 않았다.

ST-10은 데스크톱 설정을 import할 때 홈 아래에 데이터 폴더와 `secret_key`가 생기는 부작용을 막으려고 `HOME`과 `APPDATA`를 임시 폴더로 바꾼다. 실제 `~/Library/Application Support/LifeDiary` 폴더 목록은 실행 전후가 같았다.

## 구현 중 결정

- ST-05: 명시적 `status_code == 200` 확인을 넣지 않았다. 헤더는 뷰 끝의 `render()` 응답에만 붙고, `@login_required`가 익명 302를 먼저 돌려주기 때문이다. Security & Resilience Reviewer가 이 구조적 보장을 승인했다. 명시적 확인은 비차단 권고로 남았고, 뷰에 두 번째 응답 분기가 생길 때 넣는다(Deferred).
- ST-06: 사용자 ID 부분 문자열 검사를 헤더 전체 형식 일치 검사로 바꿨다. 짧은 ID가 시간 값에 우연히 나타나 테스트가 흔들리는 것을 막기 위해서다. Coach는 더 강한 보장이라고 판정했다.
- 로깅: 계측 실패 시 로그를 남기지 않는다. Deployment & Operations Reviewer가 이 기능에 새 로깅을 넣지 말라고 했다.
- ST-11: 예외는 `apps.stats.use_cases.get_stats_context`에 주입했다. 유스케이스가 이 이름을 `from .logic import`로 가져와 쓰기 때문에, `apps.stats.logic` 쪽에 주입하면 유스케이스에 닿지 않는다. 계획 Test List의 Given도 이에 맞게 고쳤다.
- 헤더 조립 실패 보호는 넣지 않았다. 계획의 "실패 안전성"에는 적혀 있었지만, 조립은 정수와 불리언을 문자열로 만드는 일이라 실패 경로가 없다. 이를 요구하는 시나리오도 없다. 계획에 이 차이를 기록했다.

## 동시성

gunicorn은 gthread(워커 2개, 스레드 4개)로 돈다. 계측이 다른 요청의 쿼리를 세지 않는지는 Django 소스로 확인했다. 테스트로 확인하지는 않았다.

- `django.db.connection`은 `connections[DEFAULT_DB_ALIAS]`를 가리키는 프록시다(`django/db/__init__.py:43`).
- `ConnectionHandler.thread_critical = True`(`django/db/utils.py:145`)여서 연결 객체는 스레드마다 따로 있다.
- `execute_wrapper`는 그 연결 객체의 `execute_wrappers` 목록에 넣고 빼므로(`django/db/backends/base/base.py:772-781`), 래퍼도 요청을 처리하는 스레드 안에만 걸린다.

## 검증

HEAD `226be13`(코드 기준. 이후 커밋은 문서만 바꾼다)에서 다시 실행했다.

- 전체 회귀 `python -m pytest -q`: 617 passed, 0 failed, exit 0.
  - 진행 표시 617개가 모두 `.`이었다. `conda run`이 마지막 요약 줄을 잘라서 소요 시간은 남지 않았다.
  - 경고는 221건이고 모두 WhiteNoise의 `No directory at: .../staticfiles/`다. 로컬에서 `collectstatic`을 하지 않아서 생긴다.
- `python manage.py check`: `System check identified no issues (0 silenced).`
- `python manage.py makemigrations --check --dry-run`: `No changes detected`
- `python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`: exit 0. 경고는 기존 W009 1건이다(로컬에 운영 `SECRET_KEY`가 없음).
- `git diff --check`: exit 0

## 배포

계획과 PR #76 본문은 "`deploy.yml` dry run 뒤 실제 배포"를 적었지만, 실제 배포는 이 저장소가 써 온 배포 PR로 했다.

- 사용자가 PR #76을 머지했다(2026-09-30 21:18 KST).
- 이어 `deploy-pr.yml`이 main→production 배포 PR #75를 갱신했고, 사용자가 21:21 KST에 머지했다. 이 머지로 PR #74와 #76이 함께 production에 올라갔다. #75는 #74 머지 때 열린 뒤 그때까지 열려 있었다.
- production 브랜치 머리는 `55ef6dc`이고, 그 트리가 main 트리와 같음을 확인했다.
- `deploy.yml`은 실행 이력이 없다. production 트리에는 배포 PR 머지로 들어온 docs가 있어서 지금 돌리면 docs 삭제만 변경으로 잡힌다. 그래서 dry run을 하지 않았다.
- 스위치를 켜기 전(22:40 KST)에는 로그인하지 않은 `/stats/`가 302를 돌려주고 `Server-Timing` 헤더가 없었다.
- 로그인한 상태에서 스위치가 꺼진 화면은 확인하지 않았다. 사용자가 바로 스위치를 켰다.
- 사용자가 Render에서 `STATS_SERVER_TIMING_ENABLED=true`를 설정하고 재시작했다.
- 롤백: 스위치를 끄거나, 직전 정상 커밋으로 배포 PR을 다시 만든다.

## 운영 측정 (2026-09-30 22시대 KST)

데스크톱 Chrome에서 사용자가 직접 로그인한 뒤 쟀다. 네트워크와 CPU 에뮬레이션은 설정하지 않았다. 각 로드에서 읽은 값은 `performance.getEntriesByType("navigation")[0]`의 `responseStatus`, `responseStart - requestStart`(TTFB), `serverTiming`, 그리고 현재 URL뿐이다. 페이지 내용과 쿠키는 읽지 않았다.

날짜는 임의로 고른 과거 날짜 2026-05-04~05-08이다. 먼저 날짜마다 한 번씩 열고, 이어 같은 순서로 한 번 더 열었다. 모든 응답은 200이었다.

`serverTiming`에는 매번 `cache`, `ctx`, `db`, `db-count`와 Cloudflare의 `cfExtPri`가 함께 나왔다. 원 서버 헤더가 Cloudflare를 지나도 남는다(인수 기준 9).

| 날짜 | 첫 조회 cache | TTFB | ctx | db | 쿼리 | 재조회 cache | TTFB | ctx | db | 쿼리 |
|---|---|---|---|---|---|---|---|---|---|---|
| 05-04 | miss | 3,312 | 2,820.5 | 2,467.1 | 29 | hit | 451 | 1.1 | 0.0 | 0 |
| 05-05 | miss | 3,294 | 2,738.8 | 2,361.8 | 29 | hit | 468 | 0.5 | 0.0 | 0 |
| 05-06 | miss | 3,402 | 2,932.2 | 2,398.3 | 29 | hit | 440 | 0.4 | 0.0 | 0 |
| 05-07 | miss | 3,204 | 2,730.6 | 2,360.4 | 29 | hit | 465 | 0.4 | 0.0 | 0 |
| 05-08 | miss | 3,206 | 2,702.9 | 2,363.0 | 29 | hit | 904 | 0.4 | 0.0 | 0 |

단위는 ms이고, `ctx`, `db`, 쿼리 수는 유스케이스 호출 구간만 센다.

### B-6 분해

캐시 미스 TTFB 중앙값은 3,294ms(3,204~3,402)다. 중앙값 기준으로 나누면 다음과 같다.

| 몫 | 계산 | 중앙값 | TTFB 대비 |
|---|---|---|---|
| DB execute | `db` | 2,363ms | 약 72% |
| 유스케이스 안 파이썬 계산 | `ctx - db` | 370ms | 약 11% |
| 유스케이스 밖 | `TTFB - ctx` | 492ms | 약 15% |

- 유스케이스 밖 몫에는 네트워크, 미들웨어, 세션·인증 조회, 내보내기 달 목록 조회, 템플릿 렌더가 들어간다.
- 차이 값마다 따로 중앙값을 냈기 때문에 세 몫을 더해도 TTFB 중앙값과 정확히 같지는 않다.

사실:

- 캐시 미스 비용의 대부분은 DB execute 시간이다.
- 쿼리는 매번 29개였고, 쿼리당 execute 시간은 81.4~85.1ms로 고르다.
- 캐시 hit에서는 유스케이스가 쿼리를 하나도 실행하지 않는다(`ctx` 중앙값 0.4ms, 최대 1.1ms). hit TTFB 중앙값 465ms는 거의 다 유스케이스 밖 몫이고, 미스의 유스케이스 밖 몫(492ms)과 비슷하다.
- 05-08 재조회의 TTFB 904ms는 다른 hit(440~468ms)의 약 2배다. 그런데 이 로드의 `ctx`도 0.4ms라 늘어난 시간은 유스케이스 밖에서 생겼다. 원인은 따로 보지 않았고, 중앙값에는 영향이 없다.

로컬 PostgreSQL 14 벤치마크(측정 트랙 기록)와 비교하면 다음과 같다. 두 환경은 기계, 버전, 풀러, 데이터가 달라 참고용이다.

| 항목 | 로컬 PostgreSQL cold | 운영 miss |
|---|---|---|
| SQL execute | 약 49ms(21개, 쿼리당 약 2.3ms) | 2,363ms(29개, 쿼리당 81~85ms, 약 35~36배) |
| execute 밖 | 약 800ms(요청 전체 849ms에서 execute를 뺀 값) | 약 860ms(파이썬 370ms + 유스케이스 밖 492ms, 운영은 네트워크 포함) |

execute 밖 시간은 두 환경이 비슷하다. 로컬과 운영의 차이는 거의 다 DB execute에서 난다.

추정(따로 재지 않음):

- 쿼리 내용과 관계없이 쿼리마다 비슷한 시간이 든다. 로컬 DB에서는 같은 일이 쿼리당 몇 ms였다. 이 두 가지는 Render와 Supabase 풀러 사이의 왕복 지연이 쿼리 실행 시간보다 크다는 가설과 맞는다.
- 왕복 지연 자체와 두 서비스의 리전은 확인하지 않았다.

측정 트랙의 로컬 테스트 데이터는 쿼리 21개였지만, 이 계정은 29개였다. 어떤 조회가 늘었는지는 확인하지 않았다. 목표 개수에 비례하는 조회를 다루는 B-3과 관련될 수 있다. 측정 트랙의 운영 미스 TTFB 중앙값 2,817ms와 이번 3,294ms의 차이는 날짜와 시간대가 달라 원인을 따로 보지 않았다.

## 미검증 항목

- 멀티스레드에서 계측이 섞이지 않는다는 점은 위 "동시성"의 소스 확인뿐이고, 테스트는 없다. 운영 측정은 요청을 하나씩 보냈다.
- 로그인한 상태에서 스위치가 꺼진 화면은 확인하지 않았다. 해당 동작은 ST-04가 테스트로 보장한다.
- 왕복 지연 가설(위 "추정")은 따로 재지 않았다.
- 스위치를 켜 둘지는 사용자가 아직 정하지 않았다. 켜 둔다면 백로그 A-8의 보존 검토를 한다.

## Deferred

- 백로그 B-8: 헤더 부착에 명시적 `status_code == 200` 확인 추가. 트리거: 통계 뷰에 두 번째 응답 분기가 생길 때.
- 백로그 A-8: 스위치를 오래 켜 둘 경우의 보존 검토. 트리거: 측정 뒤에도 켜 두기로 할 때. 보안과 운영 검토를 다시 한다.
- 백로그 B-9: DB 측정 래퍼를 `apps/core`로 추출. 트리거: 두 번째 운영 화면이 같은 헤더를 필요로 할 때.
- 백로그 A-8에 함께 적음: A-1과 A-6 문구 재확인. 두 항목은 "통계 캐시 키에 버전이 없다"고 적었지만 현재 키에는 `:v2`가 있다(`apps/stats/use_cases.py:21`).
- 백로그 A-7(명시적 `Cache-Control`)은 그대로 남는다.
