# 클릭 가능 요소의 호버 상태 복구 계획

2026-08-13 사용자 보고로 시작한다.

> 큰 오류를 발견. 모든 클릭 이벤트가 발생되는 곳들은 사용자가 지금 커서가
> 어디에 있는지 명시적으로 알 수 있도록 애니메이션 hover효과가 필수인데 ui
> 리디자인하면서 빠진것 같다. 공용 css를 확인해서 이 부분을 수정 및 최적화.

## 확인된 결손

브라우저에서 파싱된 스타일시트와 `rg` 결과가 일치한다.

| 항목 | 값 |
|---|---|
| `style.css` 전체 `:hover` 규칙 | 15 |
| `transition` 선언 | 8 (대부분 시트·스낵바 전용) |
| `:active` 규칙 | 0 |
| `.btn-sian` 템플릿 사용 | 35 |
| `.btn-sian` 호버 규칙 | 0 |
| `.btn-sian` 전이 시간 (브라우저 실측) | `0s` |

기존 호버 15개 중 13개는 base 선택자에 `transition` 이 없어 즉시 튄다. 즉
"애니메이션이 없다"는 신고는 부분적으로 이미 있던 호버에도 해당한다.

### 신고에 없었지만 더 심각한 것

`.slot-block` — 하루 24×6 기록 그리드. `dashboard.js:664` 가 슬롯마다
`role="button" tabindex="0"` 를 붙이는데 `:hover` 도 `:focus-visible` 도
0개다. 제품 1순위 루프이고, 키보드 사용자는 지금 어느 칸에 있는지 알 방법이
없다.

`.btn-tag-legend` — `tag_ui.py:26` 이 만들고 `dashboard.js:1010` 이
`selectTag()` 에 연결하는 버튼인데 `style.css` 에 규칙이 0개다.

## 승인 범위

`apps/core/static/core/css/style.css` 한 파일만 바꾼다. 템플릿·JS 무변경.

호버·포커스를 **추가할** 대상:

| 우선 | 대상 | 변화 |
|---|---|---|
| 1 | `.btn-sian`, `.btn-sian--danger` | 배경·테두리 |
| 2 | `.slot-block` | inset 링만, `:focus-visible` 신규 |
| 3 | `.btn-tag-legend`, `.tag-btn` | 링 / 배경·테두리 |
| 4 | `.chip--pick`, `.category-picker__option`, `.stepper__btn`, `.goal-card__header`, `.app-nav__tab`, `.breadcrumb-trail a` | 배경·테두리·색 |
| 5 | 기존 호버 6개 | `transition` 만 추가 |

## 명시적 제외

호버를 **주지 않는다**: `.summary-tile`, `.data-table` 행·셀,
`.observation`, 바탕 `.chip`, `.tag-totals__row`, `.card`,
`#tagFormPreviewChip`, `.settings-row`, `.tag-row`.

전부 클릭 핸들러·`href`·`tabindex` 가 없다. 호버는 "누를 수 있다"는 약속이라
표시 전용에 붙이면 오조작을 부른다. `style.css:2726` 에 이미 "읽기 전용
예시다 — 클릭 핸들러도 tabindex 도 붙이지 않는다" 고 적혀 있다.

`cursor: pointer` 를 추가하지 않는다. Bootstrap Reboot 가
`button:not(:disabled)`, `[type=submit]:not(:disabled)`, `[role="button"]` 에
이미 넣는다. 브라우저에서 `#statsExportBtn` 과 `a.btn-sian` 모두 `pointer`
로 실측했다.

`.theme-toggle` 와 `#statsTabs .nav-link` 는 자체 `transition` 이 있어
손대지 않는다. `.auth-card .auth-google-login` 은 `.btn-sian` 을 겸하므로
물려받는다.

`.btn-primary:hover` 의 `transform: translateY(-1px)` 는 이번 범위 밖이다
(이연 작업 참조).

## 수용 기준

1. `.btn-sian` 기본형 위에서 배경이 `--color-surface-soft`, 테두리가
   `--color-primary-border` 로 0.15초에 걸쳐 바뀐다. `--primary`·`--danger`
   변형은 각자 색을 유지한다.
2. 기록 그리드 슬롯 위에서 **태그색 배경은 그대로**, inset 링만 나타난다.
   10분 눈금(`background-image`)이 유지된다.
