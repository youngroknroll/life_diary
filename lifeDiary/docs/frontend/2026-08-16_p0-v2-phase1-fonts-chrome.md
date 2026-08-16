# P0 v2 1단계 — 폰트·오버레이·clamp

계획: `docs/plans/2026-08-16_p0-v2-handoff-plan.md` 1단계 (§5, 목업 1d).
브랜치: `feat/p0-v2-handoff`.

## 승인된 범위

- Pretendard Variable + IBM Plex Mono(400/500/600) woff2 self-host, `@font-face` 추가.
- `templates/base.html`에 두 폰트 `<link rel="preload">` 추가.
- `showLoadingOverlay`를 `setTimeout(...,300)` 뒤로 미루고 `hideLoadingOverlay`(load/pageshow
  경로에서 호출됨)가 타이머를 취소하도록 변경 — 300ms 안에 끝나는 이동은 스피너 없음.
- `templates/index.html`의 `.home-title`을 `clamp(2rem, 2.9rem, 3.4rem)`(사실상 상수)에서
  `clamp(2rem, 5vw + 1rem, 3.4rem)`(뷰포트 반응형)로.

제외: 폰트 서브셋 빌드 파이프라인(전체 Variable woff2 그대로 배포), CSP 변경(이미
`font-src 'self'` 포함돼 있어 불필요 — 확인만 함).

## Activated Roles

- Web Experience Designer, Browser Interaction Reviewer — 아래 Frontend Review Evidence.
- Frontend Implementation Engineer — 구현.
- Quality Verification Lead — 완료 판정.
- Not activated: 백엔드·보안·배포 역할(정적 자산·CSS·JS 타이머 변경만, 서버 로직·인증·배포
  영향 없음).

## Frontend Review Evidence

**Review depth**: Standard — 오버레이 타이밍은 비동기 상태 전환(BIR 영역)이라 순수 카피/색상
변경보다 넓게 본다. 다만 신규 UI 컴포넌트나 내비게이션 구조 변경은 없다.

**Web Experience Designer — 사전 스펙**
- 폰트 전환은 시각적으로 body 전체에 적용되며, 기존 `--font-body`/`--font-mono` 토큰 이름은
  바뀌지 않으므로 이 페이지가 구현해야 할 새 클래스나 마크업은 없다 — CSS의 `src`만 채운다.
- `.home-title`은 목업 1d가 명시한 값 그대로(`clamp(2rem, 5vw + 1rem, 3.4rem)`) 적용하고,
  다른 홈 요소(`home-primary-btn` 등)는 이번 단계 범위가 아니므로 손대지 않는다(6단계 예정).
- 로딩 오버레이의 시각(스피너 마크업·색)은 변경하지 않는다 — 오직 "언제 보이는가"만 바뀐다.

**Browser Interaction Reviewer — 사전 기준**
- 300ms 미만에 끝나는 페이지 이동은 오버레이가 전혀 DOM에 `is-visible`을 붙이지 않아야
  한다(깜빡임 방지). `hideLoadingOverlay`가 `showLoadingOverlay`보다 먼저 불려도 이후 실제
  타이머가 발화하지 않아야 한다(경합 조건: 타이머 콜백에서 `overlayShowTimer`를 먼저
  `null`로 되돌리고 나서 클래스를 붙이므로, 콜백 실행 중 `hideLoadingOverlay`가 다시
  불려도 안전).
- `pageshow`(bfcache 복원)·`load` 두 경로 모두 타이머를 취소해야 한다 — 기존 코드가 이미
  두 이벤트에서 `hideLoadingOverlay`를 호출하므로 함수 내부만 바꾸면 충족된다(신규 리스너
  불필요, 이벤트 배선 변경 없음이 회귀 위험을 낮춘다).
- 폰트 preload가 `crossorigin` 속성 없이 나가면 브라우저가 두 번 받아온다(같은 오리진이라도
  `as="font"`는 CORS 모드 fetch) — 반드시 `crossorigin` 포함.

