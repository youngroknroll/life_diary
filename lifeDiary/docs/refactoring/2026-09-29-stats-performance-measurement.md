# 통계 전체 요청 성능 측정 실행 로그 (2026-09-29 ~ 09-30)

- 계획: `docs/plans/2026-09-29-stats-performance-measurement-plan.md`
- 설계: `docs/plans/2026-09-29-stats-performance-measurement-design.md`
- 브랜치: `perf/lifediary-measurement`

## 요약

`/stats/` 한 번의 요청을 통째로 재는 테스트 전용 측정 도구를 만들었다.
요청 하나를 다음 항목으로 쪼개서 보고한다.

- 전체 시간
- 렌더 전 구간과 렌더 구간
- 쿼리 수와 SQL execute 시간
- 응답 크기
- DB 종류와 캐시 백엔드

벤치마크 테스트는 워밍업 1회를 따로 라벨링하고, 캐시 미스(cold) 5회와 캐시 히트(warm) 5회를 분포로 보고한다. 운영 요청 경로는 바꾸지 않았다.

## 변경 내용

- `apps/stats/conftest.py` (신규)
  - `RequestSample` 데이터클래스와 `measure_request`, `summarize_samples` 픽스처를 둔다.
  - `connection.execute_wrapper()`로 쿼리 수와 execute 시간을 잰다.
  - `template_rendered` 테스트 신호로 렌더 경계를 찾는다.
- `apps/stats/test_stats_perf.py`
  - 기존 테스트 4개 아래에 시나리오 테스트 7개(파라미터 케이스 포함 8건)를 추가했다.
- 처음 구현은 `apps/stats/request_performance.py`에 두었다. 재검토에서 운영 배포 트리에 실리는 위치라는 결함이 나와 conftest로 옮기고 삭제했다(R1).

## TDD 증거

모든 명령은 `conda run -n knou-life-diary python -m pytest ... -o cache_dir=/tmp/lifediary-pytest-cache` 로 실행했다. 회귀 범위는 `apps/stats/test_stats_perf.py` 전체다. Backend TDD Coach가 각 단계의 순서, Red 사유, Green을 판정했고 TDD 웨이버는 요청하지 않았다.

| 시나리오 | 테스트 | Red (예상 사유 그대로) | Green |
|---|---|---|---|
| PERF-03 | `test_measurement_retains_redirect_response` | `ModuleNotFoundError: No module named 'apps.stats.request_performance'` (기존 4개는 그대로 통과) | 5 passed |
| PERF-01 | `test_full_stats_request_reports_measured_cost` | `AttributeError: 'RequestSample' object has no attribute 'sql_execute_ms'` | 6 passed |
| PERF-02 | `test_stats_request_benchmark_reports_cold_and_warm_samples` | `ImportError: cannot import name 'summarize_samples'` (나머지 6개 통과) | 7 passed |
| PERF-04 | `test_report_keeps_failed_requests_without_render_timing` | `TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'` | 8 passed |
| R1 (리팩터링) | 헬퍼를 conftest 픽스처로 이동 | 해당 없음 | 이동 전후 8 passed, `request_performance` 참조 코드 0건 |
| PERF-06 | `test_report_without_samples_is_rejected[no_groups, empty_group]` | 두 케이스 모두 `StopIteration` | 10 passed |
| PERF-05 | `test_stats_page_finishes_data_access_before_rendering` | `AttributeError: ... 'queries_before_render'` | 11 passed |
| PERF-01 수정 (a) | SQL execute 시간 > 0, DummyCache 전제 명시 | 돌연변이 Red 1: SQL 래퍼가 0ns를 기록하게 바꾸면 `assert 0.0 > 0`(172행)에서만 실패. 되돌린 뒤 통과 | 11 passed |
| PERF-02 수정 | 실측 캐시 백엔드, `DEBUG = False`, `finally` 정리 | `TypeError: _summarize_samples() missing 1 required keyword-only argument: 'cache_backend'` | 11 passed |
| PERF-01 수정 (b) | `before_render_ms > render_ms` | 돌연변이 Red 2: 두 구간 계산을 맞바꾸면 `assert 31.49 > 511.16`(176행)에서만 실패. 되돌린 뒤 통과 | 11 passed |
| PERF-08 | `test_stats_page_render_boundary_starts_at_page_template` | `AttributeError: ... 'first_rendered_template'` | 12 passed |