3. 슬롯에 Tab 으로 포커스를 옮기면 outline 이 보인다.
4. 터치 시뮬레이션에서 탭 후 슬롯·범례 호버가 고착되지 않는다.
5. `#statsExportBtn` 이 제출 후 4초간 `disabled` 인 동안 호버가 먹지 않는다.
6. 온보딩 STEP1 에서 체크된 칩의 선택 표시가 호버로 깨지지 않는다.
7. 바탕 `.chip` 에 아무 변화가 없다.
8. 중립 표면 호버는 다크 테마에서 밝아지는 방향으로 바뀐다. 단색
   `.btn-sian--danger` 는 브랜드색이라 두 테마 공통으로 어두워진다
   (Web Experience Designer 명세, 아래 참조).
9. `transition: all` 과 `transform` 을 쓰지 않는다.

## Activated Roles

- Web Experience Designer (호버 시각 언어)
- Browser Interaction Reviewer (호버·포커스·터치·비활성 규칙)
- Frontend Implementation Engineer (구현)

## Not Activated

- Backend TDD Coach, Backend Integration Engineer — 백엔드 변경 없음
- Security Resilience Reviewer — 신뢰 경계 변경 없음
- Deployment Operations Reviewer — 배포·마이그레이션 변경 없음

## Frontend Review Evidence

### 리뷰 깊이와 근거

`High`. 전역 공용 CSS 를 바꾸고 대시보드·태그·통계·마이페이지·온보딩·인증
전 화면이 함께 움직인다. 저장소 전역 패턴 점검과 브라우저 증거가 필요하다.

### Web Experience Designer 구현 전 명세

호버 언어는 **신규 토큰 없이** 기존 것을 재사용한다.

- 중립 테두리 컨트롤(`.btn-sian`, `.tag-btn`, `.stepper__btn`,
  `.goal-card__header`, `.app-nav__tab`): 배경 `--color-surface-soft`,
  테두리 `--color-primary-border`. 라이트 `#F5F6F4`/`#98c7aa`, 다크
  `#232a26`/`#3a6b4a` 로 이미 정의돼 있어 다크 전용 블록이 필요 없다.
- 골라내기(`.chip--pick`, `.category-picker__option`): 기존 선택 표시
  (`--color-primary-soft` + inset 링)와 겹치면 "이미 선택됨"으로 오독되므로
  더 옅게 쓰고 `:not(:has(...:checked))` 로 분리한다.
- 인라인 배경 요소(`.slot-block`, `.btn-tag-legend`): 태그색이
  `style.backgroundColor` 로 박혀 있어 배경을 건드리면 색 식별이 깨진다.
  `box-shadow` 링만 쓴다. 슬롯은 기존 `.day-row__selection .is-selected` 와
  같은 값(`0 0 0 1.5px var(--color-primary) inset`)을 써서 호버가 선택
  프리뷰와 시각적으로 일치하게 한다.
- `.btn-sian--danger`: 배경 `#8A3A18` 이 토큰이 아니므로 같은 방식으로
  `#6d2f13` 하드코드.

전이 시간은 `0.15s` 로 통일한다. `#statsTabs .nav-link:hover` 가 이미 쓰는
값이다. `0.18s`~`0.24s` 는 시트·스낵바 열고닫기 전용이라 건드리지 않는다.

`transform` 을 쓰지 않으므로 `prefers-reduced-motion` 신규 블록이 불필요하다.

### Browser Interaction Reviewer 구현 전 기준

- 새 호버는 `:focus-visible` 과 짝을 이룬다. `.btn-sian` 은 현재 색 변화도
  아웃라인도 없어 키보드 사용자가 아무것도 못 얻는다. 기존 아웃라인 전용
  `:focus-visible` 규칙(`.stepper__btn`, `.goal-card__header`,
  `.category-picker__option`)은 그대로 둔다.
- `<button>` 을 쓰는 `.btn-sian` 계열은 `:not(:disabled)` 로 가둔다.
  `stats.js:298` 이 `#statsExportBtn` 을 4초간 비활성으로 만들고,
  `utils.js:116` 의 `setButtonLoading` 과 `goals.js:62` 도 같은 일을 한다.
  가드가 없으면 못 누르는 버튼이 누를 수 있다고 거짓말한다.
