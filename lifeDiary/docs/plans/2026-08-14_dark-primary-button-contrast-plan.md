# 다크 테마 기본 버튼 대비 수정 계획

2026-08-14. `docs/plans/2026-08-13_hover-state-restoration-plan.md` 의 이연
작업에서 넘어온 건이다.

## 문제

다크 테마에서 초록 배경 위 흰 글자가 대비 기준을 못 넘는다.

| 테마 | 평상 | 호버 |
|---|---|---|
| 라이트 | `#2C6E4A` 6.11:1 | `#235B3C` 7.98:1 |
| 다크 | `#4aa66d` **3.01:1** | `#5cb87e` **2.44:1** |

본문 기준은 4.5:1. 버튼 라벨은 13.5px / weight 600 이라 큰 글씨(3:1)
예외에 해당하지 않는다. 세 역할(Web Experience Designer, Browser
Interaction Reviewer, Quality Verification Lead)이 각자 계산해 같은 값이
나왔다.

호버가 평상보다 **더 나쁘다**. 색이 밝아지는 것과 글자 대비가 오르는 것은
다른 축이다.

## 사용자 결정

> 초록 유지 글자만 반전

브랜드 초록(`--color-primary`, `--color-primary-hover`)은 그대로 두고,
다크 테마에서만 버튼 글자를 짙은 색으로 바꾼다.

## 근거 — 후보별 대비 실측

브라우저에서 WCAG 상대휘도로 계산했다.

| 글자색 | 평상 `#4aa66d` | 호버 `#5cb87e` |
|---|---|---|
| `#ffffff` (현재) | 3.01 | 2.44 |
| **`#14211A`** (라이트 `--color-text`) | **5.52** | **6.82** |
| `#0F1A14` | 5.91 | 7.31 |
| `#4C5B52` | 2.38 | 2.94 |

`#14211A` 를 쓴다. 이미 라이트 테마 `--color-text` 로 저장소에 있는 값이라
새 색을 만들지 않고, 두 상태 모두 기준을 넘긴다. `#0F1A14` 가 조금 더
높지만 저장소에 없는 값이다.

## 승인 범위

`apps/core/static/core/css/style.css` 한 파일.

신규 토큰 `--color-ink-on-primary` 를 만든다.

- `:root` — `#ffffff`
- `[data-theme="dark"]` — `#14211A`

적용 대상은 초록 배경 위에 글자가 놓이는 규칙뿐이다.

| 행 | 규칙 | 현재 |
|---|---|---|
| 371 | `.btn-sian--primary` | `color: #fff` |
| 377 | `.btn-sian--primary:where(:not(:disabled)):hover` | `color: #fff` |
| 1976 | `.btn-primary` (Bootstrap) | 색 미선언, Bootstrap 기본 `#fff` |
| 1981 | `.btn-primary:hover` | 색 미선언 |

## 추가 승인 범위 — 눌림 상태 (2026-08-14 사용자 결정)

대비 수정을 검증하다가 부트스트랩 `.btn-primary` 가 키보드 포커스와 눌림에서
배경을 **부트스트랩 파랑**(`rgb(11,94,215)`)으로 바꾸는 것을 실제 Tab 키로
확인했다.

사용자가 "이벤트 발생 표시를 위해 만든 것 아니냐" 고 물었고, 의도가 아니라는
근거 셋을 확인했다.

1. 저장소 CSS 어디에도 파랑 리터럴이 없다(`#0b5ed7`, `#0d6efd`, `#0a58ca`
   전부 0건). 부트스트랩 기본값이다.
2. `.btn-primary` 와 `.btn-primary:hover` 는 **일부러 초록으로 덮어 놨다.**
   눌림만 안 덮었다. 같은 커밋에 `btn-outline-primary` 를 `!important` 로
   강제한 흔적도 있다.
3. `style.css` 전체에 `:active` 규칙이 **0개** 다.

즉 눌림 피드백은 설계된 적이 없고, 부트스트랩 클래스를 쓴 4곳에서만 우연히
파랑으로 나타난다. `.btn-sian` 계열 18곳 이상에는 아예 없다.

사용자 결정:

> 1번으로 해보자

1번 = 초록 계열 눌림 상태를 만든다. 브랜드를 유지하면서 눌림 피드백을
주고, `.btn-sian` 계열에도 함께 적용한다.

