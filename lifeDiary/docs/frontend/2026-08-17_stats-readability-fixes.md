# 분석 화면 가독성 수정 3건

사용자 지시(2026-08-17). P0 v2 트랙 3·4단계로 들어간 화면에 대한 후속 수정이다.
브랜치: `feat/p0-v2-handoff`.

## 승인된 범위

사용자가 지목한 3건만 고친다.

1. 그래프 호버 툴팁의 글자와 배경이 비슷해 읽히지 않는다 → 글자를 검정으로.
2. 요약 탭 "기록 밀도"에 x축·y축 설명이 없어 무슨 필드인지 알 수 없다.
3. 주 탭 "요일별 기록량"의 값 축이 24시간 고정이어야 한다.

## Activated Roles

- Web Experience Designer, Browser Interaction Reviewer — 아래 판정.
- Frontend Implementation Engineer — 구현.
- Quality Verification Lead — 완료 판정.
- Not activated: 백엔드 역할(집계·뷰·컨텍스트 무변경, 템플릿과 CSS·JS만 손댔다).

**Review depth**: Standard — 컴포넌트 내부의 색·축·라벨 변경이고, 내비게이션이나
비동기 상태는 건드리지 않는다. 다만 색 대비는 두 테마 모두 실측해야 한다.

## 1. 툴팁 대비

**원인.** `tooltipBaseOptions()`가 배경만 `--color-text`로 지정하고 글자색을 지정하지
않아, Chart.js가 `Chart.defaults.color`(= `--color-text-meta`, 회색)를 썼다.
`--color-text`는 라이트에서 `#14211A`(검정), **다크에서 `#E4EBE6`(흰색)**이라,
다크 모드에서 흰 배경 위에 회색 글자가 되어 거의 읽히지 않았다. 사용자가 본 화면이
이 경우다.

**수정.** 글자색을 배경의 반대인 `--color-surface`로 못박았다. 토큰이 테마를 따라가므로
분기 없이 두 테마가 동시에 해결된다.

| 테마 | 배경 (`--color-text`) | 글자 (`--color-surface`) |
|---|---|---|
| 라이트 | `#14211A` 검정 | `#ffffff` 흰색 |
| 다크 | `#E4EBE6` 흰색 | `#1a1f1c` **검정** |

사용자 요청("검정으로")은 사용자가 쓰는 다크 모드에서 그대로 충족되고, 라이트 모드는
반대로 흰 글자가 되어 대비를 유지한다. 시안 2a의 "어두운 툴팁" 의도도 라이트에서는
그대로 지켜진다.

## 2. 기록 밀도 축 라벨

**원인.** 보이는 히트맵(`.density__grid`)은 `aria-hidden="true"`인 순수 시각 요소이고,
축 라벨은 `visually-hidden` 표에만 있었다. 즉 **화면에는 축 설명이 아예 없었다.**

**수정.** 히트맵을 `.density__chart`로 감싸고 축 라벨을 화면에 노출했다.
- 세로: 7일치 날짜(`8/11`…`8/17`). `.density__ylabels`를 `grid-auto-rows: 14px; gap: 1px`
  로 두어 셀 높이·간격과 같은 리듬을 만들어 행에 정렬시켰다.
- 가로: `0 / 6 / 12 / 18 / 24`.
- 캡션에 축 설명을 덧붙였다: "…세로는 날짜, 가로는 하루 24시간입니다."

축 라벨도 `aria-hidden`이다 — 읽기는 기존 `visually-hidden` 표가 이미 담당하므로,
노출하면 스크린리더에 같은 내용이 두 번 들어간다.

**백엔드 무변경.** `summary.density.grid`(7×24)와 `summary.density.rows`(날짜 포함)가
인덱스 정렬돼 있어, 라벨 열을 별도 블록으로 렌더하면 파이썬을 고치지 않아도 된다.
`_density_rows`에 시간별 배열을 추가하는 편이 마크업은 단순하지만 그건 백엔드 변경이라
Backend TDD 사이클이 필요하다 — 순수 프런트로 끝나는 쪽을 골랐다.

## 3. 요일별 기록량 값 축

