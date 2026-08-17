# Life Diary P0 구현 명세 v2 — 이식 계획

## 배경

Claude Design 프로젝트("Life Diary 웹앱 UI 리디자인")에서 두 문서를 가져왔다.

1. `Life Diary P0 구현 명세 v2.dc.html` — 1차 명세(2026-07) 대비 "남은 작업만" 담은 핸드오프
   문서. §1 차트 전면 정리, §2 category_stats 집계, §3 입력정보 패널, §4 segmented+목표
   진행 바, §5 폰트·크롬, §6 인증·온보딩·설정·홈 여섯 영역과 §7 작업 순서·검증표, §8 미결정
   항목을 포함한다.
2. `Life Diary 반영 점검 시안.dc.html` — 위 명세가 옵션 번호(1a–1e, 2a–2f, 4a–4g)로 가리키는
   실제 화면 목업. 디자인 토큰(색·타이포·간격), 정확한 클래스명·수치를 담고 있다.

가장 큰 격차는 화면 마크업이 이미 새 디자인 언어(토큰 체계·24×6 그리드·요약 탭 등, 1차
명세 반영 완료 항목)로 가 있는데 `stats.js`의 차트 4개만 Chart.js 기본값 그대로 남아 있는
것이다.

## 조사로 확정한 사실

- **차트(§1)**: `apps/stats/static/stats/js/stats.js`(312줄)는 태그 단위 데이터셋만 그리고,
  `applyChartTheme` 없음, `drawEmptyState`가 `Arial`/`#6c757d` 하드코딩, 범례는 Chart.js
  네이티브. 카테고리 딥 라인 색상은 어디에도 없음 — 완전 재작성 대상.
- **집계(§2)**: `apps/stats/aggregation/{weekly,monthly,daily}.py`에 `category_stats` 키
  없음. `Tag.category` FK(`apps/tags/models.py:78`)가 이미 있어 카테고리 롤업 자체는
  어렵지 않다. 카테고리 pastel(fill) 토큰은 `style.css`에 이미 존재, 딥(line) 변형은 신규.
- **입력 패널(§3)**: `apps/dashboard/templates/dashboard/index.html`(271줄)이 스펙이 지목한
  FA 아이콘·card-header·btn-sm·alert 구조 그대로. `.quick-input-sheet` CSS는
  `style.css:1866-1945`.
- **분석 화면(§4)**: `apps/stats/templates/stats/index.html`(462줄)이 `card > card-header >
  nav-tabs`로 감싸여 있음(교체 대상). `.goal-card`/`.segmented` CSS는 존재하지만 어떤
  템플릿에서도 쓰이지 않음 — 목표 진행 바는 실질적으로 신규 구현.
