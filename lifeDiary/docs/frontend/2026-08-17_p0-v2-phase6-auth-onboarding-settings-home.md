# P0 v2 6단계 — 인증 · 온보딩 · 설정 · 홈

계획: `docs/plans/2026-08-16_p0-v2-handoff-plan.md` 6단계 (§6, 목업 4d–4f·1e).
브랜치: `feat/p0-v2-handoff`.

## 진행 방식 — 병렬 서브에이전트

사용자 지시로 팀 방식으로 전환했다. Agent Teams는 이 환경에서 비활성(env 미설정)이라
병렬 서브에이전트 3개로 진행했다. 파일 소유권을 영역별로 분리하고, **모든 에이전트가
공유하는 `style.css`와 `locale/**/*.po`는 리드가 직렬로 반영**해 read-modify-write
경합을 원천 차단했다.

| 에이전트 | 소유 파일 |
|---|---|
| 인증·온보딩 | `login.html`, `signup.html`, `welcome.html`, `auth-enhance.js` |
| 설정 | `mypage.html`, `base.html`의 테마 IIFE만 |
| 홈 | `templates/index.html`, `apps/core/tests.py` |

**Wave 1(읽기 전용)**에서 각자 현재 상태 감사 + WED 스펙 + BIR 기준 + 편집 목록을
만들게 했다. 이것이 AGENTS.md의 프런트엔드 이중 리뷰 게이트가 요구하는 구현 전
산출물이다. **Wave 2**에서 사용자 결정을 전달하고 각자 템플릿을 구현하게 했다.

### Wave 1이 밝혀낸 것 — 스펙의 "현재 상태" 기술이 대부분 낡았다

- **온보딩은 이미 3단계 전부 구현돼 있었다.** 진행 점, STEP 라벨, 카테고리 칩(44px,
  스와치 opacity .35), 50px CTA까지 전부. 스펙이 지시한 "welcome.html 삭제"는 불필요.
  남은 건 카피 2건과 가이드 링크뿐이었다.
- **비밀번호 강도 위젯도 이미 있었다.** `aria-live="polite"`까지. 팔레트만 어긋나 있었다.
- **상단바 언어·테마 이동도 이미 끝나 있었다.** `base.html` 내비에 둘 다 없었다.
- **`.settings-row`는 이미 3개 화면에서 쓰이는 확립된 패턴**이었다(신규 도입 아님).
- **계정 삭제용 `danger-panel` 모달은 존재하지 않는다.** 스펙의 "기존 모달 유지"는
  구현 불가능한 기술이었다 — 실제로는 전용 페이지다.

## 사용자 결정 3건

1. **홈 가이드 링크**: `tags:category_guide`가 `@login_required`라 비로그인 방문자가
   로그인 벽에 부딪히는 문제 → **로그인 사용자에게만 링크 노출**(백엔드 무변경).
2. **설정 범위**: 시안 4f를 따르되 **로그아웃 행은 유지**. 767px 아래에서 상단바
   드롭다운이 접히므로 지우면 모바일에 로그아웃 수단이 사라진다.
3. **홈 예시 그리드**: 시안대로 18행 예시 그리드와 "오늘의 한 줄" **삭제**.

## 구현 요약

- **인증(4d)**: H1 카피 교체, 우측 정렬 비밀번호 찾기 행 신설, 주 CTA 50px,
  **FontAwesome 구글 아이콘 → 모노 "G" 마크**(금지 요소 제거, `#2563eb` 호버 규칙 삭제),
  푸터 재구성(무료로 시작 강조 + 아이디 찾기 약화). `auth-enhance.js`의 눈 아이콘·
  캡스락 화살표도 텍스트로 교체. 로그인 상태 유지와 아이디 찾기는 유지(결정).
- **온보딩(4e)**: 카운터 "N개 선택됨", 가이드 링크 신설, CTA "다음 — 하루 채워 보기".
- **설정(4f)**: 560px 단일 카드로 전면 재작성. 화면(테마 3값 라디오 세그먼트 / 언어)·
  기록 설정(태그·목표·메모, 개수 + chevron)·계정(비밀번호·로그아웃·삭제) 3그룹.
  테마 IIFE를 2값 토글 → 3값으로 교체.
- **홈(1e)**: 469 → 285줄. PNG 2장·확대 모달·언어 분기·18행 그리드·로컬 버튼 CSS·
  FA 아이콘 7개 제거, 2열 그리드 + "이렇게 씁니다" 3박스 + 5개 카테고리 행 신설.

### 테마 3값의 "시스템" = localStorage 키 부재

