# 목표 관리 페이지 — 목록·추가·수정·삭제 한 화면 통합

계획: `docs/plans/2026-08-17_goal-management-page-plan.md`.
브랜치: `feat/goal-management-page`.

## 승인된 범위

- `users:usergoal_list`가 `base.html`을 상속한 완전한 문서(`goals.html`)를
  렌더하고, 진행률 카드와 CRUD 표를 `_goal_manager.html` 한 조각에 담는다.
- 추가·수정·삭제를 모두 이 화면에서 처리하고, 폼 페이지 두 개를 걷어낸다.
- 사용자 결정 1 — 진행률이 붉어지는 조건을 "페이스보다 뒤처짐"으로 바꾸고,
  분석 요약 탭도 같은 규칙으로 함께 바꾼다.
- 사용자 결정 2 — 서버를 부르는 모든 조작(행 저장·삭제 확정·목표 추가·되돌리기)에
  대기 상태를 보여준다.
- 추가 요청(같은 날) — 추가 폼 아래에 "원하는 태그가 없다면 태그를 추가하세요"
  + `+ 태그` 링크 줄.

## Activated Roles

- Domain Architecture Reviewer — `apps.users.views`가
  `apps.stats.aggregation.goal_progress`를 import 하는 방향을 확인. 역방향
  (`goal_progress` → `apps.users.repositories`)이 이미 있으나 두 모듈은 서로를
  부르지 않아 순환 없음. 중복 검증은 스키마를 건드리지 않도록 폼 계층에 둔다.
- Backend TDD Coach, Backend & Integration Engineer — 아래 Test List.
- Web Experience Designer, Browser Interaction Reviewer — 아래 Frontend Review
  Evidence.
- Quality Verification Lead — 완료 판정.

## Test List — `apps/users/test_goal_page.py`, `test_goal_progress.py`

| Scenario ID | Business behavior | Then | Test name |
|---|---|---|---|
| GM-1 | 목표 화면은 완전한 문서다 | `<html` 포함 | test_the_goal_page_renders_a_full_document |
| GM-2 | 컨텍스트에 진행률 행이 실린다 | rows=[공부] | test_the_page_carries_progress_rows_for_each_goal |
| GM-3 | 목표가 없으면 진행률 행도 없다 | `[]` | test_the_page_carries_no_progress_rows_without_goals |
| GM-4 | 생성 GET은 목록으로 | 302 → usergoal_list | test_create_get_redirects_to_the_goal_page |
| GM-5 | 수정 GET은 목록으로 | 302 → usergoal_list | test_update_get_redirects_to_the_goal_page |
| GM-6 | 생성 POST 성공 후 목록으로 | Location=usergoal_list | test_creating_a_goal_returns_to_the_goal_page |
| GM-7 | 수정 POST 성공 후 목록으로 | period·hours 반영 | test_updating_a_goal_returns_to_the_goal_page |
| GM-8 | 삭제 POST 후 목록으로 | 행 제거 | test_deleting_a_goal_returns_to_the_goal_page |
| GM-9 | XHR 생성은 갱신된 본문을 돌려준다 | 200, `<html>` 없음 | test_ajax_create_returns_the_refreshed_body |
| GM-10 | XHR 검증 실패는 422 | 422, 미생성 | test_ajax_create_reports_invalid_input_as_unprocessable |
| GM-11 | XHR 삭제도 본문을 돌려준다 | 200 + 삭제됨 | test_ajax_delete_returns_the_refreshed_body |
| GM-12 | 같은 태그·기간 중복은 거절 | count 그대로 | test_a_second_goal_for_the_same_tag_and_period_is_rejected |
| GM-13 | 거절돼도 입력값이 남는다 | add_values 보존 | test_a_rejected_add_keeps_what_the_user_typed |
| GM-14 | 자기 자신은 중복이 아니다 | 수정 성공 | test_keeping_a_goals_own_tag_and_period_is_not_a_duplicate |
| GM-15 | 남의 동일 목표는 중복이 아니다 | 생성 성공 | test_another_users_identical_goal_is_not_a_duplicate |
| GP-9 | 지난 날짜의 일간 페이스는 100 | pace=100 | test_a_past_daily_goal_reports_a_fully_elapsed_pace |
| GP-10 | 오늘의 일간 페이스는 경과 비율 | round(경과분/1440*100) | test_todays_daily_goal_paces_by_the_elapsed_part_of_the_day |
| GP-11 | 페이스보다 뒤처지면 참 | is_behind_pace=True | test_a_goal_trailing_its_pace_is_marked_behind |
| GP-12 | 페이스와 같으면 거짓 | is_behind_pace=False | test_a_goal_matching_its_pace_is_not_marked_behind |

