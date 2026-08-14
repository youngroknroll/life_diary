# 기본 버튼 — 다크 대비 수정과 눌림 상태 신설

날짜: 2026-08-14
계획서: `docs/plans/2026-08-14_dark-primary-button-contrast-plan.md`
편집 파일: `apps/core/static/core/css/style.css` (단일)

## 두 갈래로 진행됐다

### 1. 다크 테마 대비 미달

직전 호버 작업의 이연 건이다. 다크에서 초록 배경 위 흰 글자가 평상
3.01:1, 호버 2.44:1 로 기준 4.5:1 을 못 넘었다. 세 역할이 각자 계산해 같은
값이 나왔다.

사용자 결정: **초록 유지, 글자만 반전.**

| 다크 테마 | 전 | 후 |
|---|---|---|
| 평상 | 3.01:1 | **5.91:1** |
| 호버 | 2.44:1 | **7.31:1** |

라이트는 6.11 / 7.98 로 변화 없다. 초록 배경값을 손대지 않았다.

### 2. 눌림 상태

대비 수정을 검증하다가 부트스트랩 `.btn-primary` 가 키보드 포커스와 눌림에서
배경을 **부트스트랩 파랑**으로 바꾸는 것을 실제 Tab 키로 확인했다.

사용자가 "이벤트 발생 표시를 위해 만든 것 아니냐" 고 물었다. 근거 셋으로
의도가 아님을 확인했다.

1. 저장소 CSS 에 파랑 리터럴이 0건. 부트스트랩 기본값이다.
2. `.btn-primary` 와 그 `:hover` 는 일부러 초록으로 덮여 있다. 눌림만
   안 덮었다.
3. `style.css` 전체에 `:active` 규칙이 0개였다.

사용자 결정: **초록 계열 눌림 상태를 만든다.**

## 리뷰어가 제 안을 세 번 고쳤다

**첫째, 잉크 색.** 내가 고르려던 `#14211A` 는 저장소가 **이미 부족하다고
판정하고 버린 값**이었다. 36행 주석에 "시안의 `#14211A` 는 투자·주도적
색에서 4.5:1 에 못 미쳐 한 단계 낮췄다" 고 적혀 있다. 기존
`--ink-on-accent`(`#0F1A14`)를 참조하니 새 리터럴도 안 늘고 대비도 더
높다.

**둘째, 토큰 이름.** `--color-ink-on-primary` → `--ink-on-primary`.
`--ink-on-accent` 가 이미 있어 접두 없는 계열이 서 있다.

**셋째, 부트스트랩을 이기는 선택자.** Web Experience Designer 는
`.btn-primary:active` 로 충분하다고 했다. 근거는 "호버가 이미 그렇게
이긴다" 였는데 **호버에서만 참**이다.

| | 부트스트랩 | 필요한 것 |
|---|---|---|
| 호버 | `.btn:hover` (0,2,0) | `.btn-primary:hover` 로 충분 |
| 눌림 | `.btn:first-child:active` **(0,3,0)** | `.btn` 을 함께 적어야 함 |

CSSOM 으로 실측했다: 부트스트랩 순번 557, `.btn.btn-primary:active` 순번
4764. 동률에 뒤 순서라 이긴다. Browser Interaction Reviewer 안이 맞았다.

## 내가 낸 결함 하나

**키보드로 누르면 눌림색이 아니라 포커스색이 나왔다.** `:active` 를
`:focus-visible` 앞에 뒀는데 동률이라 뒤가 이겼고, 키보드로 누르면 두
상태가 동시에 참이라 포커스가 눌림을 덮었다.

이 결함은 "실측 못 한다" 로 넘어갈 뻔했다. Browser Interaction Reviewer 가
"대안을 시도하지 않고 확정 불가로 끝내는 것은 부족하다" 고 반박해 다시
시도한 끝에 잡혔다.

찾은 방법: `keydown` 리스너 안에서 `requestAnimationFrame` 으로 다음
프레임에 측정한다. `keydown` 동기 시점엔 `matches(':active')` 가 `false`
지만 다음 프레임엔 `true` 다. 핸들러가 브라우저 기본 동작보다 먼저 돈다.

거기서 한 번 더 막혔다. 순서를 고쳤는데도 포커스색이 나왔는데, 원인은
**전이**였다. `.btn` 이 0.15s 전이를 갖는데 Space 는 순간이라 끝나기 전에
풀린다. `rAF 2` 에서 배경이 `rgb(93,184,127)` 로 눌림색 쪽으로 움직이는
것을 보고 방향을 잡았고, 전이를 끄니 확정됐다.

```
Space keydown → rAF (transition: none)
active: true
배경 rgb(117,195,146) = --color-primary-press 다크값
글자 rgb(15,26,20)    = --ink-on-primary 다크값
대비 8.47:1
```

세 곳의 순서를 뒤집었지만 **실제 충돌은 `.btn.btn-primary` 한 곳뿐**
이었다. `.btn-sian` 과 `.stepper__btn` 의 `:focus-visible` 은 `outline`
만 건드려 속성이 겹치지 않는다. 나머지 둘은 방어적으로 맞춘 것이다.

## 눌림을 주지 않은 곳

`.slot-block`, `.tag-btn`, `.chip--pick`, `.category-picker__option`,
`.goal-card__header`.

**누르면 이미 결과가 남기 때문이다** — 슬롯은 선택 표시가 뜨고, 칩은 체크가
되고, 목표 카드는 펼쳐진다. 눌림 색을 얹으면 곧 나타날 상태와 겹쳐
깜빡이거나 묻힌다.

## 대비 (WCAG 상대휘도, 기준 4.5:1)

| 대상 | 라이트 | 다크 |
|---|---|---|
| `.btn-sian` 눌림 | 5.43 | 4.78 |
| `.btn-sian--primary` 눌림 | 10.68 | 8.47 |
| `.btn-sian--danger` 눌림 | 13.32 | 13.32 |
| `.app-nav__tab` 눌림 | 14.78 | 11.88 |

## 원 지시 범위를 넘은 것

`.app-nav__tab:active` 는 사용자 지시(버튼)에 없었다. Web Experience
Designer 권고를 받아 넣었고 Browser Interaction Reviewer 가 범위 밖임을
지적했다. 사용자에게 밝혔다.

## 검증

497 passed · `manage.py check` 0 issues.

판정: Web Experience Designer `Conforms`, Browser Interaction Reviewer
`Conforms` (일부 항목 `Unverified`).

## 확인하지 못한 것

- **Enter 키는 `:active` 를 발동시키지 않는다.** 같은 방법으로 쟀더니
  `false` 였다. Space 와 다르다. 브라우저 동작이지 이 변경의 결함이 아니다.
  링크형 버튼(`<a class="btn-sian">`)은 Space 로도 활성화되지 않아 키보드
  눌림 피드백이 구조적으로 없다.
- Firefox, Safari — 이 환경에 Chrome 만 있다.
- **WKWebView(데스크톱 셸)** — 데스크톱 배포 전에 사람이 직접 확인해야
  한다.
- 색각 이상 시뮬레이션 — 도구 없음.

## 이연

- 짧게 톡 누르면 전이 중간값이 스친다. 눌림에만 `transition-duration: 0s`
  를 주는 것은 선택 사항이다.
- `.frequent-tags__chip`, `.undo-snackbar__action` 은 호버만 있고 눌림이
  없다.
- 이 파일의 인터랙티브 전이가 `prefers-reduced-motion` 으로 가드되지
  않는다. 이번에 생긴 문제가 아니다.