### 이 확장이 어려운 이유

- 부트스트랩의 `.btn:first-child:active` 와 `:not(.btn-check) + .btn:active`
  는 (0,3,0) 이다. `style.css` 의 `.btn-primary` 는 (0,1,0) 이라 진다.
- 라이트에서 호버는 더 어두워지고 다크에서 호버는 더 밝아진다. 눌림이
  "호버보다 한 단계 더" 라면 방향이 테마마다 반대다.
- 바로 앞 작업에서 `:not(:disabled)` 가 특정도를 올려 회귀 3건을 냈다.
  같은 실수를 반복하면 안 된다.

설계는 두 리뷰어에게 맡겼다. 결과는 아래 `Frontend Review Evidence` 에
기록한다.

## 명시적 제외

- `--color-primary`, `--color-primary-hover` 값을 바꾸지 않는다. 사용자가
  초록 유지를 지정했다.
- `--color-primary-soft` 배경(11곳)은 손대지 않는다. 옅은 배경이라 기존
  글자색으로 이미 대비가 나온다.
- `.onboarding__tick.is-done`(698)은 초록 배경이지만 글자가 없다.
- `.btn-primary:hover` 의 `transform: translateY(-1px)` 는 별개 이연 건이라
  건드리지 않는다.

## 수용 기준

1. 다크 테마 `.btn-sian--primary` 평상 대비가 4.5:1 이상이다.
2. 다크 테마 `.btn-sian--primary` 호버 대비가 4.5:1 이상이다.
3. 라이트 테마 대비가 지금(6.11 / 7.98)에서 내려가지 않는다.
4. 다크 테마 `.btn-primary`(Bootstrap 계열)도 같은 기준을 넘는다.
5. 초록 배경색이 두 상태 모두 바뀌지 않는다.
6. 비활성 가드(`:where(:not(:disabled))`)가 그대로 작동한다.
7. `--color-primary-soft` 를 쓰는 옅은 배경 컴포넌트의 글자색이 바뀌지
   않는다.

## Activated Roles

- Web Experience Designer (색 결정과 토큰 이름)
- Browser Interaction Reviewer (상태별 적용 누락 점검)
- Frontend Implementation Engineer (구현)

## Not Activated

- 백엔드 역할 — 백엔드 변경 없음
- Security Resilience Reviewer — 신뢰 경계 변경 없음
- Deployment Operations Reviewer — 배포 변경 없음

## Frontend Review Evidence

### 리뷰 깊이와 근거

`Standard`. 전역 토큰을 하나 추가하지만 적용 대상이 4개 규칙으로 좁고,
색 결정은 사용자가 이미 내렸다. 다만 다크 테마 전 화면의 주 버튼이 바뀌므로
누락 점검이 필요하다.

### Web Experience Designer 구현 전 명세

**대비 수정.** 신규 토큰은 `--color-ink-on-primary` 가 아니라
**`--ink-on-primary`** 로 한다. 저장소에 이미 `--ink-on-accent` 가 있어
"강조 배경 위 잉크" 계열은 `--color-` 접두 없이 쓰는 관례가 서 있다.

값은 `#14211A` 가 아니라 **`var(--ink-on-accent)`** 를 참조한다. 36행
주석이 "시안의 `#14211A` 는 투자·주도적 색에서 4.5:1 에 못 미쳐 한 단계
낮췄다" 고 기록한다 — 이 저장소가 **이미 같은 문제를 겪고 버린 값**이다.
참조하면 새 리터럴도 안 늘고 대비도 더 높다(5.91/7.31 대 5.52/6.82).

다크에서 초록 위 짙은 글자가 어색하지 않은 근거: `.slot-block`(1387행)이
이미 `--ink-on-accent` 를 쓴다. 사용자가 매일 보는 기록 그리드가 같은
언어다. 라이트와 다크의 초록은 명암 관계가 아니라 서로 다른 색이므로
(`#2C6E4A` 대 `#4aa66d`) 각자 자기 명도에 맞는 글자를 받는 것이 정상이다.

**눌림 상태.** 호버가 라이트에서 어두워지고 다크에서 밝아지는 방향을 눌림이
한 단계 더 이어간다. HSL 명도 델타를 한 번 더 적용해
`--color-primary-press` 를 라이트 `#1C462F`, 다크 `#75C392` 로 둔다.

