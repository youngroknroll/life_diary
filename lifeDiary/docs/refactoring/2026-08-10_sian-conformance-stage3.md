# 시안 정합 재작업 3단계 실행 로그

계획: `docs/plans/2026-08-10_sian-conformance-remediation-plan.md`
범위: D3 · A4 · A2 (+ 발견해서 함께 고친 카테고리 순서)

## 한 것

### D3 태그 이름 10자 (사용자 결정)

`Tag.name` `max_length` 50 → 10. 설명이 필요한 경우는 기록 저장 시의 메모로
갈음한다.

`name_limit.shorten_tag_name()` 은 절삭 후 같은 사용자 안에서 겹치면 꼬리
숫자를 붙인다. 앞 10자가 같은 두 이름을 그냥 자르면 `unique_user_tag_name`
제약이 깨진다. dev 데이터에는 10자 초과가 1건, 충돌 0건이었지만 운영
데이터는 알 수 없어 방어한다.

마이그레이션 `0011_tag_name_max_10`. 되돌리면 열 길이만 돌아가고 잘린 이름은
복원되지 않는다 — 역방향에 명시해 두었다.

### A4 새 태그 모달 (시안 7b)

- 필드 순서를 카테고리 → 이름에서 **이름 → 카테고리**로. 사람은 이름을 붙인
  뒤 분류한다
- 카테고리를 `<select>` 에서 **다섯 개의 네이티브 라디오**로. 방향키 이동과
  탭 정지 하나를 브라우저가 처리한다. div 로 흉내 내면 roving tabindex 를
  직접 만들어야 하고 그게 흔한 회귀 원인이다
- 라디오는 `opacity:0` + 1px 로 감춘다. `display:none` 이면 키보드로도 못 고른다
- 제목 "새 태그", 부제, 버튼 "태그 만들기". 수정 모드는 "태그 수정"/"저장"
- 이름 `maxlength="10"` + "최대 10자" 도움말
- 미리보기 칩이 이름 입력과 카테고리 선택 양쪽에 반응한다

### A2 설정 재구성 (시안 5c·6b)

섹션 순서를 시안대로 바꿨다 — **목표 시간(최상단) → 태그와 카테고리 →
표시 · 계정(2단)**. 이전에는 목표가 세 번째였고 추가 폼과 목록이 좌우로
갈려 있었다.

- 목표 추가는 별도 화면이 아니라 목록 아래에서 펼친다. 서버가 오류와 함께
  폼을 돌려주면 접지 않는다
- 태그와 카테고리 섹션이 5색 범례와 실제 태그 칩을 직접 보여 준다
- 계정 섹션 신설 — 아이디 · 비밀번호 변경 · 로그아웃(좁은 화면) · 회원 탈퇴
- 하단 단독 "계정 탈퇴" 카드를 없앴다. 15일 유예 안내는 탈퇴 확인 페이지에
  이미 같은 내용이 있어 **이전이 아니라 중복 제거**다(확인함)

칩을 눌러 편집하는 건 태그 관리 재작성(A1, 7단계)이 있어야 성립하므로,
그때까지 `태그 관리 ›` 보조 링크를 남긴다. 잠정 이탈로 기록한다.

### 카테고리 순서 (계획에 없던 발견)

모달을 브라우저에서 확인하다 잡았다. 시안 7a·7b 는 **투자 → 주도적 → 수동적
→ 기초 → 수면** 순인데 DB `display_order` 는 정반대(수동적이 먼저)였다.
자기통제력이 높은 쪽에서 낮은 쪽으로 읽는 배열이라 순서 자체가 의미다.

`Category.Meta.ordering` 이 `display_order` 라 이 값 하나가 카테고리를
나열하는 모든 화면(7a 설명, 7b 모달, 설정 범례)을 바꾼다.
마이그레이션 `0012_sian_category_order`.

## 잡은 결함

**모달을 Escape 로 닫으면 포커스가 `<body>` 로 떨어졌다.** 모달을
`data-bs-toggle` 이 아니라 JS 로 열어 Bootstrap 이 트리거를 모른다. 여는
시점의 `activeElement` 를 기억했다가 `hidden.bs.modal` 에서 돌려준다.

**목표 추가 패널을 열 때 포커스가 움직이지 않았다.**
`querySelector('select, input')` 가 CSRF 히든 입력을 먼저 잡아 `focus()` 가
조용히 실패했다. `input:not([type=hidden])` 으로 좁혔다.