import를 모듈 상단으로 옮긴 리팩터링 2건은 Coach 허용 범위 안에서 했고, 각각 5개와 7개가 통과했다.

PERF-01 수정분은 이미 있던 기능에 단언을 더한 것이라 정상적인 Red가 나올 수 없다. 그래서 Coach가 돌연변이 Red를 대신 인정했다. 두 돌연변이 모두 커밋하지 않았고, 되돌린 뒤 conftest diff가 0줄인 것을 확인했다.

## 돌연변이 검사로 찾은 공백

PERF-05가 Green이 된 뒤 PERF-01과 PERF-05에 결함을 일부러 넣어 보았다.

| 넣은 결함 | PERF-05 직후 | 최종 |
|---|---|---|
| 첫 렌더 시점의 쿼리 수를 항상 0으로 기록 | PERF-05 실패 (`assert 0 == 21`) | PERF-05 실패 |
| 마지막 렌더 신호에서 구간을 나눔 | 두 테스트 모두 통과 (못 잡음) | PERF-08 실패 (`'shared/_date_selector.html' == 'stats/index.html'`) |
| 렌더 전/후 구간 계산을 맞바꿈 | 두 테스트 모두 통과 (못 잡음) | PERF-01 실패 (176행) |

Coach는 처음에 PERF-05가 뒤의 두 결함도 잡는다고 판정했다가, 이 결과를 보고 철회했다. 그 뒤 PERF-01 수정 (b)와 PERF-08을 승인했다.

## 재검토 (2026-09-30)

사용자 요청으로 구현이 끝난 뒤 세 검토자가 따로 다시 보았다.

- Domain Architecture Reviewer: 헬퍼 위치가 결함이라고 판정했다. 저장소에서 테스트 파일도 conftest도 아니면서 `django.test`를 import하는 모듈은 이 파일 하나였고, 운영 배포 트리와 데스크톱 빌드에 함께 실렸다. 계획 40행의 "callable을 받는다"도 코드와 달랐다.
- 측정 의미 검토 (general-purpose): Django 소스와 실행으로 확인했다.
  - 테스트 환경 밖에서는 렌더 구간이 조용히 `None`이 된다.
  - SQL execute 시간은 DB마다 뜻이 반대다.
  - PERF-01 단언은 결함을 잡지 못한다.
  - 빈 입력에서는 `StopIteration`이 새어 나온다.
  - `cache_backend` 단언은 넘긴 상수를 그대로 되받아 비교한다.
  - 캐시 무효화가 실제로 적중하는지는 반사실 실험으로 확인했다. `cache.delete`를 무력화하니 cold도 3쿼리가 되어 테스트가 실패했다.
- Quality Verification Lead: Task 1과 2는 통과로 보았다. 막는 항목은 Task 3(작업 로그, 상태 문서, 브라우저 측정, 벤치마크 재측정)이었다.

사용자 결정은 세 가지였다.

1. 헬퍼를 conftest 픽스처로 옮긴다. 결함 두 건(운영 배포에 실림, 테스트 환경 밖에서 조용히 틀림)이 함께 해결된다.
2. 브라우저 측정을 이번 트랙에서 한다.
3. 권고 4건을 모두 반영한다: PERF-01 강화, 빈 입력 `ValueError`, 캐시 백엔드 실측과 `finally`, `DEBUG = False`.

### 순서가 어긋난 부분