중립 버튼(`.btn-sian`, `.stepper__btn`)은 `--color-primary-soft` 배경 +
`--color-primary` 테두리·글자를 쓴다. 이미 선택 상태에 쓰이는 어휘라 새
토큰이 필요 없다. `.btn-sian--danger` 는 `#50220E` 하드코드 — 형제 규칙이
하드코드인데 한 변형만 토큰화하지 않는다.

제외: `.slot-block`, `.tag-btn`, `.chip--pick`, `.category-picker__option`,
`.goal-card__header`. **누르면 이미 결과가 남기 때문이다** — 슬롯은 선택
표시, 칩은 체크, 목표 카드는 펼침. 눌림 색을 얹으면 곧 나타날 상태와 겹쳐
깜빡이거나 묻힌다.

### Browser Interaction Reviewer 구현 전 기준

`.btn-primary:active` 로는 **부트스트랩에 진다.** 부트스트랩의
`.btn:first-child:active` 와 `:not(.btn-check) + .btn:active` 는 (0,3,0)
이다. `.btn` 을 함께 적어 `.btn.btn-primary:active` (0,3,0) 로 동률을
만들고 소스 순서로 이겨야 한다. `style.css` 는 부트스트랩 뒤에 로드된다.

`:focus-visible` 도 같은 뿌리다. 함께 고치지 않으면 포커스는 파랑, 누르면
초록이 되는 부자연스러운 전환이 남는다.

`:active` 규칙은 대응하는 `:hover` 규칙 **뒤에** 선언해야 한다. 동률
특정도라 순서가 갈리고, 마우스로 누르는 중에는 눌림이 이겨야 한다.

`.btn.btn-primary:active` 에는 비활성 가드가 불필요하다 — `:active` 는
`:hover` 와 달리 비활성 컨트롤에서 브라우저가 활성화 시퀀스를 억제한다.
`.btn-sian` 계열은 기존 표기 관례를 위해 `:where(:not(:disabled))` 를
유지하되, 맨 `:not(:disabled)` 는 금지다(직전 작업의 회귀 원인).

`:active` 를 `@media (hover: hover)` 로 가두면 안 된다. 터치에서야말로
눌림 피드백이 필요하다.

### 계획한 브라우저 증거

라이트·다크 두 테마에서 `.btn-sian--primary` 와 `.btn-primary` 의 평상·호버
계산된 배경·글자색을 읽고 대비를 계산한다. 실제 마우스 호버로 잰다.

### 실제로 나온 브라우저 증거

**대비 수정** (실제 Tab 키, `/accounts/login/` 로그인 버튼):

| 다크 테마 | 전 | 후 |
|---|---|---|
| `.btn-sian--primary` 평상 | 3.01:1 | **5.91:1** |
| `.btn-sian--primary` 호버 | 2.44:1 | **7.31:1** |
| `.btn-sian--primary` 포커스 | — | 5.91:1, 배경 `rgb(74,166,109)` 초록 유지 |

라이트는 6.11 / 7.98 로 변화 없음. 초록 배경값 무변경.

**부트스트랩 파랑 제거** (실제 Tab 키,
`/accounts/username-recovery/` 제출 버튼):

| 테마 | 전 | 후 |
|---|---|---|
| 라이트 | 파랑 | `rgb(35,91,60)` 초록, 7.98:1 |
| 다크 | `rgb(11,94,215)` 파랑 | `rgb(92,184,126)` 초록, 7.31:1 |

**눌림 상태** (Space 키, CDP trusted event, 전이 제거 후):

| 항목 | 값 |
|---|---|
| `matches(':active')` | `true` |
| 배경 | `rgb(117,195,146)` = `--color-primary-press` 다크값 |
| 글자 | `rgb(15,26,20)` = `--ink-on-primary` 다크값 |
| 대비 | **8.47:1** |

캐스케이드 우위는 CSSOM 으로 확인했다. 부트스트랩 `.btn:first-child:active`
순번 557, `.btn.btn-primary:active` 순번 4764 — 동률 특정도에 뒤 순서.

**Enter 키는 `:active` 를 발동시키지 않는다.** 같은 방법으로 쟀더니
`matches(':active')` 가 `false` 이고 배경이 포커스색 그대로다. Space 와
다르다. 브라우저 동작이지 이 변경의 결함이 아니다.

