# P0 v2 5단계 — 입력 패널 재구성과 모바일 바텀시트

계획: `docs/plans/2026-08-16_p0-v2-handoff-plan.md` 5단계 (§3, 목업 1b·4a).
브랜치: `feat/p0-v2-handoff`.

## 승인된 범위

- **데스크톱(1b)**: card-header + FA 아이콘 → `.section-title` 성격의 헤더, btn-sm 3종 →
  "사용법" 텍스트 링크 + 푸터의 "태그 관리" 링크, alert 도움말 → 접이식 안내 블록,
  선택 상태 박스(모노 시간 범위 + "N칸 선택"), 태그는 카테고리 그룹 아래 44px 칩
  (`.chip--pick` 재사용), 저장 버튼 라벨에 칸 수("N칸 저장").
- **모바일 바텀시트(4a)**: 기존 `.quick-input-sheet` 골격 유지, 내용물 교체. 80dvh,
  헤더(핸들 + 선택 범위)·저장 버튼 sticky, 태그 목록만 내부 스크롤. 백드롭 탭 = 닫기
  (선택 유지), 핸들 스와이프 다운 = 닫기. z-index 탭바 1030 < 백드롭 1035 < 시트 1040.
- `#usageHelp` 내용 축소, 태그 이미지 모달(`_tag_image_modal.html`) 삭제.

## Activated Roles

- Web Experience Designer, Browser Interaction Reviewer — 아래 Frontend Review Evidence.
- Frontend Implementation Engineer — 구현.
- Quality Verification Lead — 완료 판정.
- Not activated: 백엔드 역할(저장·삭제 API와 뷰는 무변경), 보안(권한·데이터 범위 불변).

## Frontend Review Evidence

**Review depth**: High — 모달성 시트의 포커스 관리, sticky 지오메트리, z-index 적층,
드래그 제스처, 배경 스크롤 잠금이 모두 걸린다. 저장소 전역 패턴 확인 포함.

**Web Experience Designer — 사전 스펙**
- 시트/패널은 카드 헤더 없이 `.quick-input-sheet` 자체가 표면을 갖는다(시안이 카드
  헤더를 금지). 헤더 = 선택 범위(모노) + 보조 라인, 우측에 "사용법" 텍스트 링크.
- 태그는 카테고리 그룹 아래 44px 칩. 선택된 칩만 스와치가 불투명, 나머지는 35%.
- "새 태그"는 점선 테두리 칩(`.chip--add`)으로 태그 목록과 구분한다.
- 저장은 시트의 유일한 주 CTA — 50px(다른 컨트롤 44px보다 크다).
- 푸터에 "태그 관리" 링크와 "저장 후 되돌리기 가능" 안내를 함께 둔다.

**Browser Interaction Reviewer — 사전 기준**
- 시트가 열리면 포커스가 시트 안으로 들어가고, 닫히면 **닫기 전에** 그리드로 돌아가야
  한다. 포커스가 시트 안에 남은 채 `aria-hidden`이 걸리면 ARIA 위반이다.
- 백드롭 탭으로 닫아도 선택은 유지돼야 한다(다시 열면 이어서 작업).
- 스와이프는 **핸들에서 시작한 제스처만** 반응해야 한다. 태그 목록 스크롤과 겹치면
  목록을 스크롤하려다 시트가 닫힌다.
- 시트가 열린 동안 배경은 스크롤되지 않아야 한다.
- 적층 순서가 탭바 < 백드롭 < 시트여야 한다. 하나라도 뒤집히면 탭바가 백드롭 위로
  떠서 시트 뒤의 탭이 눌린다.
- 모든 상호작용 타깃 44px 이상(주 CTA 50px).

## 구현

- `apps/dashboard/templates/dashboard/index.html`: 시트 마크업 전면 교체
  (`__handle`/`__header`/`__range`/`__body`/`__footer` 구조). `createNewTagBtn`을
  `#tagContainer` **밖** 형제로 배치 — `renderTagContainer()`가 CRUD 후 컨테이너
  안쪽만 다시 그리므로 안에 두면 리스너가 새 DOM 노드에 안 붙는다.
- `apps/dashboard/static/dashboard/js/dashboard.js`: `showSlotInfo` 재작성(모노 시간
  범위 + 메타 + 삭제 링크, 전부 `escapeHtml` 경유), `updateButtons`가 저장 라벨에 칸
  수를 넣도록, `renderTagButton`/`renderTagContainer`를 칩 마크업으로, 스와이프 닫기
  (`initQuickInputSheetSwipeToClose`) 신설, `manageTagsBtn` 핸들러 제거(푸터 링크로 대체).