**원인.** `renderWeeklyBarChart`의 y축이 `beginAtZero: true`만 있고 상한이 없어 기록량에
따라 눈금이 달라졌다. 바로 위 "카테고리별 추세"는 0–24h 고정이라 두 그래프를 나란히
두고도 비교할 수 없었다.

**수정.** `min: 0, max: 24`, 눈금 `v => v + 'h'`, 데스크톱 stepSize 6 / 모바일 12로
선 차트들과 같은 규칙에 맞췄다. 함께 x축 그리드를 끄고 툴팁·그리드 색을 다른 차트와
같은 토큰 기반으로 통일했으며, 테마 재적용 핸들러에도 등록했다.

사용자는 "x축"이라 했지만 요일이 가로축이고 24시간은 세로축이다. 의도가 "값 축을 24시간
고정으로"인 것이 분명해 세로축을 고정했다.

## 구현 중 발견해 고친 것

`{# … #}`로 단 두 줄짜리 주석이 **화면에 그대로 출력**됐다. Django의 `{# #}`는 한 줄
주석이라 여러 줄을 감싸지 못한다. 프로젝트 주석 규칙(기본적으로 달지 않는다)에 따라
주석 자체를 지웠다 — `aria-hidden`이 코드에 그대로 보인다.

## 검증

- `node --check apps/stats/static/stats/js/stats.js` — 통과.
- `conda run -n knou-life-diary python manage.py check` — 이슈 없음.
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run` —
  변경 없음.
- `conda run -n knou-life-diary pytest -q`(전체) — exit 0.
- i18n: 캡션이 기존 문장을 늘린 형태라 예상대로 fuzzy 오상속이 났다(ko는 옛 짧은 문장,
  en은 옛 영어 문장을 물려받음). 양쪽 수동 교정 후 fuzzy 0건(헤더 제외),
  `msgfmt --check-format` ko·en 통과, `compilemessages` 통과, `gettext()`로 두 언어
  직접 조회해 새 문장이 나오는 것 확인.
- 브라우저 실측(격리 임시 SQLite + `runserver 8765`, 종료 후 임시 DB·설정·`.cache/` 삭제):

| 항목 | 결과 |
|---|---|
| 툴팁(다크) | 배경 `#E4EBE6` + 글자 `#1a1f1c`, 값 내림차순 유지, 스크린샷으로 판독 확인 |
| 툴팁(라이트) | 배경 `#14211A` + 글자 `#ffffff`, 스크린샷으로 판독 확인 |
| 기록 밀도 축 | y 라벨 7개(8/11–8/17) 행 정렬 오차 ≤1px, x 라벨 5개(0/6/12/18/24), 셀 168개(7×24) |
| 기록 밀도 넘침 | `document.scrollWidth == window.innerWidth`(가로 스크롤 없음) |
| 요일별 기록량 | y 눈금 `["0h","6h","12h","18h","24h"]`, 위 추세 그래프와 같은 척도로 렌더 |
| Django 주석 누출 | 수정 후 본문에서 사라짐 |
| 콘솔 | 오류·경고 0 |

**미검증**: 툴팁을 실제 마우스 이동으로 띄우는 대신 `mousemove`를 디스패치해 확인했다
(실제 포인터 하드웨어 경로는 미검증). 색 대비 수치는 토큰 값으로 계산했고 자동 대비
검사 도구는 돌리지 않았다.

## Frontend Review Evidence — 판정

- **Web Experience Designer**: Conforms — 툴팁이 두 테마 모두 판독 가능, 밀도 히트맵이
  축 설명 없이 읽히던 문제 해소, 두 그래프의 척도 통일로 비교 가능해짐.
- **Browser Interaction Reviewer**: Conforms — 축 라벨을 `aria-hidden`으로 두어 기존
  `visually-hidden` 표와 중복 낭독이 생기지 않음을 확인. 모바일 폭에서 가로 넘침 없음.
  실제 포인터 하드웨어 경로는 Unverified로 남긴다(디스패치로 대체 검증).
- **Quality Verification Lead**: 완료로 판정 — 지시 3건 모두 실측으로 확인, 전체 테스트
  통과, 잔여 Unverified 항목은 이 변경의 수용 기준에 해당하지 않음.

## Deferred

없음.