## 기존 테스트 정리

카테고리 순서와 모달 문구가 바뀌면서 9건이 깨졌다. 전부 **의도한 계약 변경**의
결과였고, 실제 회귀는 없었다.

| 테스트 | 조치 |
|---|---|
| `TestCategoryRepository::test_find_all` | 첫 카테고리 기대값을 시안 순서로 |
| `TestSeedCategory::test_display_order` | 순서 기대값을 시안 순서로 |
| `TestTagRepositoryCategory::...ordered_groups...` | 같음 |
| `TestDashboardIndexRendering::...correct_category` | 그룹 순서만 뒤집고 그룹핑 검증은 유지 |
| `TestTagsEnglish::test_tags_index_renders_english` | 새 문구로 |
| `TestTagsEnglish::test_tags_modal_labels_english` | 새 문구로 |
| `TestMypageEnglish::test_mypage_renders_english` | "Account deletion" 섹션이 사라져 "Tags and categories" 로 |
| `TestHomePageEnglish::...javascript_catalog...` | 제거된 "Select a category" 대신 새 문구로 |
| `TestTagModalTemplate::test_category_select_has_readable_font_size_class` | **삭제** |

마지막 건은 템플릿과 CSS의 **소스 문자열을 읽어 검사**하는 테스트였다.
`AGENTS.md` 프론트엔드 정책이 금지하는 유형이고 "미러링하는 코드가 교체되면
삭제하라"고 명시돼 있다. 대상인 `<select>` 가 라디오로 바뀌어 삭제했고,
고아가 된 `.tag-category-select` CSS 규칙도 같이 지웠다.

## i18n 누락

영문 설정 화면에 한국어가 남아 있었다. 새로 만든 문구의 영어 번역이
비어 있었기 때문이다.

- `회원 탈퇴` 가 빈 msgstr → 영문 페이지에 한국어 노출
- `태그와 카테고리` 가 "Tag category guide"(설명 화면 문구)로 잘못 붙어 있었다
- `탈퇴 진행` 의 "Continue" 는 파괴적 동작 문구로 모호해 "Continue to delete" 로

## 검증

| 검사 | 결과 |
|---|---|
| 태그 이름 제한 | RED → GREEN **7/7** |
| `manage.py check` | 0 issues |
| 마이그레이션 드리프트 | No changes detected |
| `msgfmt --check-format` | django · djangojs, ko · en 전부 통과 |
| `node --check` | `tag.js` · `goals.js` 통과 |

브라우저 (360px) —

- 모달: 제목 "새 태그", 부제 일치, 버튼 "태그 만들기", `maxlength=10`,
  네이티브 라디오 5개, `<select>` 없음
- 카테고리 순서 `투자시간 · 주도적 사용시간 · 수동적 소비시간 · 기초 생활시간
  · 수면시간` — 시안과 일치
- 이름 필드에서 **Tab 한 번**에 라디오 그룹으로 (탭 정지 하나)
- **방향키만으로** 선택이 따라가고 색 미리보기가 즉시 갱신 (클릭 불필요)
- Escape 로 닫으면 포커스가 트리거 버튼으로 복귀
- 설정: 섹션 순서 `목표 시간 · 태그와 카테고리 · 표시 · 계정`,
  범례 5색, 목표 패널 기본 접힘, 열면 첫 필드로 포커스, 닫으면 토글로 복귀,
  좁은 화면에서 로그아웃 행 노출, 가로 스크롤 없음
- 설정 화면에서도 태그 모달이 열리고 카테고리 5개가 채워짐

## i18n

`makemessages` 가 또 오역을 물려줬다. 이번에도 **플래그를 걷기 전에 내용을
확인**해서 잡았다.

- `이름` → "이동" / "Commuting"
- `필수` → "터치:" / "Touch:"
- `최대 10자까지 입력 가능` → "최대 50자까지 입력 가능"
- `새 태그` → "새 태그 생성", `저장` → "저장중..."

`django.po` 와 `djangojs.po` 양쪽을 갱신했다. 모달 문구는 JS 카탈로그
소관이라 `-d djangojs` 를 따로 돌려야 한다.

## 남긴 것

- 태그 칩 클릭 편집은 A1(7단계) 이후
- 카탈로그 빈 항목(법적 고지 등)은 이 작업 이전부터의 백로그
