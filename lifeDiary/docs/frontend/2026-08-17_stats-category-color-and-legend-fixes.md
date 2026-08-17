# 분석 화면 카테고리 색 불일치와 기초 생활시간 고정 해소

사용자 지시(2026-08-17). "그래프의 카테고리 색상이 맞지 않고, 기초생활시간이
non-check로 고정된 것 같다"는 보고에서 출발했다.
브랜치: `fix/stats-category-line-colors`.

## 승인된 범위

조사 결과 원인이 셋으로 갈렸고, 사용자가 두 가지를 결정한 뒤 셋 모두 고쳤다.

1. 선 팔레트가 파스텔 개편 이전 값이라 `life`·`sleep`의 색상(hue)이 카테고리 색과
   다르다 → **딥 변형으로 보정**(사용자 결정).
2. 테마 전환 감지가 존재하지 않는 요소 id를 보고 있어 다크 모드에서 차트만 라이트
   색으로 남는다 → 속성 관찰로 교체.
3. 기초 생활시간이 기본 꺼짐이고 모바일에서는 범례 항목조차 없어 켤 방법이 없다 →
   **기본 켜짐 + 전 뷰포트 범례 노출**(사용자 결정).

## Activated Roles

- Frontend Implementation Engineer — 조사와 구현.
- Not activated: Web Experience Designer, Browser Interaction Reviewer.
  이 세션은 에이전트 위임이 요청되지 않아 두 프런트엔드 리뷰 역할을 활성화하지
  않았다. `CLAUDE.md`가 요구하는 dual-review 증거가 이 변경에는 **없다**.
  머지 전에 두 역할의 판정을 받는 것을 권한다.
- Not activated: 백엔드 역할. 집계·뷰·컨텍스트 계산은 무변경이고, 서버 쪽 변경은
  색 상수 딕셔너리의 값 두 개뿐이다.

## 1. 선 팔레트가 파스텔 개편을 따라오지 않았다

