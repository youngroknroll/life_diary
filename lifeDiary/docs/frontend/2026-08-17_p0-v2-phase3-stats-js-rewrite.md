# P0 v2 3단계 — `stats.js` 전면 재작성

계획: `docs/plans/2026-08-16_p0-v2-handoff-plan.md` 3단계 (§1, 목업 1a·2a–2f).
브랜치: `feat/p0-v2-handoff`.

## 승인된 범위

- `applyChartTheme()` 신설(라이트/다크 공통 기본값), `#themeToggle` 클릭 시 재적용
  (오늘은 토글이 통계 화면과 다른 페이지에 있어 실사용 트리거는 없지만 스펙이 정한
  대로 방어적으로 구현).
- 데이터 단위를 태그 → 카테고리 5선(work/move/care/life/sleep, 2단계가 만든
  `category_stats`/`hourly_stats` 소비)으로 전환.
- 축: 주/월 라인 y 0–24h(모바일 stepSize 12, 데스크톱 6), 일간 스택 y 0–60분
  (눈금 0/30/60), 주 x 고정 라벨(월~일), 월 x 월요일만, 모바일 주간 라벨 월·수·금·일.
- 카드 상단 HTML 칩 범례(클릭 토글+취소선), 모바일은 4개(기초 제외), 데스크톱도
  기초(life)는 기본 꺼짐.
