# 통계 탭 성능 최적화 계획

- 작성일: 2026-04-26
- 대상: `apps/stats/`
- 상태: 사용자 확인 후 진행

## 요구사항

통계 탭의 응답 시간과 초기 렌더 비용을 줄인다. 백엔드(중복 쿼리·반복 집계)와 프론트(차트 일괄 렌더) 양쪽이 모두 병목이다. 캐시 레이어(`GetStatsContextUseCase`)는 이미 있으므로, **캐시 미스 경로의 비용을 낮추는 것**이 핵심 목표.

## 현황 진단

`Explore` 에이전트 조사 결과 다음 병목 후보가 식별되었다.

| # | 이슈 | 위치 | 영향 | 작업량 |
|---|------|------|------|--------|
| 1 | `find_daily_counts()` 중복 호출 | `aggregation/calculator.py:88,103` | HIGH | Low |
| 2 | Chart.js 6개 차트가 `DOMContentLoaded`에서 일괄 렌더 (숨겨진 탭 포함) | `static/stats/js/stats.js:80-85` | HIGH | Medium |
| 3 | `find_by_month()` 중복 호출 | `aggregation/monthly.py:8` vs `analysis.py:9` | MEDIUM | Low |
| 4 | 주간 블록 그룹핑이 Python 메모리에서 수행 | `aggregation/weekly.py:20-23` | MEDIUM | Medium |
| 5 | Goal progress 3회 반복 attach | `logic.py:70-76` | MEDIUM | Low (별도 판단) |

## Phase 0 — 베이스라인 측정 (필수)

추측 기반 최적화를 막기 위해 먼저 측정한다 (Golden Principle #10: Evidence-Based Completion).

**산출물**:
- 백엔드: `/stats/` 요청의 쿼리 수·총 시간 (django-debug-toolbar 또는 `connection.queries` 미들웨어)
- 프론트: `performance.mark/measure` 기반 차트 6개의 개별 렌더 시간
- 데이터: 한달치 TimeBlock이 채워진 시드 (없으면 pytest fixture)
- 기록: `docs/performance/stats-baseline-2026-04-26.md`

**예상 작업량**: 1–1.5h

## Phase 1 — 백엔드 중복 쿼리 제거

**파일**: `apps/stats/aggregation/calculator.py`, `apps/stats/logic.py`, `apps/stats/aggregation/{monthly,analysis,weekly}.py`

1. `find_daily_counts()` 중복 호출 제거 → `StatsCalculator.__init__`에서 1회 호출 후 인스턴스 속성 공유
2. `find_by_month()` 중복 호출 제거 → `logic.py`에서 한 번 fetch한 queryset을 두 집계 함수에 주입
3. 주간 집계 in-Python 그룹핑 → `.values('date').annotate(Count('id'))`로 DB 위임

**검증**:
- 베이스라인 대비 쿼리 수 감소 측정
- pytest 통과
- 집계 결과 동일성 보장: 스냅샷 테스트 1건 추가

**예상 작업량**: 2–3h

## Phase 2 — 프론트엔드 차트 lazy render

**파일**: `apps/stats/static/stats/js/stats.js`, `apps/stats/templates/stats/index.html`

현재 `DOMContentLoaded`에서 6개 차트를 모두 생성. **활성 탭의 차트만 렌더**하고 나머지는 탭 전환 시 1회 lazy 생성.

1. 차트 생성 로직을 4개 함수로 분리 (daily / weekly / monthly / analysis)
2. `renderedTabs = new Set()` 가드로 탭당 1회만 생성
3. 초기 활성 탭(URL hash 기반)만 즉시 렌더, 나머지는 탭 클릭 시 호출
4. JSON 데이터는 그대로 script 태그 embed 유지 (서버 라운드트립 없음)

**검증**:
- 초기 렌더 시간 측정 (4개 탭 → 1개 탭 분량)
- 4개 탭 모두 클릭하며 각 차트 정상 렌더 (수동 + Playwright 가능 시)

**예상 작업량**: 2–3h

## Phase 3 — 측정 및 마무리

- 베이스라인 대비 개선치 기록: `docs/performance/stats-after-2026-04-26.md`
- before/after 표: 쿼리 수, 백엔드 총 시간, 차트 렌더 시간
- `prompt_plan.md` 갱신 + 본 문서 링크

## 의존성

- Phase 0 → Phase 1, 2 (측정 없이 최적화 불가)
- Phase 1 ↔ Phase 2 독립 (병렬 가능, 단 측정은 순차)

## 리스크

| 등급 | 항목 | 완화책 |
|------|------|--------|
| MEDIUM | 쿼리 합치는 과정에서 집계 결과 변경 | 기존 출력 스냅샷 테스트로 방어 |
| MEDIUM | Chart.js가 숨겨진 탭에서 0 width 렌더 이슈 | 탭 활성화 후 렌더로 우회 (계획대로) |
| LOW | 캐시 적중 상태에서는 Phase 1 효과 미미 | 캐시 미스 경로(첫 방문, 오늘 5분 이후)에서 측정 |

## 복잡도: **MEDIUM-LOW**

- Phase 0: 1–1.5h
- Phase 1: 2–3h
- Phase 2: 2–3h
- **합계: 5–7.5h**

## 범위 제외 (이번에는 하지 않음)

- Goal progress 3회 attach (logic.py:70-76) — 영향도 불명확, 측정 후 별도 판단
- 캐시 TTL 정책 개선 — 현재 정책이 잘못됐다는 근거 없음
- `select_related/.only()` 추가 — Phase 1 측정 결과 보고 결정

## 다음 단계

1. 사용자 확인
2. `/tdd` 또는 `/auto`로 Phase 0부터 순차 진행
3. 완료 시 본 문서에 결과 링크 추가
