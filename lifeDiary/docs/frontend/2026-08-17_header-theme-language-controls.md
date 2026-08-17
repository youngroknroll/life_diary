# 헤더 테마·언어 컨트롤 고정 (2026-08-17)

## 배경
테마와 언어 선택이 `users/mypage.html`(로그인 필수) 안에만 있어서 비로그인 사용자는
둘 다 바꿀 수 없었다. 사용자 지시로 두 컨트롤을 브랜드 이름 옆 헤더로 옮겨 모든
방문자에게 고정 노출한다.

## 변경
- `templates/shared/_nav_prefs.html` (신규): 테마 3값 드롭다운(라이트·다크·시스템),
  언어 드롭다운(`set_language` POST 폼 + `next`=현재 전체 경로).
  언어 이름은 `get_language_info_list`의 `name_local` — `get_available_languages`는
  이름에 gettext를 걸어 ko 화면에서 "English"가 "영어"로 보였다.
- `templates/base.html`: 브랜드 직후 partial include(인증 분기 밖). 테마 스크립트를
  `#themeChoice` 라디오 그룹 대신 `#themeMenu` 드롭다운 기준으로 다시 씀 —
  선택 표시(`aria-checked`), 버튼 아이콘(해/달) 갱신, 시스템 선택 시 OS 변경 즉시 반영.
- `apps/users/templates/users/mypage.html`: 화면 그룹(테마·언어 행) 제거.
- `apps/core/static/core/css/style.css`: `.app-nav__prefs`, `.app-nav__pref*` 추가.
  탭이 접히는 768px 아래에서도 아바타가 오른쪽에 남도록 `.app-nav__account`에
  `margin-left:auto`. 설정 페이지 전용으로 남은 `.settings-lang`, `.settings-select`,
  `.settings-row--stack` 규칙 제거.
- 회원가입 문구(같은 세션 지시): "30초면 됩니다" + 리드 문장 → "환영합니다. 처음 뵙네요".
  `locale/{ko,en}` 카탈로그 교체 후 재컴파일.

## 시스템 자동 반영
- 테마: `localStorage.theme`가 없으면 `prefers-color-scheme`를 따른다(기존 FOUC
  스크립트 유지). 브라우저 다크/라이트 전환을 실측으로 확인.
- 언어: `LocaleMiddleware`가 `django_language` 쿠키 → `Accept-Language` 순으로
  해석한다. 영어 브라우저는 별도 조작 없이 영어로 렌더된다.

## 검증
- 전체 pytest 543 passed (5분 24초), `manage.py check` 이슈 0
- 렌더 확인: `Accept-Language: en` → 헤더 `EN`/`Language`, `ko` → `KO`/`언어 선택`
- 브라우저(Chrome DevTools MCP) 실측
  - 1280px 비로그인: 브랜드 → 테마 → KO, 로그인/무료로 시작 우측 유지
  - 1280px 로그인(테스트 DB 렌더): 브랜드 → 테마 → KO → 탭 4개, 아바타 우측
  - 390px 로그인: 가로 오버플로 0, 아바타 우측 정렬 유지
  - 테마: 시스템 → 라이트 클릭 시 `data-theme` 즉시 전환, `localStorage.theme=light`;
    시스템 선택 후 OS 다크 전환 시 리로드 없이 dark + 달 아이콘
  - 언어: 비로그인 상태에서 영어 전환 성공, 회원가입 페이지에서 전환해도 경로 유지
  - 콘솔 error/warn 0건
- i18n: `msgfmt --check-format` 통과, 컴파일된 en 카탈로그에 신규 문구 반영 확인

## 후속 수정 — 모바일 비로그인 진입점 (사용자 지시)
`.app-nav__tabs--guest`가 `.app-nav__tabs`를 함께 달고 있어 768px 아래 숨김 규칙에
걸렸고, 게스트에게는 하단 탭바도 없어 헤더에 로그인·가입 진입점이 남지 않았다.
모바일에서 게스트 그룹만 다시 노출하고, 320px 한 줄에 들어가도록 좁은 폭(575.98px
아래)에서 상단바를 압축했다.

- `.app-nav__tabs--guest { display: flex }`(767.98px 아래)
- 575.98px 아래: `.app-nav__inner` 간격 12px → 8px, 테마·언어 버튼 폭 36px → 32px,
  게스트 링크·CTA 12px 글자 + `white-space: nowrap`
- 줄바꿈을 막은 이유: 320px에서 "무료로 시작"이 3줄로 접혀 버튼이 56px 헤더 밖으로
  자랐다
- 실측(가로 오버플로 0, 헤더 높이 56px 유지): 320px ko·en, 375px ko·en 비로그인,
  375px 로그인(아바타 우측 유지), 700px 비로그인, 1280px 로그인 — 압축은 576px
  아래에만 걸려 데스크톱 배치는 그대로

## 발견 사항 (이번 범위 밖, 수정하지 않음)
- `.segmented__radio*` 규칙은 이번 삭제로 사용처가 없어졌지만 재사용 가능한
  컴포넌트라 남겨 두었다.
- 언어에는 테마의 "시스템"에 해당하는 자동 항목이 없다. 사용자 결정으로 한국어·영어
  두 개만 두고, 쿠키를 지우는 자동 항목은 넣지 않는다.