- 다크 배경·모노 폰트 툴팁, 값 내림차순.
- `drawEmptyState`(Arial/#6c757d 하드코딩 canvas 그리기) 삭제 → 데이터 없으면
  `canvas.hidden=true` + 형제 `.chart-empty`(empty-nudge 문법 + 기록 화면 링크).

**제외(§8 미결정 항목 중 이번 단계 범위 밖)**: 목표선(annotation 상수 데이터셋).
`UserGoal`은 태그 단위·복수 목표가 가능해 "이 라인 차트의 목표 1개"를 가리킬 근거
데이터가 없다 — 4단계(목표 진행 바)가 "주요 목표" 개념을 만든 뒤에야 정당하게 값을
채울 수 있다. `renderGoalLineDataset()` 형태로 함수만 준비해 두는 대신, 데이터
계약이 없는 채로 죽은 코드를 남기지 않기 위해 이번 단계에서는 구현하지 않고
Deferred로 남긴다.

## Activated Roles

- Web Experience Designer, Browser Interaction Reviewer — 아래 Frontend Review
  Evidence.
- Frontend Implementation Engineer — 구현.
- Quality Verification Lead — 완료 판정.
- Not activated: 백엔드 TDD 코치(2단계가 이미 데이터를 검증), 보안(개인 데이터 범위
  불변).

## 구현에서 발견해 함께 처리한 것

`apps/stats/logic.py`의 `weekly_stats_json`/`monthly_stats_json` envelope가 2단계가
만든 `category_stats`/`week_start`/`start_date`를 프런트로 넘기지 않고 있었다(2단계는
집계 함수의 반환값에만 추가했다). 이번 단계에서 envelope에 추가했다 — 이미 검증된
값을 그대로 통과시키는 배선이라 새 TDD 사이클 없이 진행하고, 쿼리 예산·회귀
테스트로 안전을 확인했다(아래 검증).

## 구현

- `apps/stats/static/stats/js/stats.js`: 전면 재작성. `CATEGORY_ORDER`/
  `CATEGORY_LINE`/`CATEGORY_FILL_TOKEN`/`MOBILE_LEGEND_KEYS`/`DEFAULT_OFF_KEYS`
  상수, `categoryLineColor`/`categoryFillColor`(다크 모드 분기), `applyChartTheme`,
  `rethemeCharts`+`chartRethemeHandlers`(차트별 재테마 콜백), `buildCategoryLegend`,
  `isCategoryDataEmpty`/`toggleChartEmptyState`. 4개 렌더 함수(`renderHourlyBarChart`,
  `renderWeeklyLineChart`, `renderWeeklyBarChart`, `renderMonthlyLineChart`) 재작성.
  `renderWeeklyBarChart`(요일별 기록량, 단일 계열)는 목업 2a–2f 어디에도 재설계
  대상으로 언급되지 않아 테마 재적용만 추가하고 로직은 그대로 뒀다.
- `apps/stats/templates/stats/index.html`: 세 차트 패널에 `.chart-panel__canvas-wrap`
  + `.chart-empty` 형제 + (라인 차트 둘은) `.chart-legend` 컨테이너 추가. 섹션
  타이틀 카피를 "태그"→"카테고리" 표현으로 갱신(§1.3 근거).
- `apps/core/static/core/css/style.css`: `.chart-panel`을 flex column으로,
  `.chart-panel--tall.has-legend`(범례 공간), `.chart-legend`/`.chart-legend__item`
  (취소선 꺼짐 상태 포함), `.chart-empty`/`.chart-empty__title`/`__hint`/`__action`
  추가.
- `apps/stats/logic.py`: envelope에 `category_stats`/`week_start`/`start_date` 통과.
- i18n: 새/변경 문자열 8개(`{% trans %}`) makemessages로 수집. **회귀 발견·수정**:
  msgmerge가 유사 문자열에 fuzzy 매칭을 걸어 엉뚱한 기존 번역을 물려받았다(예:
  "카테고리별 추세" → 옛 "카테고리 비중" 상속, ko·en 각 6건). ko 6건 항등 번역으로,
  en 6건은 직접 새 영어 문구로 교체하고 fuzzy 플래그를 제거했다
  ([[project_i18n_fuzzy_trap]] 메모리와 일치하는 재현 — msgfmt --check-format +
  수동 fuzzy grep으로 확인).

## Frontend Review Evidence

**Review depth**: Standard — 차트 컴포넌트 내부 변경(데이터 단위·범례·빈 상태), 페이지
간 내비게이션이나 모달·드래그는 없음. 다만 데이터 시각화라 뷰포트·테마 조합을 넓게
확인한다.

**Web Experience Designer — 사전 스펙**
- 카테고리 5색은 목업 3a가 준 표(면=기존 `--color-accent-*`, 선=신규 딥 hex)를
  그대로 쓰고 임의로 조정하지 않는다.
- 범례는 카드 상단 HTML(칩 아님, `.chart-legend__item` 텍스트+14×3 스와치), 클릭 시
  취소선+무채색으로 꺼짐을 표시한다 — Chart.js 네이티브 범례는 완전히 끈다.
- 빈 상태는 canvas를 지우는 대신 형제 DOM(`.chart-empty`)으로 교체하고, empty-nudge
  문법(현재 상태 + 다음 행동 링크)을 따른다.
- 일간 스택은 데이터 단위가 카테고리로 바뀌어도 태그 상세 표(하루 구성)는 그대로
  태그 단위를 유지한다 — 두 단위가 한 화면에 공존하는 것이 스펙의 의도다.

**Browser Interaction Reviewer — 사전 기준**
- 모바일(≤767.98px, 기존 dashboard.js와 동일 브레이크포인트 표현 재사용)에서는
  범례 항목 자체가 4개만 렌더되어야 한다(기초 항목이 꺼진 채로 보이는 게 아니라
  DOM에서 아예 없어야 함) — 목업 2d "선·범례 모두 숨김"의 문자 그대로 해석.
  x축 라벨도 모바일에서 월·수·금·일 넷만 남아야 한다.
- 라이트/다크 전환은 재로드 없이 확인 가능해야 하지만, 오늘은 토글과 차트가 같은
  화면에 없어 실제 트리거 경로가 없다 — 대신 다크 테마로 저장된 상태에서 새로
  로드했을 때 올바른 색이 나오는지(실제로 매 세션이 거치는 경로)를 최소 기준으로
  삼는다.
- 범례 버튼은 `<button type="button">`이라 키보드 포커스·Enter/Space로 조작
  가능해야 한다(스와이프·드래그 없음, 클릭 핸들러만).
- 빈 상태 링크(`오늘 기록 이어가기`)는 실제 `<a href>`라 스크린리더 랜드마크 없이도
  탭 이동이 가능해야 한다.

## 검증

- `node --check apps/stats/static/stats/js/stats.js` — 통과.
- `conda run -n knou-life-diary python manage.py check` — 이슈 없음.
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run` —
  변경 없음.
- `conda run -n knou-life-diary pytest apps/stats apps/dashboard apps/tags apps/users -q`
  — 전부 통과(쿼리 예산 포함, envelope 변경으로 인한 회귀 없음).
- i18n: `msgfmt --check-format` ko·en 통과, `compilemessages` 통과,
  `test_pytest_i18n_compile.py` 통과, `python manage.py shell`에서 ko/en 활성화 후
  `gettext()`로 8개 신규 문자열 직접 조회해 두 언어 모두 올바른 번역 확인.
- 브라우저 실측(chrome-devtools MCP, 격리된 임시 SQLite + `runserver 8765`로 확인.
  dev DB는 열지 않았고, 확인 후 임시 DB·임시 설정 모듈 삭제):
  - 로그인 사용자에 투자/주도적/수동적/수면 4개 카테고리 태그로 1주일치 시드
    (기초=life 카테고리는 의도적으로 데이터 없음 — 기본 꺼짐 상태를 눈으로 구분하기
    위함).
  - **일간(스택)**: 카테고리 색 스택 바, y축 0/30/60분, x축 0/6/12/18/23시만 라벨,
    미분류 시간이 차트에 안 나타나고 아래 표에만 "미분류 11.0h"로 남음(§1.3 대로).
    콘솔 오류 0.
  - **주간(라인, 1280px)**: 범례 5개(기초는 회색+취소선), 값 라인 4개(work/move/
    care/sleep) 정상 렌더, y축 0/6/12/18/24h. 기초 범례 클릭 → 취소선 해제 확인
    (데이터가 0이라 선 자체는 평평).
  - **주간(라인, 375px 새로고침 로드)**: 범례 4개만 렌더(기초 항목이 DOM에 없음),
    x축 라벨 월·수·금·일만, y축 0/12/24h(step 12) — 목업 2d와 일치.
  - **월간(라인)**: x축이 8월 각 월요일(3·10·17·24·31일)만 라벨, y축 0/12/24h,
    기초 카테고리 기본 꺼짐 유지, 트렌드 모양이 시드 데이터(8/10–16주만 기록)와
    일치.
  - **빈 상태(일·주·월 세 탭 모두, 2026-01-05 조회)**: canvas 숨김, `.chart-empty`
    표시("오늘/이번 주/이번 달 기록이 아직 없습니다" + "오늘 기록 이어가기" 링크),
    범례 컨테이너도 함께 숨김. 콘솔 오류 0.
  - **다크 모드(설정에서 테마 전환 → 통계 페이지 재방문)**: 카테고리 선 색이 파스텔
    원색으로 전환(예: 수면=연보라 `#B8A6F0` 계열), 그리드·툴팁 배경도 다크 토큰으로
    전환. 콘솔 오류 0.
  - 요일별 기록량(단일 계열, 재설계 범위 밖) 라이트/다크 모두 정상 렌더 확인 —
    회귀 없음.

## Frontend Review Evidence — 판정

- **Web Experience Designer**: Conforms — 카테고리 5색·범례 마크업·빈 상태 문법·
  태그 상세 표 유지 네 기준 모두 스크린샷·스냅샷으로 확인.
- **Browser Interaction Reviewer**: Conforms — 모바일 범례 4개+DOM 부재, x축 라벨
  구성, 다크 모드 로드 경로, 범례 버튼 접근성(네이티브 `<button>`) 확인. 실시간
  토글 클릭 경로(같은 화면에 토글이 없어 실사용 안 됨)는 Unverified로 남긴다 —
  4단계 이후 설정 페이지 위치가 바뀌지 않는 한 이 경로는 앱에서 발생하지 않는다.
- **Quality Verification Lead**: 완료로 판정 — 두 역할 모두 Conforms, 남은
  Unverified 항목(실시간 토글 경로)은 이번 화면 구성상 트리거 자체가 없어 수용
  기준 밖으로 판단.

## Deferred

- 목표선(annotation 상수 데이터셋) — 위 "제외" 참조, 4단계에서 데이터 계약이
  생긴 뒤 별도로 처리.
- 목업 1a의 라이트 모드 work 라인 아래 `opacity:.07` 영역 채우기 — 1단계 계획서에서
  이미 장식적 요소로 판단해 Deferred 처리한 항목, 이번 단계도 동일하게 유지.