- `apps/core/static/core/css/style.css`: 시트 컴포넌트 CSS 신설(데스크톱 패널 + 모바일
  시트 오버라이드), `.chip--add`, 백드롭 z-index 1030 → **1035**(시안 값).
- `apps/dashboard/templates/dashboard/_tag_image_modal.html` 삭제.
- `apps/dashboard/tests.py`: 삭제된 이미지 모달을 검사하던 테스트 2건과 그 전용 픽스처
  `dash_en_user_with_tags` 제거(마크업 문자열을 검사하던 테스트 — Frontend Work Policy에
  따라 고치지 않고 지운다).
- i18n: 신규/변경 문자열을 `django.po`·`djangojs.po` 양쪽에 반영.

## 브라우저 실측에서 찾아 고친 결함 4건

전부 유닛 테스트로는 잡히지 않는 실행 시점 결함이다.

1. **"새 태그" 칩이 가로 전체로 늘어남** — `.quick-input-sheet__body`가 flex column
   이라 직접 자식인 칩이 stretch됐다(322px). `.chip--add`에 `align-self: flex-start`
   추가 → 80px.
2. **선택된 칩의 스와치가 35%로 흐려짐** — `.chip--pick`이 두 상태 모델을 공유한다:
   온보딩은 숨은 체크박스, 시트는 `.active` 클래스. 체크박스가 없는 시트 칩에서
   `:not(:has(.chip__check:checked))`가 항상 참이 되어 선택된 칩까지 흐려졌다.
3. **(2를 고치자 드러난 대칭 결함) 온보딩의 체크된 칩도 35%** — 이번엔 내가 넣은
   `.chip--pick:not(.active)`가 `.active`를 안 쓰는 온보딩 칩에서 항상 참이 됐다.
   두 모델을 서로 새지 않게 격리했다: 온보딩 규칙은 `:has(.chip__check)`로, 시트
   규칙은 `.quick-input-sheet` 하위로 한정. 두 화면 모두 실측 재확인.
4. **저장 버튼이 50px이 아니라 44px** — 기존 모바일 규칙의 `.quick-input-sheet #saveBtn`
   id 선택자가 `.quick-input-sheet__save`의 50px를 특정도로 눌렀다. 그 규칙에서
   `#saveBtn`을 뺐다.
5. **ARIA 위반: 포커스가 시트 안에 있는 채 `aria-hidden` 적용** — 브라우저 콘솔이
   경고를 냈다. 원인은 저장·삭제 경로 모두 `clearSelection()`이 `closeQuickInputSheet()`
   **보다 먼저** 실행돼, 닫을 때 포커스를 되돌릴 슬롯이 이미 사라진 것.
   `closeQuickInputSheet` 안에는 "포커스를 옮긴 뒤 숨긴다"는 로직이 있었지만 되돌릴
   대상이 `null`이라 건너뛰었다. 두 호출부에서 닫기를 선택 해제보다 앞으로 옮겼다.
   부수 효과로 UX도 좋아진다 — 포커스가 방금 저장한 칸으로 돌아간다.
   **이 결함은 선존재였고, `test_mobile_sheet_close_moves_focus_before_hiding_dialog`가
   통과하고 있었다.** 그 테스트는 `closeQuickInputSheet` 함수 *안의 소스 순서*만
   검사해서, 실제 결함이 있던 *호출부 순서*를 보지 못했다. JS 소스 문자열 검사가
   왜 계약을 지켜주지 못하는지 보여주는 사례다(Frontend Work Policy의 근거).

## 검증