Coach가 정한 순서는 PERF-01 수정 → PERF-08 → PERF-02 수정이었다. PERF-08과 PERF-01 (b)에 대한 판정이 도착했을 때는 PERF-02 수정이 이미 커밋된 뒤였다. 그래서 실제 순서는 PERF-02 수정 → PERF-01 (b) → PERF-08이 되었다. 두 변경은 PERF-02 수정과 겹치는 줄이 없다.

### 검토 의견 중 사실 확인으로 정리한 것

Coach는 `DEBUG = True`에서 SQLite가 매개변수 인용을 위해 보내는 `SELECT QUOTE(?)`가 쿼리 수에 잡힐 수 있다고 보았다. 실제로는 잡히지 않는다.

- `django/db/backends/sqlite3/operations.py:172-174`는 이 쿼리를 Django 래퍼를 거치지 않는 원시 sqlite3 커서로 실행한다.
- 실측 쿼리 수도 `DEBUG = True`(PERF-01)와 `DEBUG = False`(PERF-02) 모두 21이었다.

## 백엔드 벤치마크 (최종 코드 기준)

- 명령: `conda run -n knou-life-diary python -m pytest apps/stats/test_stats_perf.py::test_stats_request_benchmark_reports_cold_and_warm_samples -s -q -o cache_dir=/tmp/lifediary-pytest-cache -p no:warnings`
- 실행: 2026-09-30 00:53 KST, 커밋 `47d8b40`. 다른 테스트가 돌지 않는 상태에서 단독으로 실행했다.
- 조건: in-memory SQLite, `LocMemCache`, `DEBUG = False`, 2,160블록 fixture, `/stats/?date=2026-04-15`

| 라벨 | 샘플 | 쿼리 | 전체 (min / 중앙값 / max, ms) | 렌더 전 중앙값 | 렌더 중앙값 | SQL execute 중앙값 |
|---|---|---|---|---|---|---|
| warmup | 1 | 21 | 435.61 | 402.67 | 32.94 | 8.07 |
| cold | 5 | 21 × 5 | 297.70 / 298.06 / 341.52 | 289.78 | 8.60 | 7.30 |
| warm | 5 | 3 × 5 | 16.16 / 16.60 / 16.98 | 8.35 | 8.19 | 6.55 |

원시 값:

- cold 전체: 341.52, 298.06, 297.85, 297.70, 336.64
- warm 전체: 16.98, 16.16, 16.66, 16.60, 16.32

모든 샘플이 200 응답, 89,232바이트였다. 첫 렌더 템플릿은 `stats/index.html`이었고, 렌더 전에 끝난 쿼리 수는 전체 쿼리 수와 같았다.

## 브라우저 측정 (운영 사이트)

측정 조건:

- 사이트: `https://www.lifediary.kr`, 사용자가 DevTools로 제어되는 Chrome에 직접 로그인한 계정. 자격 증명은 저장소와 로그에 남기지 않았다.
- 시각: 2026-09-30 00:54~00:57 KST
- 브라우저: Chrome 154. UA 축소로 세부 버전은 노출되지 않았다.
- 화면: 1365×900, 배율 1, 데스크톱 에뮬레이션
- 언어: `ko-KR`
- 네트워크: 제한 없음. 브라우저가 보고한 값은 4g, rtt 50ms, HTTP/3.
- 로드 직후 Navigation Timing, `largest-contentful-paint`, `layout-shift` 버퍼 항목을 읽었다.
- 조회만 했고 기록은 바꾸지 않았다. 페이지 본문과 쿠키는 읽지 않았고, LCP 요소는 태그 이름만 남겼다.

그룹 구성:

- 워밍업: `2026-09-25` 첫 방문 1회. 통계 페이지 정적 파일 5개를 받아 오느라 분포에서 뺐다.
- 서버 캐시 미스: 과거 날짜 5개(`09-01`, `09-05`, `09-10`, `09-15`, `09-20`)를 각각 처음 열었다. 브라우저 정적 캐시는 채워진 상태였다.
- 서버 캐시 히트: `09-20`을 주소로 다시 5번 열었다.
- 캐시 무시: `09-20`을 캐시 무시 새로고침으로 5번 열었다. 정적 파일 15개를 모두 네트워크로 받는다.

| 그룹 | TTFB (min / 중앙값 / max, ms) | LCP (min / 중앙값 / max, ms) | load 중앙값 | CLS |
|---|---|---|---|---|
| 워밍업 (1회) | 3,370.5 | 3,736 | 3,770.1 | 0 |
| 서버 캐시 미스 | 2,750.7 / 2,816.7 / 3,081.9 | 2,812 / 2,868 / 3,384 | 2,967.7 | 모두 0 |
| 서버 캐시 히트 | 433.3 / 453.7 / 961.7 | 492 / 520 / 1,028 | 624.7 | 모두 0 |
| 히트 + 브라우저 캐시 무시 | 430.6 / 460.5 / 780.9 | 840 / 996 / 1,156 | 1,120.9 | 모두 0 |

원시 TTFB (ms):

- 미스: 2,769.4, 2,816.7, 3,081.9, 2,848.1, 2,750.7
- 히트: 961.7, 520.6, 453.7, 443.8, 433.3
- 캐시 무시: 457.3, 460.5, 780.9, 481.4, 430.6

TTFB의 거의 전부가 서버 대기 시간(`responseStart - requestStart`)이었다. 문서 전송은 약 10.5KB(압축 전 91KB)였다.

원시 문서 다운로드 시간 (`responseEnd - responseStart`, ms):

- 워밍업: 1.5
- 미스: 1.3, 0.6, 1.4, 1.0, 0.9
- 히트: 27.3, 0.9, 1.1, 1.0, 0.7
- 캐시 무시: 0.9, 0.9, 1.5, 1.4, 1.1

기준 지연: DB를 쓰지 않는 `/robots.txt`를 fetch로 5번 요청하니 TTFB가 121.7~129.7ms(중앙값 122.9)였다.

## 해석

- 처음 연 날짜와 다시 연 날짜를 비교하면 TTFB는 약 2.8초 대 약 0.45초, LCP는 약 2.9초 대 약 0.5초였다. 이 차이가 24시간 통계 캐시의 효과라고 본다. 다만 "처음 연 날짜는 서버 캐시 미스"라는 분류 자체가 이 TTFB 차이로 추정한 것이다. 서버 로그나 캐시 키로 확인하지 않았다(미검증 항목 참고). 외부에 인용할 때는 이 단서를 함께 적는다.
- 느린 쪽에서도 사용자가 기다리는 시간은 대부분 서버 대기 시간이었다.
- 계획에 적혀 있던 "3.83초 첫 로드"는 원본 기록이 없어 증거로 쓰지 않는다. 이번에 새로 잰 첫 방문(워밍업)은 TTFB 3.37초, LCP 3.74초였다. 규모는 비슷하지만 같은 조건이라는 근거는 없다.
- 로컬 벤치마크의 cold는 약 0.3초인데 운영의 캐시 미스는 약 2.7초다(TTFB에서 기준 지연을 뺀 값). 이 차이는 이번 측정으로 설명하지 못한다. 후보는 세 가지다.
  - Render에서 Supabase 트랜잭션 풀러까지 쿼리 21회의 왕복
  - 운영 계정의 데이터 양
  - 인스턴스 CPU

  서버 쪽 계측이 없으므로 가설로만 남긴다.
- 캐시 히트도 기준 지연보다 약 330ms 길다. 쿼리 3회(세션, 사용자, 내보내기 가능한 달)와 파일 캐시 읽기, 렌더가 후보다. 역시 가설이다.
- 서버 캐시 히트 1회차(961.7ms)와 캐시 무시 3회차(780.9ms)가 튀는 원인은 확인하지 못했다.
- 16개 측정 로드 모두 CLS가 0이었다.