설정 에이전트의 판단을 채택했다. `base.html` 최상단 FOUC 방지 스크립트가
`saved || (prefersDark ? 'dark' : 'light')`로 계산하므로, `'system'`을 저장하면
`data-theme="system"`이 되어 어떤 규칙과도 매칭되지 않는다. 키를 지우면 그 스크립트를
**한 줄도 건드리지 않고** 동작하며, 기존 사용자의 저장 상태와도 그대로 호환된다.
실측 결과 시스템 선택 시 키가 삭제되고 OS 설정(다크)을 따라갔다.

## 리드가 브라우저 실측으로 잡은 결함 5건

에이전트들은 서버를 띄우지 않으므로(제약) 실행 시점 결함은 전부 리드가 잡았다.

1. **홈 H1이 단어 중간에서 줄바꿈**("기/록하세요"). 한글은 기본값이면 아무 데서나
   끊긴다 → `word-break: keep-all`.
2. **가입 화면 비밀번호 규칙이 두 번 렌더**. 코드 출처는 한 곳뿐이었고, 원인은
   **ko 카탈로그의 msgstr에 본문이 두 번 들어가 있던 것**(과거 잘못된 identity 번역).
   마크업이 아니라 데이터 결함이었다.
3. **약관 동의 링크가 부트스트랩 기본 파란색**(`#0d6efd`) → 팔레트 토큰으로 덮음.
4. **캡스락 경고가 정의되지 않은 `--color-warning` 토큰에 의존**해 `#d97706`로 폴백.
   토큰이 없으니 다크 오버라이드까지 따로 있었다 → `--color-danger-text`로 통일하고
   다크 오버라이드 삭제.
5. **여러 줄 `{# #}` 주석 2개가 설정 화면에 그대로 출력**. Django의 `{# #}`는 한 줄
   주석이다. 이번 세션에서 두 번째로 나온 같은 실수라, 전 템플릿을 스캔해 0건을 확인했다.

## i18n — fuzzy 함정이 전부 실재했다

세 에이전트 모두 "유사 문자열 오상속"을 경고했고, 실제로 6건이 났다. 그중:

- **`화면` → `"Tue"`** — 요일 '화'(Tuesday)의 번역을 물려받았다. 설정 화면 첫 섹션
  라벨이 영어에서 "Tue"로 나올 뻔했다.
- `이렇게 씁니다` → "Here is how it will look"
- `비밀번호를 잊으셨나요?` → "Enter the password you want to use."
- `특이사항 메모` → "Note:", `%(n)s개` → "%(n)s selected", `%(n)s개 선택됨` → 부분 상속

여기에 **이전부터 잘못 들어가 있던 영어 번역 3건**도 함께 고쳤다(에이전트들이 발견):
`어제 기록이 그대로 기다리고 있습니다.` → "No records to delete.",
`아이디와 비밀번호만 있으면…` → "You can now sign in with your new password.",
`설정된 목표가 없습니다` → "No tags yet."

최종적으로 **4개 카탈로그(ko/en × django/djangojs) 모두 빈 msgstr 0건, fuzzy 0건**.

## 삭제한 테스트

전부 마크업·CSS 문자열을 검사하던 것으로, AGENTS.md 프런트엔드 정책에 따라 고치지
않고 지웠다.

| 테스트 | 이유 |
|---|---|
| `test_home_page_uses_{korean,english}_tag_usage_guide…` (2건) | 삭제된 PNG 경로를 검사 |
| `test_login_page_google_button_has_blue_hover_style` | **CSS 규칙 텍스트**와 금지된 `#2563eb`를 고정 |
| `TestMypageEnglish` (2 메서드) | 4f가 걷어낸 목표 폼·태그 카드 마크업을 검사. 커버리지는 `TestUserGoalFormEnglish`·`TestUserNoteEnglish`가 이미 담당 |
| `test_home_page_presents_…`의 모달 assertion 2줄 | 삭제된 모달 id를 검사 |

인증 에이전트는 i18n 테스트에서 **assertion 줄만 지우고 메서드는 남겼다** — 주변의
한글 누출 가드는 살아 있는 계약이라 함께 지우면 안 된다는 판단이었고, 타당하다.

## 검증

- `conda run -n knou-life-diary pytest -q`(전체) — **exit 0**. 인증 에이전트가 보고한
  영어 로그인 테스트 실패(신규 문자열 미번역으로 인한 한글 누출)는 리드의 카탈로그
  작업으로 해소됐다.
- `manage.py check` 클린, 마이그레이션 드리프트 없음, `node --check` 통과.
- i18n: 4개 카탈로그 `msgfmt --check-format` 통과, `compilemessages` 통과,
  `gettext()`로 ko/en 직접 조회 확인, 영어 홈·로그인 렌더에서 한글 누출 0건.