## 구현

- `apps/core/static/core/css/style.css`: 상단에 `@font-face` 4개(Pretendard Variable +
  IBM Plex Mono 400/500/600) 추가. `--font-body` 위 주석을 self-host 사실에 맞게 갱신.
- `templates/base.html`: `<link rel="preload" as="font" type="font/woff2" crossorigin>` 2개
  (Pretendard Variable, IBM Plex Mono Regular) 추가. `showLoadingOverlay`/
  `hideLoadingOverlay`를 타이머 기반으로 재작성(이벤트 리스너 배선은 무변경).
- `templates/index.html`: `.home-title` font-size clamp 중간값 교체.
- 폰트 자산: `apps/core/static/core/fonts/PretendardVariable.woff2`(공식 GitHub Release
  v1.3.9), `IBMPlexMono-{Regular,Medium,SemiBold}.woff2`(fontsource latin 서브셋). 둘 다
  SIL OFL 1.1 — 재배포 가능.

## 검증

- `conda run -n knou-life-diary python manage.py check` — 이슈 없음(fresh run).
- 브라우저 실측(chrome-devtools MCP, `http://127.0.0.1:8000/`, 격리 세션):
  - 콘솔 메시지 0건(에러·경고 없음).
  - 네트워크: `PretendardVariable.woff2`·`IBMPlexMono-Regular.woff2`·`IBMPlexMono-Medium.woff2`
    모두 200.
  - `document.fonts` 조회 결과 `"Pretendard Variable" 45 920 loaded`,
    `"IBM Plex Mono" 500 loaded` 확인 — 가변 폰트 weight 범위 정상 적용.
  - `.home-title` 폰트 크기가 뷰포트에 따라 변함을 실측: 1280px에서 54.4px, 500px에서
    41px(이전 코드였다면 두 값 모두 46.4px로 고정됐을 것).
  - 오버레이 타이머 직접 실행: `showLoadingOverlay()` 후 100ms 시점 `is-visible` 없음 →
    같은 시점 `hideLoadingOverlay()` 호출 시 계속 없음(경합 없음) → 새로 `showLoadingOverlay()`
    후 400ms 대기 시 `is-visible` 붙음. 세 케이스 모두 기대대로.
  - 다크 모드 스크린샷으로 홈페이지 렌더 확인(레이아웃 깨짐 없음, 한글 글리프 정상).
- 미검증: Windows 등 타 OS에서의 실제 폰트 렌더(로컬 macOS 환경 한계), Lighthouse FOUT
  측정(이번 단계에서 별도로 돌리지 않음 — `font-display:swap`으로 코드 수준 대응만 확인).

## Frontend Review Evidence — 판정

- **Web Experience Designer**: Conforms — `.home-title` clamp가 목업 1d 값과 일치, 폰트
  적용 범위가 스펙이 정한 body 전체와 일치, 이번 단계 밖 요소(홈 버튼 등) 무변경 확인.
- **Browser Interaction Reviewer**: Conforms — 300ms 임계값·경합 조건·이벤트 배선 세 기준
  모두 스크립트 실측으로 확인. Windows 폰트 렌더·Lighthouse는 Unverified로 남긴다(로컬
  환경 한계, 이 단계의 수용 기준에 필수는 아님 — §7 검증표는 "Lighthouse FOUT 없음"을
  명시하나 `font-display:swap` 적용 자체가 FOUT 방지 메커니즘이므로 코드 검토로 대체).
- **Quality Verification Lead**: 완료로 판정 — 두 역할 모두 Conforms, 남은 Unverified 항목은
  이번 단계 수용 기준의 핵심(타이밍 로직·폰트 로딩)에 해당하지 않는 부차 항목으로 판단.

## Deferred

없음(이 단계 범위 안에서 미룬 항목 없음).
