# 목표 표 포커스·오류 칸·탭 순서 계획 (2026-10-07)

- 브랜치: `feat/goal-due-date` (PR #89에 이어 붙인다)
- 상태: 승인 (2026-10-07)

## 배경

목표 기한 작업(`docs/refactoring/2026-10-06-goal-due-date.md` "남은 일")에서 기존 결함 세 건을 범위 밖으로 남겼다. 사용자가 2026-10-07에 세 건의 해결을 지시했다.

1. 목표를 저장하면 키보드 포커스가 사라진다. `goals.js` `swapBody`가 `#goalManagerBlock`을 통째로 갈아끼우기 때문이다. 추가·삭제·되돌리기·거부(422) 경로도 같다. 네트워크 실패 경로는 본문을 갈지 않지만, 요청 중 버튼을 `disabled`로 잠그면서 포커스가 빠질 수 있다.
2. 오류가 난 행에서 원인과 무관하게 목표 시간 칸(과 기한 칸)이 빨갛게 칠해진다. `style.css`의 `.goal-row.has-error .goal-row__input`, `.goal-row.has-error .goal-row__date`(추가 폼 `.goal-add.has-error` 포함)가 행 단위로 칠한다. 뷰는 첫 오류 문구만 넘기고 어느 칸의 오류인지는 넘기지 않는다(`views.py` `_first_form_error`). 태그·기간 셀렉트는 오류여도 칠해지지 않는다.
3. 쌓기 레이아웃(992px 미만)에서 화면 순서와 탭 순서가 다르다. DOM은 태그 → 기간 → 시간인데 화면은 1행이 태그·시간, 2행이 기간이다.

## 승인 범위

1. 뷰가 화면에 보이는 오류의 필드 이름을 context `error_field`로 넘긴다. 값은 `form.errors` 키 그대로(`tag`, `period`, `target_hours`, `due_date`, 필드 밖 오류는 `__all__`), 오류가 없으면 빈 문자열. 문구와 필드는 `form.errors`를 한 번 순회해 함께 꺼낸다.
2. 템플릿이 `error_field`에 맞는 컨트롤에만 `aria-invalid="true"`와 `aria-describedby`(오류 문구 `<p>`의 id)를 붙인다. 중복 오류(`__all__`)는 태그·기간 셀렉트 둘 다 표시한다.
3. 오류 색은 `[aria-invalid="true"]` 컨트롤에만 칠한다. 행 단위 `.has-error` 규칙과, 그 때문에 쓰이지 않게 되는 `has-error` 클래스는 지운다. 기존 토큰 두 개(`--color-danger-text`, `--color-danger-soft`)만 쓴다.
4. `goals.js`가 경로마다 포커스를 옮긴다(아래 "포커스 목표").
5. 992px 미만 그리드 배치: 1행 태그(두 열 차지), 2행 기간 | 시간, 3행 기한 | 저장·삭제. 추가 폼은 1행 태그, 2행 기간 | 시간, 3행 기한, 4행 추가 버튼. DOM 순서는 바꾸지 않는다.

### 포커스 목표

| 경로 | 포커스 |
|---|---|
| 행 저장 성공 | 같은 행(`data-goal-id`)에서 제출 직전 포커스가 있던 칸(`name`으로 찾음). 그 칸이 없거나 비활성·숨김(저장 버튼은 성공 뒤 숨는다)이면 그 행의 태그 셀렉트 |
| 행 저장 거부(422) | 새로 그린 본문의 첫 `aria-invalid` 컨트롤. 중복 오류면 태그 셀렉트 |
| 추가 성공 | 비워진 추가 폼의 태그 셀렉트(`#goalAddTag`). 이어서 추가하는 동선 |
| 추가 거부(422) | 추가 폼의 첫 `aria-invalid` 컨트롤 |
| 삭제 성공 | 스낵바의 "되돌리기" 버튼 |
| 되돌리기 성공 | 되돌린 행의 태그 셀렉트. 새 pk라 id로는 못 찾으므로 태그·기간 값이 같은 행을 찾는다(태그·기간 조합은 사용자당 하나, `UserGoalForm.clean`). 못 찾으면 `#goalAddTag` |
| 되돌리기 거부(422) | 추가 폼의 첫 `aria-invalid` 컨트롤(서버가 추가 폼 오류로 그린다) |
| 스낵바 8초 자동 숨김 | 포커스가 스낵바 안에 있으면 숨기기 전에 `#goalAddTag`로 옮긴다 |
| 네트워크·예외 실패 | 본문은 그대로다. 잠금을 푼 뒤 포커스가 `<body>`에 떨어져 있으면 눌렀던 버튼으로 되돌린다(`stats.js`의 `activeElement === body` 가드와 같은 방식) |

- 거부 문구는 지금처럼 라이브 리전에 다시 넣지 않는다. 포커스가 간 컨트롤의 `aria-describedby`로 읽힌다. 성공 문구는 기존 `setStatus` 그대로.
- 저장소 선례: `tags/js/tag_list.js`의 `pendingFocus`/`repairFocus`(다시 그린 뒤 같은 의미의 노드를 찾아 포커스, 없으면 고정 앵커).

## 제외 범위

- JS 없는 환경의 422 전체 페이지에 `autofocus` 붙이기(브라우저 상호작용 검토 기준 11). 결함은 AJAX 교체에서 포커스를 잃는 것이고, JS 없는 경로는 일반 페이지 이동이라 포커스가 사라지지 않는다. 오류 칸 표시(`aria-invalid`)는 JS 없는 경로에도 그대로 적용된다.
- 칸마다 오류 문구를 따로 두는 구조. 첫 오류 한 줄 설계를 유지한다.
- 전역 `busy` 플래그로 다른 행 저장이 조용히 무시되는 문제, `dashboard.js` 다시 그리기의 포커스 복원(검토자가 같은 결함 유형으로 보고, 범위 밖).
- `GoalRepository.find_by_user` 정렬 추가.

## 수락 기준

1. 기한 오류로 거부된 추가·수정 응답의 context `error_field`가 `"due_date"`이고, `add_error`/`row_error`는 문구 문자열 그대로다.
2. 중복 태그·기간으로 거부되면 `error_field`가 `"__all__"`, 일간 24시간 초과로 거부되면 `"target_hours"`다.
3. 화면에서 빨간 테두리·배경이 붙는 칸이 오류 원인과 같다. 기한 오류 → 기한 칸만, 시간 초과 → 시간 칸만, 중복 → 태그·기간 칸만. 원인이 아닌 칸이 칠해지는 경우 0건.
4. 오류 칸 컨트롤에 `aria-invalid="true"`와 오류 문구 id를 가리키는 `aria-describedby`가 있다.
5. "포커스 목표" 표의 경로마다 `document.activeElement`가 표대로이고 `<body>`가 아니다.
6. 375px, 820px, 991px에서 Tab으로 이동할 때 포커스가 위 → 아래, 같은 줄에서는 왼쪽 → 오른쪽으로만 간다(행 폼, 추가 폼). 위로 되돌아가는 이동 0건.
7. 375px 가로 넘침 없음, 체크박스·버튼 터치 영역 44px 이상 유지. 992px·1280px 5열 표는 바뀌지 않는다.
8. 콘솔 오류 0건, `node --check` 통과. 다크·라이트, ko·en 확인.
9. 전체 pytest, `manage.py check`, prod deploy check, `makemigrations --check`가 통과한다.

## Activated Roles

- Web Experience Designer: 사전 명세(완료), 구현 후 판정
- Browser Interaction Reviewer: 사전 기준(완료), 구현 후 판정
- Backend TDD Coach: `error_field` 테스트 목록(완료)
- Backend & Integration Engineer: 뷰 context, 테스트, 문서
- Frontend Implementation Engineer: 템플릿, CSS, `goals.js`
- Quality Verification Lead: 증거와 수락 기준 대조

## Not Activated

- Product Scope Owner: 사용자가 해결할 결함 세 건을 직접 지정했다. 범위 결정은 이 계획 승인으로 받는다.
- Domain Architecture Reviewer: `users` 앱 뷰 안의 context 키 하나 추가다. 앱 경계·의존 방향이 바뀌지 않는다.
- Security & Resilience Reviewer: 새 엔드포인트·권한 경로가 없다. 기존 소유자 필터 그대로.
- Deployment & Operations Reviewer: 마이그레이션·설정·배포 변경 없음.
- AI Automation Architect: 해당 없음.

## 도메인 경계와 의존 방향

- 변경은 `users` 앱의 뷰·템플릿·정적 파일과 공용 `style.css`에 머문다. 새 import 없음.
- 오류 원인 판단은 폼(`UserGoalForm`, `UserGoal.clean`)이 이미 필드 키로 정한다. 뷰는 그 키를 그대로 내보내고, 키를 어떤 컨트롤에 표시할지(`__all__` → 태그·기간)는 템플릿이 정한다.

## 결합도와 응집도

- 문구와 필드 이름을 한 함수가 함께 돌려줘 둘이 어긋날 수 없다.
- JS는 거부 응답 뒤 `[aria-invalid="true"]`만 찾는다. 필드 → 컨트롤 대응을 JS에 다시 두지 않는다.

## Pythonic 설계

- `_first_form_error(form)`가 `(field, message)` 튜플을 돌려준다. 오류가 없으면 `("", "")`.
- `_goal_page_context`에 키워드 인자 `error_field=""`를 더한다. 새 클래스·헬퍼 없음.

## 파일과 단계

### 백엔드 (TDD)

| 파일 | 변경 |
|---|---|
| `apps/users/views.py` | `_first_form_error`가 필드 이름과 문구를 함께 반환, `_goal_page_context`·`usergoal_create`·`usergoal_update`가 `error_field` 전달 |
| `apps/users/test_goal_page.py` | 아래 테스트 |

### TDD 체크포인트 (한 번에 하나)

1. `test_an_empty_date_without_no_due_date_is_rejected`에 `error_field == "due_date"`와 `add_error`의 정확한 문구 단언을 더한다. 예상 Red: `KeyError: 'error_field'`. 최소 Green: 튜플 반환, 두 호출부 언패킹, 추가 경로만 `error_field` 전달.
2. `test_moving_a_due_date_into_the_past_is_rejected`에 `error_field == "due_date"`를 더한다. 예상 Red: `error_field`가 빈 문자열. Green: 수정 경로도 전달.
3. `test_a_second_goal_for_the_same_tag_and_period_is_rejected`에 `error_field == "__all__"`를 더한다. 일반 구현이면 바로 통과(특성 테스트). `__all__`을 건너뛰는 변이에서 실패를 확인한다.
4. 새 테스트 `test_a_daily_goal_over_24_hours_names_the_hours_field`: 일간 25시간 추가 → `error_field == "target_hours"`. 모델 `clean()`에서 오는 오류 경로라 따로 고정한다. 특성 테스트, `target_hours`를 건너뛰는 변이에서 실패 확인.

### 프론트엔드 (테스트 없음, 브라우저 검증)

| 파일 | 변경 |
|---|---|
| `apps/users/templates/users/_goal_manager.html` | 컨트롤별 조건부 `aria-invalid`/`aria-describedby`, 오류 `<p>`에 id(`goalRowError{pk}`, `goalAddError`), `has-error` 클래스 제거 |
| `apps/users/static/users/js/goals.js` | 경로별 포커스 이동, 스낵바 숨김 전 포커스 구조, 실패 경로 버튼 포커스 복귀 |
| `apps/core/static/core/css/style.css` | `.has-error` 규칙 두 개를 `[aria-invalid="true"]` 규칙 하나로, 992px 미만 태그·시간 칸 배치 |

## Frontend Review Evidence

### 검토 깊이: High

비동기 상태(성공·422·예외·되돌리기·자동 숨김) 전반의 포커스 관리를 바꾼다. 정책표의 "async state"에 해당한다.

### Web Experience Designer 사전 명세 (요약)

- 쌓기 배치: `.goal-row__tag`를 `grid-column: 1 / -1; grid-row: 1`, `.goal-row__hours`를 `grid-row: 2`로. 기간·기한·액션과 추가 폼 오버라이드는 그대로. 3행, 44px 터치 영역, 기간 셀렉트 128px 유지. 태그 셀렉트가 넓어지는 것은 허용.
- 오류 표시: `error_field`와 같은 칸만. `__all__`은 태그+기간. 오류 문구는 지금처럼 행 아래 한 줄. 새 색 토큰 없음.
- 포커스 착지: 행 저장 성공 → 제출 직전 칸(저장 버튼이면 대체), 422 → 오류 칸, 추가 성공 → `#goalAddTag`, 삭제 → 되돌리기 버튼, 되돌리기 → 복원된 행 태그 셀렉트. `<body>`로 떨어지면 안 된다.
- 정적 접근성: 오류 컨트롤에 `aria-invalid`, 오류 문구 id를 `aria-describedby`로 연결. 기존 `:focus-visible` 링 재사용.

### Browser Interaction Reviewer 사전 기준 (요약)

- 결함 근거: `goals.js` `swapBody`의 `innerHTML` 교체, `lock()`의 `disabled`, 삭제 성공 뒤 포커스 이동 없음, 스낵바 8초 숨김이 포커스를 날림, 되돌린 행은 새 pk.
- 저장소 선례 `tag_list.js` `pendingFocus`/`repairFocus`, `stats.js` `activeElement === body` 가드를 따른다.
- 기준: 경로별 포커스(위 표), 422 오류는 `aria-describedby`로만 안내(라이브 리전 이중 안내 금지), `[aria-invalid]` 기반 CSS, 행·추가 폼 대칭, 쌓기 배치에서 기간·시간 좌우 순서를 뒤집지 않음, 44px·넘침 회귀 없음.
- 이 계획과 다른 점: 중복 오류는 검토자 안(칸 강조 없이 오류 문구에 `tabindex=-1` 포커스) 대신 디자이너 안(태그·기간 강조, 태그로 포커스)을 따른다. 원인이 두 칸의 조합이라 칸을 짚어 주는 쪽이 고칠 곳을 바로 알려준다. 되돌리기 포커스는 검토자 안(`#goalAddTag`) 대신 태그·기간으로 복원된 행을 찾는다(찾지 못하면 `#goalAddTag`). `autofocus`(기준 11)는 제외 범위.

### 계획된 브라우저 증거

- 격리 SQLite(스크래치 디렉터리)에 dev 설정으로 서버를 띄운다. dev DB에는 쓰지 않는다.
- 경로별 `document.activeElement` 확인: 행 저장 성공(입력에서 Enter, 저장 버튼), 행 422(과거 기한, 빈 기한, 시간 초과, 중복), 추가 성공·422, 삭제, 되돌리기, 스낵바 8초 방치, 오프라인 저장.
- 422 경우마다 칠해진 칸 스크린샷과 `aria-invalid`/`aria-describedby` 속성 확인, 접근성 트리 스냅숏으로 설명 문구 연결 확인.
- 1280, 992, 991, 820, 375px에서 Tab 순서와 넘침, 터치 영역 측정.
- 다크·라이트, ko·en. 콘솔 오류 0건. `node --check`.
- 스크린리더 실기기 확인은 이 환경에서 할 수 없다. 접근성 트리로 대신 확인하고 미검증으로 보고한다.

### 구현 후 판정

- Web Experience Designer: 미정
- Browser Interaction Reviewer: 미정
- Quality Verification Lead: 미정

## 검증 명령

```bash
conda run -n knou-life-diary pytest apps/users/test_goal_page.py --tb=short
conda run -n knou-life-diary pytest
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
node --check apps/users/static/users/js/goals.js
```

새 사용자 문자열이 없어 번역 카탈로그는 바꾸지 않는다.

## 커밋 단위

1. `docs(goals)`: 이 계획
2. `feat(users)`: 거부된 목표 폼이 오류 필드 이름을 넘긴다 (TDD 1~4)
3. `fix(goals)`: 오류 칸만 표시하고 쌓기 배치 순서를 DOM에 맞춘다 (템플릿·CSS)
4. `fix(goals)`: 목표 표를 다시 그린 뒤 포커스를 되돌린다 (`goals.js`)
5. `docs(goals)`: 작업 로그와 `docs/project-status.md`