- `.slot-block` 과 `.btn-tag-legend` 만 `@media (hover: hover) and
  (pointer: fine)` 로 감싼다. 같은 화면에서 반복 탭이 일어나는 표면이라 iOS
  Safari 의 호버 고착에 가장 취약하다. 나머지는 탭 즉시 화면이 전환된다.
- 전이 목록은 명시한다. `transition: all` 금지.

### 계획한 브라우저 증거

1280px·360px, 라이트·다크에서:

- `.btn-sian` 호버 전후 배경·테두리·전이 시간 실측
- 슬롯 호버 시 `background-image`(눈금) 유지 확인
- 슬롯 Tab 포커스 시 outline 확인
- 비활성 `#statsExportBtn` 호버 시 무변화 확인
- 바탕 `.chip` 무변화 확인
- 추가된 `:hover` 규칙 수와 `transition` 선언 수를 파싱해 집계

### 실제로 나온 브라우저 증거

집계 (Chrome CSSOM 파싱): `:hover` 15 → 25, `transition` 8 → 24. 금지
대상 위반 0건, 바탕 `.chip` 위반 0건.

1280px 라이트, 실제 마우스 호버:

| 대상 | 값 |
|---|---|
| primary 호버 배경 | `rgb(35,91,60)` = `--color-primary-hover` `#235B3C` |
| primary 호버 글자 / 테두리 | `rgb(255,255,255)` / `rgba(0,0,0,0)` |
| danger 호버 배경 / 글자 / 대비 | `rgb(109,47,19)` / `rgb(255,255,255)` / **10.16:1** |
| 빈 슬롯 호버 그림자 | `rgb(44,110,74) 0 0 0 1.5px inset` |
| 빈 슬롯 비호버 그림자 | `rgb(237,239,235) 0 0 0 1px inset` |
| 빈 슬롯 10분 눈금 | 호버 중 `backgroundImage !== 'none'` 유지 |
| 비활성 `.btn-sian` 호버 | `matches(':hover')` true, 배경 불변, `cursor: default` |
| 비활성 primary 호버 | 배경 `rgb(44,110,74)` 평상색 유지 |
| `.btn-sian` 포커스 | `outline: rgb(44,110,74) solid 2px`, offset 2px |

온보딩 STEP1 (`/accounts/welcome/`):

| 칩 | 배경 | 테두리 |
|---|---|---|
| 미체크 + 호버 | `rgb(245,246,244)` | `rgb(152,199,170)` |
| 체크됨 + 호버 | `rgb(237,243,238)` | 투명 |
| 체크됨 + 비호버 | `rgb(237,243,238)` | 투명 |

터치 에뮬(390x844 DPR 3): `(hover:hover) and (pointer:fine)` = `false` →
슬롯·범례 호버 미발동.

다크 테마: `--color-surface` `#1a1f1c` → `--color-surface-soft` `#232a26`
(밝아지는 방향). 중립 버튼 배경 `rgb(26,31,28)`, 테두리 `rgb(58,74,62)`.

### 구현 중 발견해 고친 회귀 3건

계획서의 전제 하나가 틀려서 생겼다 — "`.btn-sian--primary:hover` 는 소스
순서상 뒤에 있어 자동으로 이긴다" 는 **특정도가 같을 때만** 참이다.
`:not(:disabled)` 가 특정도를 (0,2,0) 에서 (0,3,0) 으로 올렸다.

1. **(High)** primary 버튼이 호버 시 배경 `rgb(245,246,244)` 거의 흰색,
   글자 `rgb(20,33,26)` 으로 바뀌었다. 초록 버튼이 회색이 됐다.
2. **(High)** danger 버튼 글자가 흰색에서 짙은색으로 바뀌어 **대비
   1.64:1**. 계정 삭제 버튼이 읽히지 않았다.
3. **(Medium)** `.slot-block:hover`(0,2,0) 가 `.slot-block.is-empty`(0,2,0)
   보다 소스 순서상 앞이라 졌다. 기록 없는 날은 144칸 전부가 `is-empty` 다.

고친 방법: `:not(:disabled)` → `:where(:not(:disabled))` (특정도 0),
변형 호버가 필요한 속성을 전부 선언, 슬롯 미디어 블록을 `.is-empty` 뒤로
이동(특정도는 올리지 않음).

### 리뷰어가 잡아 추가로 고친 것