- 팔레트 밖 색 **0건**(`#2563eb`·`#dc2626`·`#d97706`·`#059669` 및 다크 변형 전부 제거).
- 브라우저 실측(격리 임시 SQLite + `runserver 8765`, 종료 후 임시 DB·설정·`.cache/` 삭제):

| 화면 | 확인 |
|---|---|
| 홈(1280px) | 2열 그리드, 카테고리 5행 순서·색, 3박스, CTA `.btn-sian`, PNG·모달 0 |
| 홈(비로그인/로그인) | 가이드 링크 각각 숨김/노출, href `/tags/categories/`, 44px |
| 홈(500px) | 1열 붕괴, 가로 넘침 없음, CTA 44px |
| 홈 H1 | `word-break: keep-all` 후 어절 단위로 끊김 |
| 로그인 | 새 카피, 44px 필드, 우측 비밀번호 찾기, 50px CTA, "G" 마크(파란색 0) |
| 가입 | 규칙 1회 렌더, 동의 링크 primary 색, 강도 위젯 팔레트 |
| 온보딩 STEP1 | 진행점, STEP 라벨, 칩 그룹, "6개 선택됨", 가이드 링크, 새 CTA |
| 설정(1280px) | 3그룹, 개수·chevron, 48px 행, 계정 삭제 danger, 로그아웃 데스크톱 숨김 |
| 설정(400px) | 테마 3분할 전폭, 언어 스택, 로그아웃 행 노출 |
| 테마 3값 | 라이트/다크 → 키 저장, 시스템 → **키 삭제 + OS 추종**(실측) |
| 영어 | 홈·로그인에서 한글 누출 0 |

## Frontend Review Evidence — 판정

- **Web Experience Designer**: Conforms — 4d·4e·4f·1e 네 화면 모두 시안 구조와 일치.
  의도된 이탈 2건: 설정의 로그아웃 행 유지(모바일 로그아웃 경로 보존), 홈 가이드
  링크의 인증 조건부 노출(로그인 벽 회피). 둘 다 사용자 결정.
- **Browser Interaction Reviewer**: Conforms — 테마 라디오 그룹이 `role="radiogroup"`
  + `aria-label`로 접근 가능한 이름을 갖고 네이티브 라디오라 방향키 순회가 보장됨,
  `clip-path` 숨김이라 포커스 유지, 언어 `onchange` 자동 제출 키보드 트랩을 적용
  버튼으로 해소, 44px/48px 타깃 확인. **Unverified**: 스크린리더 실통과(VoiceOver
  "3의 3" 안내)와 실제 포인터 하드웨어 경로는 미확인.
- **Quality Verification Lead**: 완료로 판정 — 전체 테스트 통과, 발견 결함 5건 전부
  수정 후 재검증, 잔여 Unverified는 이 트랙 수용 기준의 핵심이 아님.

## Deferred

- **`category_guide`의 `@login_required` 제거** — 시안대로 비로그인에게도 링크를
  보이려면 필요. 백엔드 변경이라 Backend TDD 사이클 + 보안 검토 필요. 트리거: 공개
  콘텐츠 페이지 단계. 그 뷰의 breadcrumb도 로그인 가드라 함께 손봐야 한다.
- **mypage 목표 편집 백엔드 고아화** — `views.py`의 mypage POST 분기,
  `mypage_goals_partial`, 그 URL이 UI에서 도달 불가가 됐다. 삭제는 Backend TDD
  사이클. `goals.js` 파일 자체는 `usergoal_form.html`이 계속 쓰므로 삭제 금지.
  `GetMyPageUseCase`는 개수 표시에 goals가 필요하므로 반환을 유지해야 한다.
- **`.segmented__item` ~28px** — 프로젝트 44px 규칙 미달이나 분석 탭과 동일한
  저장소 전역 값이라 함께 올려야 한다.
- **`utils.js`의 `showOverlay(..., 'fa-sign-in-alt')`** — 공유 인프라라 이번 범위 밖.
  FontAwesome을 프로젝트 전역에서 걷을 때 함께.
- **`tag_usage_guide{,_en}.png` (약 2.1MB)** — 저장소 전체에서 참조 0건이 됐다.
  삭제 여부는 사용자 판단.
- **죽은 CSS** — `.home-daygrid*`(홈 그리드 삭제로), `.navbar-utility-controls`·
  `.navbar-language-form`·`.navbar-language-select`·`.theme-toggle` 및 480px 미디어
  블록. 별도 CSS 정리 트랙에서 처리 권장.
- **온보딩 칩의 3번째 상태**(추천-흐림) — 뷰/모델의 "추천" 신호가 필요해 백엔드 변경.