## 검증 증거 (2026-09-30)

- 대상 파일: `apps/stats/test_stats_perf.py` 12 passed.
- 전체 회귀: `conda run -n knou-life-diary python -m pytest -o cache_dir=/tmp/lifediary-pytest-cache` → 605 passed, 214 warnings, 7분 13초 (커밋 `47d8b40`).
  - 직전 main 기록 597개에 이번 트랙의 8건이 더해진 수다.
  - 경고는 모두 워크트리에 `staticfiles/`가 없어 나는 WhiteNoise "No directory at" 한 종류다.
- `python manage.py check` → 이슈 0건.
- `python manage.py makemigrations --check --dry-run` → No changes detected.
- `python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR` → exit 0. W009 1건은 로컬 셸 SECRET_KEY에 대한 기존 경고로, 이번 변경과 무관하다.
- `git diff --check` → 이상 없음.

## 역할별 최종 판정

- Backend TDD Coach: 모든 시나리오 Green, Test List 비었음, 추가 리팩터링 없음, 테스트 작성 정책 결함 없음.
- Domain Architecture Reviewer: 헬퍼 위치 결함은 R1로, 계획 문장 불일치는 계획 수정으로 해소.
- Quality Verification Lead: 완료. 해석 절과 상태 문서의 캐시 효과 문장에 "캐시 미스는 추정 분류"라는 단서가 빠진 문서 결함이 나왔고, 반영했다. 다운로드 시간 원시 값 추가 권고도 반영했다.

## 후속 검증 (2026-09-30, PR #74 머지 후)

사용자가 PR #74를 머지하도록 지시하고, 미검증 항목을 이어서 진행하게 했다. 머지 커밋은 `4f1b12e`이고, 아래 측정은 브랜치 `perf/stats-measurement-verification`에서 했다. 저장소 코드는 바꾸지 않았다.

### 배포 트리

배포는 수동 워크플로라 머지해도 운영에 자동 배포되지 않는다. `.github/workflows/deploy.yml`의 `EXCLUDE_RE`를 `main` 트리에 그대로 적용해 보았다.

- 배포 대상 파일은 277개이고, `request_performance.py`는 없다.
- 이번 트랙에서 실리는 파일은 `apps/stats/conftest.py`와 `apps/stats/test_stats_perf.py`다. 기존 테스트 파일들도 모두 배포 트리에 있으므로 기존 방식 그대로다.

### Chrome 세부 버전

`chrome://version` 기준으로 154.0.8037.58 (공식 빌드, arm64), macOS 15.7.7(빌드 24G720)이다.

### PostgreSQL 벤치마크 (로컬)

- 방법: Homebrew PostgreSQL 14.19(`localhost`)에 일회용 테스트 DB `test_lifediary_perf_probe`를 만들어 돌렸다. 설정 오버라이드는 저장소 밖 스크래치 모듈에 두었다(`dev` 설정을 그대로 쓰고 `DATABASES`만 바꿈). 끝난 뒤 `dropdb`로 지웠고, 남은 DB는 0개였다.
- 측정 파일 전체: 12 passed (22.16초). `database_vendor`는 `postgresql`로 나왔다.
- 벤치마크(`-s`, 단독 실행, 2026-09-30 02:22 KST):

| 라벨 | 쿼리 | 전체 (min / 중앙값 / max, ms) | 렌더 전 중앙값 | 렌더 중앙값 | SQL execute 중앙값 |
|---|---|---|---|---|---|
| warmup | 21 | 1,008.38 | 967.01 | 41.37 | 52.20 |
| cold | 21 × 5 | 791.91 / 849.18 / 1,012.24 | 840.10 | 8.80 | 48.60 |
| warm | 3 × 5 | 12.44 / 13.47 / 14.32 | 4.73 | 8.65 | 2.55 |