두 리뷰어가 독립적으로 같은 결함을 지적했다.

- `.btn-sian--primary:hover` 에만 비활성 가드가 없었다. `base.html` 의 전역
  제출 핸들러가 `setButtonLoading` 으로 이 클래스 버튼을 비활성으로 만드는데
  (로그인·회원가입·비밀번호 변경·목표 저장·태그 저장), 비활성 요소도
  `matches(':hover')` 가 `true` 라 호버가 발동했다. 가드를 추가했다.
- `.btn-sian:focus-visible` 이 없어 35곳이 브라우저 기본 링에만 의존했다.
  저장소가 이미 쓰는 아웃라인 패턴으로 채웠다.

### 구현 후 판정

**Web Experience Designer — Conforms.** 수용 기준 9개 전부 충족. 확인해 준
것: `.btn-sian--primary:hover` 에 덧붙인 `border-color: transparent` 는
필수다 — 그 속성을 아무도 선언하지 않으면 기본 호버의 연두 테두리가 경쟁
없이 적용돼 테두리 없는 단색 버튼의 설계와 어긋난다. 다크 primary 대비
문제는 이번 변경이 만든 것이 아님을 확인했다(`.btn-sian--primary` 는 승인
범위 12단계 목록에 없고, `--color-primary-hover` 는 다른 두 곳에서도 쓰이는
기존 토큰이다).

**Browser Interaction Reviewer — Conforms.** 1차 판정은 `Deviates` 였고
결함 2건(위 "리뷰어가 잡아 추가로 고친 것")을 지적했다. 둘 다 고친 뒤
파일을 다시 읽어 재판정했다. 확인해 준 것:

- `:where(:not(:disabled))` 가드가 네 곳으로 빠짐없이 채워졌다. 다섯 번째
  변형이 남아 있지 않다.
- `.btn-sian--primary:where(:not(:disabled)):hover`(376) 는 (0,2,0) 으로
  기본 호버(332)와 같고 소스 순서상 뒤라 여전히 이긴다.
- `.btn-sian:focus-visible`(338) 근처에 `outline: none` 이 새로 생기지
  않았다. 파일의 기존 `outline: none` 두 곳은 각자 `:focus-visible` 을
  갖고 있다.
- `:where()` 는 특정도 기여만 0 으로 만들고 비활성 요소에 매칭되지 않는
  성질은 그대로라 가드 의미가 약해지지 않는다.
- `.slot-block:focus-visible` 을 호버 게이트 밖에 둔 것도 옳다 — 게이트
  안에 넣으면 `pointer: coarse` 로 보고하면서 키보드를 쓰는 기기에서
  포커스 링이 사라진다.
- 수용 기준 5 의 취지(비활성 버튼은 호버 피드백을 보이지 않는다)가 이제
  `#statsExportBtn` 하나가 아니라 `.btn-sian` 계열 전체에서 성립한다.

대비 문제에 대한 정확한 표현을 남겨 준다: 호버가 평상보다 **더 나쁘다**
(2.44 대 3.01). 색이 밝아지는 것과 글자 대비가 오르는 것은 다른 축이라,
수용 기준 8 의 "밝아지는 방향" 은 만족하면서 대비는 반대로 간다.

### Quality Verification Lead 완료 판단

1차 판단은 **미완료**였고 막는 것이 둘이었다.

1. 다크 테마 `.btn-sian--primary` 대비. 평상 3.01:1, 호버 2.44:1 로 본문
   기준 4.5:1 미달. 평상부터 미달인 기존 토큰 문제지만 호버가 더 나쁘게
   만든다. `.btn-sian--primary` 는 16개 파일에서 쓰이는 앱의 주 CTA 다.
   토큰 변경은 이 계획서 범위를 넘으므로 **사용자 결정**이 필요하다.
2. 구현 후 판정 부재.

2 번은 두 리뷰어 모두 `Conforms` 를 내고 이 문서에 기록해 해소했다.
1 번은 이 계획서 범위 밖으로 확정하고 이연 작업에 남겼다 — 두 리뷰어
모두 이번 변경이 만든 문제가 아니며 이 계획서의 적합 판정을 막지 않는다고
판단했다. 사용자에게 올려 결정을 받는다.