- **폰트·크롬(§5)**: `style.css`의 `--font-body`가 이미 `'Pretendard Variable'`을 1순위로
  선언하고 있었지만 self-host 파일이 없어 시스템 폰트로 폴백되고 있었다(주석: "웹폰트 CDN
  미탑재"). `static/core/fonts/` 없음, `showLoadingOverlay`는 즉시 호출(지연 없음).
- **인증(§6-4d)**: `login.html`은 이미 `auth-panel` 단일 카드 + `btn-sian` Google 버튼 —
  스펙이 "미반영"이라 부르는 것보다 실제로는 더 진행돼 있음. 남은 차이는 카피와
  FontAwesome 아이콘(스펙이 금지) 교체 정도.
- **온보딩(§6-4e)**: `welcome.html`이 이미 `?step=1/2/3` 3단계 전체를 담고, 가입 시 바로
  이 뷰로 리다이렉트한다. 스펙 §8 미결정 #3("welcome.html 삭제 필요성")은 이 조사로 해소 —
  삭제·리다이렉트 변경 불필요, 칩 상태·카피만 갱신.

## 목업에서 확정한 디자인 토큰

카테고리 5색(면=기존 `--color-accent-*`, 선=신규 딥 변형):

| 카테고리 | key | 면(fill) | 선(line, 신규) |
|---|---|---|---|
| 투자시간 | work | `--color-accent-work` `#7CD9A0` | `#4E8F63` |
| 주도적 사용시간 | move | `--color-accent-move` `#7DCFE8` | `#4F8B9E` |
| 수동적 소비 | care | `--color-accent-care` `#FFA98C` | `#C1715A` |
| 기초 생활 | life | `--color-accent-rest` `#FFD166` | `#B9C2BA` |
| 수면 | sleep | `--color-accent-sleep` `#B8A6F0` | `#8A9A91` |

다크 모드는 pastel 원본이 곧 선 색(cssToken 헬퍼가 자동 대응). 기초(life) 선은 목업 렌더링
기준 데스크톱·모바일 모두 기본 OFF로 채택(스펙 §8 미결정 #1, 시각 증거로 확정).

## 실행 방침

- 브랜치 `feat/p0-v2-handoff` 하나, 단계별 작은 커밋. PR/머지는 사용자 몫.
- 순서는 스펙 §7 그대로: ①폰트/오버레이/clamp → ②category_stats 집계 → ③stats.js 재작성 →
  ④segmented+목표 진행 바 → ⑤입력 패널→바텀시트 → ⑥인증/온보딩/설정/홈.
- 단계마다: 프런트 단계는 Web Experience Designer + Browser Interaction Reviewer의
  사전 산출물과 구현 후 `Conforms/Deviates/Unverified` 판정을 실제로 작성, 백엔드(②)는
  Backend TDD Coach의 Scenario별 Red-Green. 완료 후 `docs/frontend/` 또는
  `docs/refactoring/`에 작업 로그, `docs/project-status.md` 갱신.

## 공통 수용 기준 (스펙 §7)

44px 타깃, `--ink-on-accent`, 4.5:1 대비, `tabular-nums` + 차트: 면은 파스텔·선은 딥·다크는
파스텔 선, 화면 어디에도 Chart.js 기본 회색이 남지 않을 것.

## 단계별 작업 요약

각 단계의 상세 범위·Activated Roles·검증 항목은 해당 단계 작업 로그
(`docs/frontend/` 또는 `docs/refactoring/`)에 기록한다.

1. **폰트·오버레이·clamp**(§5, 목업 1d) — Pretendard Variable + IBM Plex Mono self-host,
   `showLoadingOverlay` 300ms 지연, `.home-title` 반응형 clamp.
2. **category_stats 집계**(§2, 목업 4g) — weekly/monthly에 카테고리 롤업 키 추가,
   daily의 `hourly_stats` 태그→카테고리 전환. 백엔드 TDD 사이클.
3. **stats.js 전면 재작성**(§1, 목업 1a·2a–2f) — 테마 동기화, 카테고리 5선, HTML 범례,
   목표선, DOM 빈 상태.
4. **분석 화면 segmented+목표 진행 바**(§4, 목업 1c·4b·4c) — 카드 래핑 제거, 목표 진행 바
   신설, 내보내기 행 모바일 레이아웃.
5. **입력 패널→바텀시트**(§3, 목업 1b·4a) — 데스크톱 패널 재구성, 모바일 바텀시트 내용물
   교체, 태그 이미지 모달 삭제.
6. **인증·온보딩·설정·홈**(§6, 목업 4d–4f·1e) — 로그인 카피/아이콘, 온보딩 칩 상태, 설정
   행 그룹 재구성, 홈 버튼·가이드 컴포넌트 정리.

## Deferred

- 목업 1a의 라이트 모드 라인 아래 `opacity:.07` 영역 채우기 — 스펙 본문에 명시 없음,
  장식적 요소로 판단해 이번 트랙에서 구현하지 않음.
- `.auth-split` CSS(죽은 코드, 어떤 템플릿도 참조하지 않음) — 실제 삭제 작업 없음, 별도
  CSS 정리 트랙에서 처리.
- Pretendard는 동적 서브셋 없이 전체 Variable woff2(2.0MB)를 그대로 배포한다. 서브셋
  빌드 파이프라인은 이번 트랙 범위 밖 — 필요성이 확인되면 별도 트랙으로 처리.