원시 값:

- cold 전체: 922.17, 1,012.24, 799.49, 849.18, 791.91
- cold SQL execute: 48.60, 104.91, 47.39, 52.64, 45.59

해석:

- 같은 쿼리 21개인데 PostgreSQL cold가 SQLite(298ms)보다 약 2.8배 느리다.
- SQL execute는 약 49ms뿐이다. PostgreSQL 클라이언트 커서에서는 여기에 전송까지 포함된다. 나머지 약 790ms는 execute 밖, 즉 행 해석과 모델 생성, 집계에 쓰였을 것으로 본다. 이 분해는 계측하지 않았으므로 추정이다.
- 이 수치로 운영 캐시 미스 약 2.7초 가운데 약 0.85초가 설명된다. 남은 약 1.9초는 네트워크 왕복과 서버 CPU 몫으로 좁혀지지만, 역시 추정이다.
- 로컬 서버는 네트워크 지연이 없고 버전이 14다. 운영 Supabase와는 버전과 풀러 구성이 다르다.

### 모바일 측정 (운영 사이트)

측정 조건:

- 에뮬레이션: 390×844, 배율 3, 모바일·터치, CPU 4배 감속, DevTools "Slow 4G" 프리셋. Lighthouse 모바일 기본 조건과 같게 맞췄다. UA는 바꾸지 않았다.
- 실제 모바일 기기나 실제 다른 네트워크가 아니라 에뮬레이션이다.
- 시각: 2026-09-30 02:22~02:28 KST
- 세션: 측정 도중 1시간 세션이 만료되어(`SESSION_COOKIE_AGE = 3600`), 사용자가 다시 로그인한 뒤 측정했다. 만료로 리다이렉트된 로드 1회는 버렸다.

그룹 구성:

- 워밍업: `09-26` 1회
- 캐시 미스: 오늘 처음 연 날짜 5개(`09-02`, `09-06`, `09-11`, `09-16`, `09-21`)
- 캐시 히트: `09-21`을 5번 다시 열기
- 히트 + 브라우저 캐시 무시: 5번 새로고침. 정적 파일 15개를 모두 네트워크로 받는다.

| 그룹 | TTFB (min / 중앙값 / max, ms) | LCP 중앙값 | DOMContentLoaded 중앙값 | load 중앙값 | CLS |
|---|---|---|---|---|---|
| 워밍업 (1회) | 3,339.9 | 3,768 | 4,095.7 | 4,103.7 | 0 |
| 캐시 미스 | 2,695.5 / 2,827.2 / 3,172.0 | 3,328 | 3,576.5 | 3,580.8 | 모두 0 |
| 캐시 히트 | 431.7 / 475.2 / 812.5 | 1,052 | 1,367.5 | 1,372.4 | 모두 0 |
| 히트 + 캐시 무시 | 447.8 / 475.5 / 846.5 | 2,936 | 2,907.3 | **14,981.5** | 0.0001 |

원시 TTFB (ms):

- 미스: 2,695.5, 2,863.5, 2,827.2, 3,172.0, 2,758.2
- 히트: 812.5, 475.2, 432.8, 492.2, 431.7
- 캐시 무시: 462.8, 824.3, 475.5, 447.8, 846.5

원시 LCP (ms):

- 미스: 3,200, 3,344, 3,328, 3,688, 3,292
- 히트: 1,300, 1,068, 1,052, 972, 1,052
- 캐시 무시: 2,936, 3,052, 2,760, 2,788, 3,044

해석:

- TTFB는 데스크톱과 거의 같다. 캐시 미스 중앙값이 데스크톱 2,817ms, 모바일 2,827ms다. 서버 대기 시간이 지배하므로 기기 조건과 무관하다.
- 모바일 LCP는 데스크톱보다 0.5초 정도 길다. CPU 감속과 네트워크 제한의 몫으로 보인다.
- 브라우저 캐시가 비어 있으면 load가 약 15초까지 늘어난다. 원인은 직접 호스팅하는 가변 폰트 `PretendardVariable.<hash>.woff2`다. 전송 크기가 2,010KB라 Slow 4G에서 다운로드에만 약 14.3초가 걸린다(응답 완료 시점 약 15.2초). LCP(약 2.9초)는 이 폰트를 기다리지 않지만, 처음 방문한 모바일 사용자의 데이터 사용량과 load 완료 시점에 영향을 준다. 이번 범위 밖이라 백로그로 남긴다.
- 같은 로드에서 다른 정적 파일의 전송 크기: Font Awesome 웹폰트 153KB, Chart.js 69KB, Bootstrap CSS 33KB.

### 운영 응답 헤더 (엣지 캐시)

Server-Timing 검토 과정에서 보안 검토자가, 로그인 후 응답을 엣지가 캐시하는지 먼저 확인하라고 요구했다. 로그인 상태의 같은 출처 fetch로 캐시 관련 헤더만 읽었다.

- `/stats/?date=2026-09-21`: 200, `server: cloudflare`, `cf-cache-status: DYNAMIC`, `Vary: Cookie, Accept-Language, Accept-Encoding`, `x-render-origin-server: gunicorn`. `Cache-Control` 헤더는 없다.
- 엣지는 Cloudflare(Render 앞단)이고, 현재 통계 응답을 캐시하지 않는다.
- Cloudflare가 이미 `Server-Timing: cfExtPri`를 붙이고 있고, 브라우저의 `PerformanceNavigationTiming.serverTiming`에 `cfExtPri` 항목으로 노출된다.

## 미검증 항목

- 브라우저 "서버 캐시 미스"가 실제로 미스였는지는 여전히 직접 확인하지 못했다. 처음 방문한 날짜이고 TTFB가 히트보다 약 6배 길다는 점으로 추정했다. 사용자가 Server-Timing 헤더 추가를 결정했고, 별도 계획으로 진행한다.
- 운영 서버 안에서 시간이 어디에 쓰이는지. Server-Timing 트랙에서 DB 시간과 쿼리 수를 확인할 예정이다.
- 운영과 같은 PostgreSQL 버전, 풀러, 네트워크 조건에서의 벤치마크. 로컬 14 버전으로만 측정했다.
- 실제 모바일 기기와 실제 다른 네트워크, 다른 시간대의 측정. 모바일은 에뮬레이션으로만 측정했다.

## Deferred

- 운영 캐시 미스(추정) 2.7초의 내역 분해. 로컬 PostgreSQL로 약 0.85초는 설명되었다. 남은 몫은 Server-Timing으로 확인한다.
- 렌더 전 구간 안에서 행 fetch·ORM 모델 생성과 파이썬 집계를 분리하는 계측. 2026-09-29 프로브 기준으로 cold 요청 한 번에 모델 인스턴스가 23,774개 만들어졌다.
- 측정 헬퍼를 `apps/core`로 옮겨 일반화하는 일. 트리거: 통계 외의 앱이 같은 cold/warm 측정 테스트를 필요로 할 때 (Domain Architecture Reviewer 기록).
- `PretendardVariable` 폰트(2,010KB) 경량화. 서브셋 또는 가변 폰트 대신 필요한 굵기만 쓰는 방안. 트리거: 모바일 첫 방문 성능이나 Lighthouse 작업을 할 때.
- 로그인 후 화면 응답에 명시적 `Cache-Control: private, no-store`를 붙이는 일. 지금은 Cloudflare가 `DYNAMIC`으로 캐시하지 않지만, 명시적 헤더가 없다. 트리거: 엣지 캐시 규칙을 바꾸거나 CDN을 도입할 때, 또는 보안 강화 트랙에서 (Security & Resilience Reviewer 기록).