통과 확인: 수용 기준 2·3·4·5·7·9, 파일 전체 특정도 함정 훑기(회귀 3의
패턴이 재발할 곳 없음), `:where()` 로 인한 의도치 않은 승자 없음, 선택
상태가 호버에 가려지는 컴포넌트 누락 없음(`.chip--pick`,
`.category-picker__option` 둘뿐이고 모두 가드됨).

## 대상 파일과 단계

`apps/core/static/core/css/style.css` 만 편집한다.

1. `.btn-sian`(313행)에 `transition` 추가, `:not(:disabled):hover` 신규
2. `.btn-sian--danger`(1268행) 뒤에 `:not(:disabled):hover` 신규
3. `.slot-block`(1339·1362행)에 `transition`, `:focus-visible` 신규,
   `@media (hover: hover) and (pointer: fine)` 안에 `:hover`
4. `.btn-tag-legend` 신규 규칙 (현재 0개)
5. `.tag-btn` / `.frequent-tags__chip`(1484행)
6. `.chip--pick`(739행) — `:not(:has(.chip__check:checked)):hover`
7. `.category-picker__option`(2870행) — 같은 방식
8. `.stepper__btn`(823행)
9. `.goal-card__header`(2172행)
10. `.app-nav__tab`(185행) 기존 `:hover` 에 배경 추가
11. `.breadcrumb-trail a`(1123행)
12. 기존 호버 6개에 `transition` 만 추가: `.tag-color-swatch`,
    `.settings-head__action`, `.undo-snackbar__action`,
    `.auth-card .password-toggle`,
    `[data-theme="dark"] .navbar .nav-link`,
    `[data-theme="dark"] .dropdown-item`

## Domain Boundary and Dependency Direction

프레젠테이션 계층 단독 변경이다. `views` → `use_cases` →
`repositories/domain_services` → `models` 흐름에 닿지 않는다. 템플릿과
JavaScript 도 바꾸지 않으므로 새 의존 방향이 생기지 않는다.

## Coupling and Cohesion Review

기존 클래스 선택자에만 상태 규칙을 더한다. 새 클래스·컴포넌트·토큰을 만들지
않아 결합도가 오르지 않는다. 호버 시각 언어가 `--color-surface-soft` /
`--color-primary-border` 두 토큰으로 모이므로 오히려 응집도가 오른다.

## 검증 명령과 기대 증거

```
conda run -n knou-life-diary python manage.py collectstatic --noinput
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary pytest
```

CSS 변경이므로 테스트 수는 그대로(497 passed)여야 한다. 실질 증거는 위
"계획한 브라우저 증거" 의 실측값이다.

## 이연 작업

- **다크 테마 기본 버튼 대비 미달.** `--color-primary` 계열을 흰 글자와
  대비 계산한 결과 다크에서 평상 `#4aa66d` **3.01:1**, 호버 `#5cb87e`
  **2.44:1** 로 본문 기준 4.5:1 을 못 넘는다(라이트는 6.11 / 7.98 로 통과).
  이번 변경 이전부터 있던 토큰 값 문제다 — `.btn-sian--primary:hover` 는
  기존 15개 호버 중 하나였고 이번에 `border-color: transparent` 만 더했다.
  고치려면 `--color-primary-hover` 토큰을 바꿔야 하는데 `.btn-primary:hover`
  와 텍스트 색 용도로도 쓰여 파급이 이 계획서 범위를 넘는다. 별도 건.
- `.btn-primary:hover` 의 `transform: translateY(-1px)`(1911행)는 저장소의
  다른 호버와 어긋나고 `prefers-reduced-motion` 가드도 없다. 별도 건.
- `prefers-reduced-motion` 블록이 `.undo-snackbar` 하나뿐이다.
  `.quick-input-sheet` 슬라이드업과 `.goal-card__chevron` 회전에 대체 경로가
  없다. 별도 건.
- `.tag-btn` 의 선택 상태(`.active`) 시각이 `style.css` 에 정의돼 있지 않다.
  이번 호버 결손과 별개의 결손. 별도 건.
- `.segmented` / `.segmented__item` 은 템플릿 사용처가 0건인 죽은 CSS.
  이번에 손대지 않는다.
- `setButtonLoading` / `resetButtonLoading`(`utils.js:113-129`)이 모든
  호출처에서 `disabled` 로 포커스를 떨어뜨리고 복구하지 않는다. 별도 건.