### 구현 중 발견해 고친 결함

**키보드로 누르면 눌림색이 아니라 포커스색이 나왔다.** `:active` 를
`:focus-visible` 앞에 뒀는데 둘 다 (0,3,0) 동률이라 뒤가 이겼다. 키보드로
누르면 두 상태가 동시에 참이라 포커스가 눌림을 덮었다.

실측: `rAF` 시점 `active=true` 인데 배경 `rgb(92,184,126)`(포커스색),
기대값은 `rgb(117,195,146)`(눌림색).

세 곳의 순서를 뒤집었다. 다만 **실제 충돌은 `.btn.btn-primary` 한 곳뿐**
이었다 — `.btn-sian` 과 `.stepper__btn` 의 `:focus-visible` 은 `outline`
만 건드려 속성이 겹치지 않았다. 나머지 둘은 나중에 누가 `background` 를
추가해도 재발하지 않도록 방어적으로 맞춘 것이다.

이 결함은 "실측 못 한다"로 넘어갈 뻔했다. Browser Interaction Reviewer 가
대안 검증을 요구해 다시 시도한 끝에 잡혔다.

### 구현 후 판정

**Web Experience Designer — Conforms.** 자기 명세의 오류를 인정했다:
`.btn-primary:active` 로 충분하다는 근거("호버가 이미 그렇게 이긴다")는
호버에서만 참이고, 부트스트랩 눌림은 특정도가 한 단계 높다.
`.btn.btn-primary` 로의 정정과 `:focus-visible` 추가를 설계에 받아들였다.
`.btn-sian--primary:hover` 의 `border-color: transparent` 도 필수임을
확인했다 — 아무도 선언하지 않으면 기본 호버의 연두 테두리가 경쟁 없이
적용된다.

**Browser Interaction Reviewer — Conforms** (Enter·Firefox·Safari·
WKWebView 는 Unverified). 파일을 다시 읽어 세 곳의 순서 역전과 토큰 값을
직접 확인했고, `#75C392` → `rgb(117,195,146)` 환산이 실측치와 일치함을
독립 계산했다. 짧게 톡 누를 때 전이 중간값이 스치는 것은 0.15s 이징을 쓰는
모든 UI 의 정상 동작이며 상태 무결성 문제가 아니라고 판정했다 — 눌림에만
`transition-duration: 0s` 를 주는 것은 선택 사항이다.

### Quality Verification Lead 완료 판단

이번 작업에서는 별도 활성화하지 않았다. 직전 호버 작업에서 이 역할이 지적한
두 블로커(다크 대비, 판정 부재) 중 대비 건이 곧 이 계획서의 대상이었고,
판정 부재는 위 절로 해소했다.

미확정 항목:

- Enter 키의 `:active` 미발동 — 브라우저 동작으로 확인됨. 링크형 버튼
  (`<a class="btn-sian">`)은 Space 로도 활성화되지 않아 키보드 눌림
  피드백이 구조적으로 없다. 별도 설계 논의가 필요하다.
- Firefox, Safari — 이 환경에 Chrome 만 있다.
- WKWebView(데스크톱 셸) — `desktop/launcher.py` 로 실제 앱을 띄워 사람이
  Tab+Space 로 확인해야 한다. **데스크톱 배포 전에 닫아야 한다.**
- 색각 이상 시뮬레이션 — 도구 없음.

## Domain Boundary and Dependency Direction

프레젠테이션 계층 단독. 템플릿·JavaScript·백엔드 무변경.

## Coupling and Cohesion Review

토큰 하나로 "초록 위 글자색" 결정을 한곳에 모은다. 지금은 `#fff` 가 두
규칙에 하드코드돼 있고 Bootstrap 기본값에도 흩어져 있다. 토큰화하면
다음에 브랜드색이 바뀔 때 한 곳만 고치면 된다.

## 검증 명령과 기대 증거

```
conda run -n knou-life-diary python manage.py collectstatic --noinput
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary pytest
```

CSS 변경이라 테스트 수는 497 그대로여야 한다. 실질 증거는 브라우저 대비
실측이다.

## 이연 작업

- `.btn-primary:hover` 의 `transform: translateY(-1px)` 와
  `prefers-reduced-motion` 부재.
- `--color-primary-soft` 배경 11곳의 글자 대비는 이번에 재지 않았다.
