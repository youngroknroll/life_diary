# 클릭 가능 요소의 호버 상태 복구

날짜: 2026-08-13
계획서: `docs/plans/2026-08-13_hover-state-restoration-plan.md`
편집 파일: `apps/core/static/core/css/style.css` (단일)

## 배경

사용자가 "모든 클릭 이벤트가 발생되는 곳들" 에 호버 효과가 빠졌다고
신고했다. 확인 결과 `style.css` 전체에 `:hover` 규칙이 15개뿐이었고,
템플릿에서 35회 쓰이는 `.btn-sian` 에는 하나도 없었다. 기존 호버 15개 중
13개도 base 선택자에 `transition` 이 없어 즉시 튀었다.

신고에 없었지만 더 심각한 것을 찾았다 — `.slot-block`(하루 24×6 기록
그리드)은 `dashboard.js:664` 에서 `role="button" tabindex="0"` 를 받는데
`:hover` 도 `:focus-visible` 도 없었다. 제품 1순위 루프다.

## 결과

| 항목 | 전 | 후 |
|---|---|---|
| `:hover` 규칙 | 15 | 25 |
| `transition` 선언 | 8 | 24 |
| `:where(:not(:disabled))` 가드 | 0 | 4 |

## 무엇을 어떻게 바꿨나

- 중립 테두리 컨트롤(`.btn-sian`, `.tag-btn`, `.stepper__btn`,
  `.goal-card__header`, `.app-nav__tab`)은 배경 `--color-surface-soft`,
  테두리 `--color-primary-border`. 신규 토큰 없음.
- 인라인 배경 요소(`.slot-block`, `.btn-tag-legend`)는 `box-shadow` 링만.
  태그색이 `style.backgroundColor` 로 박혀 있어 배경을 건드리면 어떤
  태그였는지 알 수 없게 된다.
- 골라내기(`.chip--pick`, `.category-picker__option`)는
  `:not(:has(...:checked))` 로 선택된 것을 제외했다. 안 그러면 "고른 것" 과
  "지금 가리키는 것" 이 구별되지 않는다.
- `.slot-block:focus-visible` 신규. 키보드 사용자가 지금 어느 칸에 있는지
  알 방법이 없었다.
- `.btn-sian:focus-visible` 신규. 35곳이 브라우저 기본 링에만 의존했다.
- 전이는 `0.15s` 로 통일. `transform` 을 쓰지 않아
  `prefers-reduced-motion` 신규 블록이 필요 없다.

## 호버를 주지 않은 것

`.summary-tile`, `.data-table` 행, `.observation`, 바탕 `.chip`,
`.tag-totals__row`, `.card`, `#tagFormPreviewChip`, `.settings-row`,
`.tag-row`. 전부 클릭 핸들러·`href`·`tabindex` 가 없다. 호버는 "누를 수
있다" 는 약속이라 표시 전용에 붙이면 오조작을 부른다.

## 특정도 함정 — 회귀 3건

계획서가 "`.btn-sian--primary:hover` 는 소스 순서상 뒤라 자동으로 이긴다"
고 전제했는데, 그건 **특정도가 같을 때만** 참이다. `:not(:disabled)` 가
(0,2,0) 을 (0,3,0) 으로 올려 순서가 무의미해졌다.

| 회귀 | 실측 |
|---|---|
| primary 버튼이 회색이 됨 | 배경 `rgb(245,246,244)`, 글자 `rgb(20,33,26)` |
| danger 버튼 글자가 안 읽힘 | 대비 **1.64:1** |
| 빈 슬롯에 호버 미발동 | `matches(':hover')` true 인데 그림자 불변 |

세 번째는 `.slot-block:hover`(0,2,0) 가 `.slot-block.is-empty`(0,2,0) 보다
소스 순서상 앞이라 진 것이다. 기록 없는 날은 144칸 전부가 `is-empty` 라
새 사용자에게는 호버가 아예 없었다.

**고침**: `:not(:disabled)` → `:where(:not(:disabled))`. `:where()` 는
특정도가 0 이라 (0,2,0) 을 유지하면서 비활성 요소에 매칭되지 않는 성질은
그대로다. 변형 호버에는 필요한 속성을 전부 선언했다. 슬롯은 특정도를
올리지 않고 미디어 블록을 `.is-empty` 뒤로 옮겼다.

## 리뷰어가 추가로 잡은 것

두 리뷰어가 독립적으로 같은 결함을 지적했다. `.btn-sian--primary:hover` 만
비활성 가드가 없었다. `base.html` 의 전역 제출 핸들러가 `setButtonLoading`
으로 이 클래스 버튼을 비활성으로 만드는데(로그인·회원가입·비밀번호
변경·목표 저장·태그 저장), **비활성 요소도 `matches(':hover')` 가 `true`**
라 호버가 발동했다.

"브라우저가 비활성 요소에 호버를 안 걸 것" 이라는 내 판단이 틀렸다. 반증은
내가 직접 잰 값이었다.

## 검증

브라우저 실측(Chrome, 실제 마우스 호버)은 계획서
`Frontend Review Evidence` 절에 표로 남겼다. 요약:

- primary 호버 `rgb(35,91,60)` / 흰 글자 / 투명 테두리
- danger 호버 대비 **10.16:1** (전 1.64:1)
- 빈 슬롯 호버 링 `rgb(44,110,74) 1.5px inset`, 10분 눈금 유지
- 비활성 primary 호버 시 평상색 `rgb(44,110,74)` 유지
- `.btn-sian` 포커스 `outline: rgb(44,110,74) solid 2px`, offset 2px
- 온보딩 체크된 칩은 호버 중에도 선택 표시 동일
- 터치 에뮬(390x844 DPR 3)에서 `(hover:hover) and (pointer:fine)` = `false`

판정: Web Experience Designer `Conforms`, Browser Interaction Reviewer
`Conforms`.

## 남은 것

**다크 테마 기본 버튼 대비가 기준 미달이다.** 평상 3.01:1, 호버 2.44:1
(기준 4.5:1). 세 역할이 각자 계산해 같은 값이 나왔다.

이번 변경이 만든 문제가 아니다 — `--color-primary` 계열 토큰 값이고
`.btn-sian--primary:hover` 는 원래 있던 15개 호버 중 하나다. 다만 호버가
평상보다 더 나쁘다. 색이 밝아지는 것과 글자 대비가 오르는 것은 다른 축이다.

고치려면 토큰을 바꿔야 하는데 `.btn-primary:hover` 와 텍스트 색으로도 쓰여
브랜드색 결정에 가깝다. 사용자 결정으로 올렸다.

확인하지 못한 것: 실제 터치 기기, 스크린리더, pywebview 데스크톱 셸,
색각 이상 시뮬레이션.