전부 `Status: Green`.

## Red → Green

- Red: `test_goal_page.py`의 GM-1이 `<html` 없음으로 실패 — 계획서에 적은
  "625바이트 조각" 렌더를 테스트로 고정했다.
- Green:
  - `goals.html`(껍데기) + `_goal_manager.html`(진행률 카드 + CRUD 표) 신설.
    두 조각으로 나눈 이유는 목표를 고치면 진행률도 같이 낡아서, AJAX 갱신
    한 번으로 둘을 함께 되받기 위해서다.
  - `views.py`: `_goal_page_context`·`_goal_mutation_done`·
    `_goal_mutation_failed`·`_wants_goal_partial`로 쪼갰다. XHR이면 조각을
    200(성공)/422(검증 실패)로, 아니면 목록으로 리다이렉트.
  - `forms.py`: `UserGoalForm(user=...)` + `clean()`에서 (user, tag, period)
    중복 거절. 위젯의 인라인 `onchange="updateTargetHoursMax()"` 제거.
  - `models.py`: `UserGoal.PERIOD_CHOICES` 추출(내용 동일, 마이그레이션 없음).
  - `goal_progress.py`: 일간 페이스를 그날 경과 비율로 채우고 `now` 주입 지원,
    행에 `is_behind_pace` 추가.
- **계획 대비 이탈 3건**(모두 의도한 판단):
  - `usergoal_partial`/`mypage_goals_partial`을 **되살리지 않고 제거**했다.
    변경 뷰가 갱신된 본문을 직접 돌려주므로 별도 partial 경로가 필요 없다 —
    죽은 코드를 되살리는 대신 없앴다.
  - 중복 검증 위치를 `SaveGoalUseCase`가 아니라 `UserGoalForm.clean()`으로
    잡았다. 폼이 이미 (user, tag, period) 셋을 다 들고 있고, 실패 시 사용자가
    친 값을 그대로 되돌려주는 경로도 폼 쪽이 짧다.
  - 모바일에서 태그·기간을 `공부 · 일간` 한 줄로 묶지 않았다. 둘 다 편집
    가능한 select 라서 텍스트로 합칠 수 없다. 대신 태그+시간 / 기간+삭제
    두 줄로 배치했다.

## Frontend Review Evidence

**Review depth**: Deep — 새 화면 전체, 비동기 변경 4종, 인라인 삭제 확인,
스낵바 되돌리기, JS 없는 폴백까지 걸린다.

**Web Experience Designer — 사전 스펙**

- 진행률 카드는 신규 개발이 아니라 분석 요약 탭의 `.goal-progress__*` 재사용.
  스와치=태그 pastel, 채움=카테고리 딥 색, 페이스=회색 세로선.
- CRUD 표는 `--goal-grid` 하나를 헤더·행·추가 폼이 공유해 세로줄이 어긋나지
  않게 한다. 추가 UI는 접이식 패널이 아니라 표 마지막 상주 행(시안 §6이 §5b를
  대체).
- 오류가 나면 사용자가 친 값을 되돌려 놓는다. 값을 원복해 놓고 빨간 테두리만
  남기면 "무엇이 틀렸는지"를 화면이 지운 셈이 된다.
- danger 위 글자색은 `--ink-on-danger` 토큰을 새로 두고 라이트/다크 각각
  5.40:1 / 7.33:1을 확보한다(기존 `--ink-on-primary` 패턴).

**Browser Interaction Reviewer — 사전 기준**

- 서버를 부르는 네 버튼 모두 `disabled` + `aria-busy` + 스피너, 재진입 플래그로
  이중 제출 차단, 어느 경로로든 `finally`에서 원상 복구.
- 시각 표시만으로 끝내지 않는다 — `aria-live="polite"` 상태 영역이 진행과
  결과를 읽어준다.
- `prefers-reduced-motion: reduce`에서는 회전을 멈춘다.
- JS 없이도 추가·수정·삭제가 전부 동작해야 한다(저장 버튼 상시 노출, 삭제는
  기존 확인 화면 경유).
- 새로 만든 컨트롤에 UA 기본 파란 포커스 링이 남지 않아야 한다.

## 브라우저에서 발견한 결함 3건