- `node --check apps/dashboard/static/dashboard/js/dashboard.js` — 통과.
- `conda run -n knou-life-diary python manage.py check` — 이슈 없음.
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run` —
  변경 없음.
- `conda run -n knou-life-diary pytest -q`(전체) — exit 0.
- i18n: `django.po`/`djangojs.po` ko·en 4개 파일에서 fuzzy 상속 오역을 발견해 수정
  (`사용법` ← `사용법:`, `태그가 없습니다. 아래에서 추가하세요.` ← 옛 `<br>` 문구,
  복수형 `%s칸 선택`/`%s칸 저장` 빈 msgstr). `msgfmt --check-format` 4개 전부 통과,
  `compilemessages` 통과, 헤더 외 fuzzy 0건.
- 브라우저 실측(chrome-devtools MCP, 격리 임시 SQLite + `runserver 8765`.
  종료 후 임시 DB·설정 모듈·`.cache/` 삭제):

| 항목 | 결과 |
|---|---|
| 데스크톱 패널(1280px) | card-header·FA 아이콘 0, 카테고리 그룹 칩, 점선 "새 태그" 80px, 저장 50px, `position: static`, 핸들·닫기·백드롭 숨김, `role` 해제 |
| 선택 상태 박스 | 5칸 드래그 → "14:00–14:50" (모노) + "5칸 선택 · 시간을 선택했어요…" |
| 저장 버튼 라벨 | 선택 없음 "저장" → 1칸 "1칸 저장" → 5칸 "5칸 저장" |
| 칩 상태 | 선택 칩 스와치 opacity 1 / 비선택 0.35, 높이 44px |
| 온보딩 칩(회귀 확인) | 체크 시 opacity 1·weight 600, 해제 시 0.35·400 |
| 시트 열림(키보드 Enter) | `is-open`, 백드롭 열림, `aria-modal="true"`, `aria-hidden="false"`, 포커스가 시트 첫 칩으로 진입 |
| 지오메트리(375px) | 시트 636px = 뷰포트 795px의 80%, 헤더 66 + 본문 462 + 푸터 94 + 핸들 = 시트 높이, 본문만 `overflow-y: auto`, 헤더 `position: sticky` |
| z-index 적층 | 탭바 1030 < 백드롭 1035 < 시트 1040 < 스낵바 1080 |
| 백드롭 탭 닫기 | 시트 닫힘, 배경 스크롤 잠금 해제, **선택 유지**("1칸 저장" 그대로), 포커스 그리드 복귀 |
| 스와이프 닫기 | 드래그 중 `translateY(100px)` 추적 → 릴리즈 시 닫힘, 인라인 transform 정리됨, 선택 유지 |
| 타깃 크기 | 칩 44 / 새 태그 44 / 저장 50 / 사용법 44 / 닫기 32 |
| 저장 → 스낵바 | 시트 닫힘, "1개의 슬롯이 저장되었습니다. 되돌리기", 탭바 위 배치, 슬롯 수 61→62 반영 |
| 포커스(저장 후) | 시트 밖, 방금 저장한 그리드 칸에 위치, 콘솔 경고 0 |
| 콘솔 | 최종 상태 오류·경고 0 |

## Frontend Review Evidence — 판정

- **Web Experience Designer**: Conforms — 카드 헤더 없는 표면, 카테고리 칩 그룹,
  점선 새 태그 칩, 50px 주 CTA, 푸터 링크·안내 모두 확인.
- **Browser Interaction Reviewer**: Conforms — 사전 기준 6개(포커스 진입/복귀, 백드롭
  닫기의 선택 유지, 핸들 한정 스와이프, 배경 스크롤 잠금, 적층 순서, 타깃 크기) 전부
  실측. 사전 기준이 "닫기 전에 포커스를 옮길 것"을 명시했기 때문에 선존재 ARIA 위반을
  잡아낼 수 있었다. **닫기 버튼 32px는 44px 규칙 미달** — 시안 4a가 32px로 명시한
  값이고 WCAG 2.5.8 AA(24×24)는 통과하므로 의도된 예외로 수용하되 아래 Deferred에 남긴다.
- **Quality Verification Lead**: 완료로 판정 — 두 역할 Conforms, 발견한 결함 5건 전부
  수정 후 재검증. 잔여 예외(닫기 32px)는 시안 명시값이라 수용.

## Deferred

- 시트 닫기 버튼 32px — 시안 명시값이나 프로젝트 44px 규칙과 어긋난다. 44px 규칙을
  전역으로 재확인할 때 함께 판단.
- JS/CSS 소스 문자열을 검사하는 기존 테스트들(`test_mobile_sheet_close_moves_focus_
  before_hiding_dialog`, `test_mobile_sheet_css_uses_fixed_viewport_height_cap`,
  `test_selected_slot_info_prompts_tag_selection` 등)은 Frontend Work Policy가 금지하는
  형태이고, 위 결함 5번에서 실제로 거짓 확신을 줬다. 이번 트랙 범위 밖이라 남기되,
  별도 테스트 정리 트랙에서 삭제를 권한다.
- `apps/core/static/core/img/tag_usage_guide{,_en}.png` — 대시보드 모달 삭제로 참조가
  하나 줄었다. 홈(6단계)에서도 걷어내면 완전히 고아가 된다. 그때 함께 판단.