**원인.** 카테고리 색은 `0010_pastel_category_palette`(2026-08-11, PR #40)에서
파스텔로 바뀌었고 CSS 토큰 `--color-accent-*`도 같이 갱신됐다. 그런데 차트 선용
딥 팔레트는 그 이전 값(`0010`의 `PREVIOUS_COLORS`)을 그대로 들고 있었다.

`work`·`move`·`care`는 색상이 같은 딥 변형이라 의도대로 읽혔지만 둘이 어긋났다.

| key | 면 (DB·CSS) | 수정 전 선 | 문제 |
|---|---|---|---|
| work | `#7CD9A0` | `#4E8F63` | 정상(같은 hue의 딥) |
| move | `#7DCFE8` | `#4F8B9E` | 정상 |
| care | `#FFA98C` | `#C1715A` | 정상 |
| life | `#FFD166` 호박 | `#B9C2BA` **회색** | 어느 팔레트에도 없던 값 |
| sleep | `#B8A6F0` 라벤더 | `#8A9A91` **회녹** | 파스텔 개편에서 hue가 바뀐 걸 미반영 |

`life`의 대비는 흰 배경에서 **1.83**으로, 형제 카테고리의 3.63~3.87에 한참 못 미쳤다.
그리드선(`--color-border-soft`)과 구별되지 않아 "선이 안 그려졌다"로 읽혔다.

**수정.** 짝이 되는 면의 hue를 따라가면서 대비를 형제 밴드에 맞췄다.

| key | 수정 후 | 흰 배경 대비 |
|---|---|---|
| life | `#A87A1A` | 3.84 |
| sleep | `#8A78D0` | 3.70 |

같은 팔레트가 두 곳에 복제돼 있어 양쪽을 함께 고쳤다.
- `apps/stats/static/stats/js/stats.js`의 `CATEGORY_LINE` — 차트 선·범례 스와치
- `apps/stats/aggregation/category_keys.py`의 `CATEGORY_LINE_COLOR` — 목표 진행 바
  채움(`goal_progress.py:105` → `stats/index.html`, `users/_goal_manager.html`)

두 곳이 같은 값이어야 한다는 사실을 양쪽 주석에 명시했다. 서버가 인라인 style로
내보내야 해 CSS 토큰 단일 출처로 합칠 수 없다(`INK_ON_ACCENT`와 같은 제약).

## 2. 테마 전환 감지가 끊겨 있었다

**원인.** `stats.js`가 `getElementById('themeToggle')`에 클릭 리스너를 걸었는데
**`themeToggle`이라는 요소는 저장소 어디에도 없다.** 실제 컨트롤은 헤더의
`#themeMenu` 안 `[data-theme-choice]` 버튼이다(`templates/shared/_nav_prefs.html`,
`base.html:75`). 헤더 컨트롤 이식(`9d271a5`, 2026-08-17)으로 위치가 바뀌었지만
`stats.js`는 그대로였다.

그 결과 `rethemeCharts()`가 한 번도 실행되지 않았다. `categoryLineColor()`는 다크에서
파스텔을 쓰도록 분기하지만 그 분기가 재계산되지 않아, 다크로 바꾸면 차트 선만 라이트용
딥 색으로 남고 축·그리드 색(`Chart.defaults`)도 라이트 값에 머물렀다.

**수정.** `<html data-theme>` 속성을 `MutationObserver`로 관찰한다.

```js
new MutationObserver(rethemeCharts).observe(document.documentElement, {
    attributes: true, attributeFilter: ['data-theme'],
});
```

id 대신 속성을 보는 이유는 두 가지다. `base.html`의 `paint()`가 커스텀 이벤트를 쏘지
않아 관찰할 신호가 그 속성뿐이고, 헤더 메뉴 클릭과 '시스템' 설정에서의 OS 테마 변경을
한 번에 잡는다. 컨트롤의 id가 또 바뀌어도 다시 끊기지 않는다.

## 3. 기초 생활시간이 모바일에서는 켤 수 없었다

**원인.** 두 상수가 겹쳐 작동했다.
- `DEFAULT_OFF_KEYS = ['life']` → 데이터셋을 `hidden: true`로 만든다.
- `MOBILE_LEGEND_KEYS = ['work','move','care','sleep']` → 767.98px 이하에서 범례를
  4개만 그린다.

데스크톱에서는 클릭 토글 자체가 정상이었다(브라우저에서 off→on→off→on 확인). 하지만
**모바일에서는 숨겨진 데이터셋을 되살릴 버튼이 아예 없었다.** 여기에 1번의 회색 선이
겹쳐 데스크톱에서도 "켜도 안 켜진다"로 보였다.

**수정.** 사용자 결정에 따라 두 상수를 모두 제거했다. 5개 카테고리가 뷰포트와 무관하게
범례에 나오고 전부 기본 켜짐이다. `buildCategoryLegend`는 `mobileKeys` 인자를 잃고
`CATEGORY_ORDER`를 직접 순회하므로 `datasetIndex`가 `forEach` 인덱스와 같아졌다.

**함께 고친 잠복 버그.** 범례의 취소선 상태를 `DEFAULT_OFF_KEYS` 상수에서 칠하고
있었다. 테마 전환 핸들러가 범례를 다시 그리므로, 사용자가 끈 선이 차트에서는 꺼진 채
범례에서만 켜진 것처럼 보이게 된다. 지금은 2번 때문에 리테마가 돌지 않아 드러나지
않던 것이, 2번을 고치면 바로 드러난다. 표시 상태를 `chart.isDatasetVisible()`에서
읽도록 바꿔 함께 막았다.

## 확인했으나 고치지 않은 것

사용자의 첫 보고("카테고리 시간이 맞지 않다")를 따라 집계도 대조했다. 월간
`category_stats`의 카테고리별 합계는 원시 블록 수와 일치했다(dev DB 사용자 1의
2026-08: `move` 177블록 = 29.5h, `sleep` 46블록 = 7.67h → 집계 29.5 / 7.7, 일별 합도
일치). 집계 결함은 확인되지 않아 손대지 않았다.

## 검증

- `node --check apps/stats/static/stats/js/stats.js` — 통과.
- `conda run -n knou-life-diary python manage.py check` — 이슈 0.
- `conda run -n knou-life-diary pytest apps/stats apps/tags -q` — exit 0(270 passed).
- `conda run -n knou-life-diary pytest -q`(전체) — **exit 0, 543 passed**.
- 브라우저 실측: 실제 `apps/stats/static/stats/js/stats.js`를 그대로 `<script src>`로
  로드하는 하니스 페이지(Chrome, Chart.js 3.9.1, 실제 CSS 토큰 값, Django JS i18n은
  스텁). 500px 뷰포트.

| 항목 | 결과 |
|---|---|
| 범례 항목 수(500px) | 5개 — `life` 포함 |
| 기본 표시 상태 | 5개 전부 `visible: true`, 취소선 0개 |
| 라이트 선 색 | `#4E8F63 / #4F8B9E / #C1715A / #8A78D0 / #A87A1A` |
| 다크 전환 후 선 색 | `#7CD9A0 / #7DCFE8 / #FFA98C / #B8A6F0 / #FFD166`(파스텔 토큰) |
| 다크 전환 후 축·그리드 | `Chart.defaults.color=#9aa39d`, `borderColor=#303733` |
| 토글 상태 유지 | `life`를 끈 뒤 다크 전환 → `off:true, visible:false` 유지 |
| 라이트 복귀 | 딥 팔레트로 정상 복원 |
| 콘솔 | 오류·경고 0 |

**미검증.** 로그인 세션이 필요한 실제 `/stats/` 페이지에서는 확인하지 않았다. 계정을
만들면 dev DB에 영구 객체가 생기므로(프로젝트 금지 사항) 하니스로 대체했다. 따라서
템플릿이 내려주는 실제 `category_stats` JSON과의 결합, 목표 진행 바의 새 채움색이
화면에 렌더되는 모습, 탭 전환 후 캔버스 리사이즈는 실측하지 않았다.
자동 대비 검사 도구는 돌리지 않았고 대비 수치는 hex 값으로 계산했다.

## Frontend Review Evidence — 판정

**없음.** 위 Activated Roles에 적은 대로 두 프런트엔드 리뷰 역할을 활성화하지 않았다.
`CLAUDE.md`의 dual-review 게이트는 이 변경에 대해 **충족되지 않았다.**

## Deferred

`docs/project-status.md`의 통합 Deferred 표에 A-6, C-11로 등록했다.

| ID | 내용 |
|---|---|
| A-6 | **통계 캐시에 옛 색이 남는다.** `GetStatsContextUseCase`가 `category_line_color`를 포함한 컨텍스트를 파일 캐시에 담는다(과거 날짜 TTL 24시간). 배포 후 `.cache/`를 비우지 않으면 목표 진행 바가 만료까지 옛 회색으로 보인다. 기존 A-1(캐시 키 버전 부여)과 같은 뿌리이고, 차트 선 색은 정적 파일이라 영향 없다. |
| C-11 | **`summary.py`의 `NEUTRAL_COLOR = "#8A9A91"`.** 옛 sleep 색과 같은 값이지만 관찰 문구의 중립 점 색이라 카테고리 색이 아니다. 이번 범위 밖이라 그대로 뒀다. 의도적 중립인지 복사 잔재인지는 확인하지 않았다. |