- **전면 로딩 오버레이가 영영 안 걷힘**: `base.html`의 링크 클릭 핸들러가
  `e.defaultPrevented`를 보지 않아, JS가 가로챈 삭제 링크에서도 오버레이를
  띄웠다. 이동이 없으니 걷히지도 않는다. 바로 아래 submit 핸들러가 이미 쓰던
  같은 규칙을 링크 쪽에도 적용해 고쳤다(별도 커밋 `fix(core)`).
- **UA 기본 파란 포커스 링**: 새 select/input/링크가 팔레트 밖 색을 썼다.
  `:focus-visible` 녹색 링 규칙 추가.
- **375px에서 `.goal-count`가 왼쪽 정렬로 혼자 줄바꿈**: `margin-left: auto`로
  접혀도 오른쪽에 붙게 했다.

검증 중 겪은 두 가지 함정도 남긴다(코드 결함 아님).

- Slow 3G 스로틀 상태에서 1500ms 뒤 DOM을 읽어 삭제가 실패한 것처럼 보였다.
  DB 조회로 삭제 성공을 확인하고 Fast 4G에서 재측정.
- `base.html` 수정이 dev 서버 재시작 전까지 반영되지 않았다
  (`curl | grep -c defaultPrevented` 1 → 2로 확인).

## 검증

- `conda run -n knou-life-diary pytest` — **543 passed** (326.82s).
- `conda run -n knou-life-diary python manage.py check` — 이슈 0.
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run`
  — 변경 없음.
- `node --check apps/users/static/users/js/goals.js` — 통과.
- prod deploy check — 기존 WARNING 1건(`security.W009` SECRET_KEY)만.
- i18n: 네 카탈로그 untranslated 0 · fuzzy 0 · `msgfmt --check-format` 통과.
  `%(tag)s %(period)s 목표가 이미 있습니다.`가 플레이스홀더가 다른 항목
  (`"Nothing logged from %(start)02d:00 …"`)을 fuzzy 로 물려받은 것을 잡아
  고쳤다 — 그대로 뒀으면 포맷 시점에 터졌을 것이다.
- 브라우저 실측(chrome-devtools MCP, 격리 임시 SQLite + `runserver 8765`.
  검증 후 임시 DB·설정 모듈·서버 모두 삭제 — dev DB 무변경):
  - 1440 / 768 / 375 / 360px, 라이트·다크, ko·en.
  - 저장(세 필드 dirty 감지) · 추가 · 삭제 확인 스트립 · 확정 · 스낵바 ·
    되돌리기 · 중복 오류 · 상한 초과 오류 전 경로 통과.
  - Slow 3G에서 네 버튼 스피너·`disabled` 확인, 연타해도 요청 1회.
  - 키보드만으로 전 경로 통과, 포커스 링 보임. JS 없는 구조(폼 action·
    formaction·확인 화면) 확인.
  - 태그 안내 줄: `/tags/` 이동 확인, 접근성 이름 "태그 추가", 44px 타깃,
    AJAX 본문 교체 뒤에도 정확히 1개 유지.
  - 콘솔 오류 0건.

## Frontend Review Evidence — 판정

- **Web Experience Designer**: Conforms — 진행률 카드 재사용, 공유 그리드,
  오류 시 입력값 보존, `--ink-on-danger` 대비 확보 모두 확인. 계획 대비
  이탈 3건은 위에 사유와 함께 기록.
- **Browser Interaction Reviewer**: Conforms — 대기 상태 4종, 이중 제출 차단,
  `aria-live` 낭독, reduced-motion, 포커스 링, JS 없는 폴백 확인. 오버레이
  결함을 잡아낸 것이 이 리뷰가 "실패·취소 경로까지" 요구한 덕분이다.
- **Quality Verification Lead**: 완료로 판정 — 두 역할 Conforms, 발견한 결함
  3건 모두 수정 후 재검증.

## Deferred

- 마이페이지 POST 목표 분기 제거 (백로그 B-1).
- (user, tag, period) DB 유니크 제약 — 스키마 변경이라 별도 승인.
- `is_under_target`은 계산만 남고 화면에서 쓰이지 않는다. "기간이 끝났고 못
  채웠다"는 별개 사실이라 지우지 않았으나, 다음 트랙까지 쓰이지 않으면 정리
  대상으로 올린다.
- `.segmented__item` 44px 등 전역 터치 타깃 규칙 (백로그 C-4).
