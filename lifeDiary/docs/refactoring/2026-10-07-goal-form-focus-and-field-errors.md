# 목표 표 포커스·오류 칸·탭 순서 실행 로그 (2026-10-07)

- 계획: `docs/plans/2026-10-07-goal-form-focus-and-field-errors-plan.md`
- 브랜치: `feat/goal-due-date` (PR #89)
- 범위: 목표 기한 작업(`docs/refactoring/2026-10-06-goal-due-date.md` "남은 일")에서 미룬 기존 결함 세 건. JS 없는 환경의 `autofocus`, 칸별 오류 문구, `busy` 플래그, 대시보드 포커스 복원은 계획대로 제외했다.

## 한 일

| 결함 | 원인 | 수정 |
|---|---|---|
| 저장 뒤 포커스가 사라짐 | `goals.js` `swapBody`가 `#goalManagerBlock`을 `innerHTML`로 갈아끼움. 실패 경로는 `lock()`이 포커스된 버튼을 `disabled`로 바꿔 포커스가 `<body>`로 빠짐 | 경로별로 포커스를 옮긴다(아래 표) |
| 오류 행에서 시간 칸까지 빨갛게 칠해짐 | 뷰가 첫 오류 문구만 넘기고 필드 이름은 넘기지 않음. CSS가 `.has-error` 행의 시간·기한 칸을 원인과 상관없이 칠함 | 뷰가 `error_field`(`form.errors` 키, 필드 밖 오류는 `__all__`)를 넘기고, 템플릿이 그 칸에만 `aria-invalid`·`aria-describedby`를 붙이고, CSS는 `[aria-invalid="true"]`만 칠한다. 중복 오류는 태그·기간 두 칸 |
| 쌓기 레이아웃의 탭 순서 어긋남 | 992px 미만에서 1행이 태그·시간, 2행이 기간 | 1행 태그(두 열), 2행 기간 \| 시간, 3행 기한 \| 저장·삭제. 추가 폼은 3행 기한, 4행 추가 버튼. DOM은 그대로 |

### 포커스가 가는 곳

| 경로 | 포커스 |
|---|---|
| 행 저장 성공 | 같은 행에서 제출 직전 칸. 저장 버튼이었으면(성공 뒤 숨음) 그 행의 태그 칸 |
| 행·추가·되돌리기 거부(422) | 새로 그린 본문의 첫 `aria-invalid` 칸 |
| 추가 성공 | 비워진 추가 폼의 태그 칸 |
| 삭제 성공 | 스낵바 "되돌리기" 버튼 |
| 되돌리기 성공 | 태그·기간이 같은 복원된 행의 태그 칸(새 pk라 id로는 못 찾는다) |
| 스낵바 8초 자동 숨김 | 포커스가 스낵바 안이면 숨기기 전에 추가 폼 태그 칸으로 |
| 네트워크 실패 | 잠금을 푼 뒤 포커스가 `<body>`면 누른 버튼으로 |

## 계획에서 달라진 점

- TDD 4번: 새 테스트 대신 기존 `test_ajax_create_reports_invalid_input_as_unprocessable`(일간 99시간 → 422)에 `error_field == "target_hours"` 단언을 더했다. 계획한 새 테스트와 입력이 같아 같은 요청을 두 번 시험하게 된다.
- `focusRow`는 대상 칸의 `disabled`만 확인하고 `hidden`은 확인하지 않는다. 숨는 컨트롤은 저장 버튼뿐이고 `name`이 없어 바로 태그 칸으로 간다. 지금 실패하는 경우는 없다(브라우저 상호작용 사후 검토가 확인).

## TDD 증거

| # | 테스트 | Red | Green |
|---|---|---|---|
| 1 | `test_an_empty_date_without_no_due_date_is_rejected` + `error_field == "due_date"`, `add_error` 정확한 문구 | `KeyError: 'error_field'` | 통과. 튜플 반환, 두 호출부 언패킹, 추가 경로만 전달 |
| 2 | `test_moving_a_due_date_into_the_past_is_rejected` + `error_field == "due_date"` | `AssertionError: assert '' == 'due_date'` | 통과. 수정 경로도 전달 |
| 3 | `test_a_second_goal_for_the_same_tag_and_period_is_rejected` + `error_field == "__all__"` | 바로 통과(특성 테스트). `__all__`을 건너뛰는 변이에서 `assert '' == '__all__'` | 원복 뒤 통과 |
| 4 | `test_ajax_create_reports_invalid_input_as_unprocessable` + `error_field == "target_hours"` | 바로 통과(특성 테스트). `target_hours`를 건너뛰는 변이에서 `assert '' == 'target_hours'` | 원복 뒤 통과 |

`apps/users/test_goal_page.py` 26 passed.

## 브라우저 검증

Chrome 154(DevTools). 격리된 SQLite(스크래치 디렉터리)에 dev 설정으로 서버를 띄웠다. 스크래치 설정 파일에서만 이메일 인증을 껐다. dev DB에는 쓰지 않았다. 동작마다 800ms 뒤 `document.activeElement`를 읽었다.

| 경로 | 결과 |
|---|---|
| 시간 칸에서 Enter로 저장 | `goalHours1`, `:focus-visible` |
| 저장 버튼에서 Enter | `goalTag3` |
| 과거 기한 거부 | `goalDue1`. 그 칸만 `aria-invalid`, `aria-describedby="goalRowError1"`. 시간 칸은 기본 테두리 |
| 일간 25시간 거부 | `goalHours1`만 오류. 브라우저 `max` 검증이 먼저 막으므로 `max` 속성을 지우고 서버까지 보냈다 |
| 중복 태그·기간 거부 | `goalTag3`. 태그·기간 두 칸 오류, 접근성 트리에 `invalid="true"`와 설명 "공부 일간 목표가 이미 있습니다." |
| 추가 성공 | `goalAddTag`, 폼 비워짐 |
| 추가 거부(체크 해제 + 빈 기한) | `goalAddDue`만 오류. 원래 시간 칸이 칠해지던 경우 |
| 삭제(키보드) | 되돌리기 버튼 |
| 되돌리기 | 복원된 행(pk 5)의 태그 칸, 기한 2026-10-17 복원, 스낵바 숨김 |
| 스낵바 8.5초 방치 | 되돌리기 버튼 → `goalAddTag`, 스낵바 숨김 |
| 오프라인 저장 | 실패 문구, 포커스는 저장 버튼. 확인해 보니 Chrome 154는 포커스된 버튼을 `disabled`로 바꾸면 포커스를 `<body>`로 옮기고 되살리지 않는다. 새 복귀 코드가 되돌린 것이다 |
| 되돌리기 거부(지운 목표를 다시 추가한 뒤 되돌리기) | 추가 폼 태그 칸(첫 오류 칸), 스낵바 유지 |

- 쌓기 배치: 375px(기기 에뮬레이션)·820px·991px에서 DOM 순서대로 컨트롤 위치를 재어 위로 되돌아가거나 같은 줄에서 왼쪽으로 가는 이동 0건(행 폼 전부, 추가 폼). 820px에서 실제 Tab: 태그(95,666) → 기간(77,718) → 시간(666,718) → 기한 없음(77,784).
- 넘침: 375·820·991·992px 가로 넘침 0. 992px 기한 칸 넘침 0. 체크박스 라벨 73×44px. 992·1280px는 머리글이 있는 5열 표 그대로.
- 다크(1280px 기한 오류, 테두리 rgb(232,146,122)), 라이트(375px 기한 오류, 1280px 추가 중복), ko·en 확인. 영어 문구 "A Daily goal for 독서 already exists.".
- 콘솔 JS 오류 0건. 콘솔에는 일부러 낸 422 응답을 Chrome이 적은 네트워크 기록만 있다. 서버 로그 Traceback 0건(POST 200 8건, 422 7건).

## 프런트 검토 판정

- Web Experience Designer: **Conforms**. 그리드 배치, 원인 칸만 표시(`__all__` → 태그·기간), 오류 문구 위치 불변, 새 토큰 없음(측정 색이 기존 토큰과 일치), 44px 유지, 포커스 착지를 확인했다. 오류 칸을 고치기 시작하면 테두리는 dirty 초록, 배경은 재제출까지 오류색으로 남는 상태는 수용 가능으로 봤다. 이전에는 시간 칸만 빨간 테두리가 남고 기한 칸은 지금과 같았는데, 이를 한쪽으로 맞춘 것이다.
- Browser Interaction Reviewer: **Conforms**. 포커스 경로, 422 칸 표시, 쌓기 배치, 라이브 리전 이중 안내 없음(422는 `aria-describedby`로만)을 코드와 증거로 확인했다. 잔여 위험은 아래 "남은 일"에 옮겼다.
- Quality Verification Lead: 아래 "품질 검증 판정".

## 품질 검증 판정

Quality Verification Lead: **Complete with residual risk**. 수락 기준 9개를 코드·테스트·검토 산출물과 대조해 위반 0건이다. 1·3·4·6·7은 코드로 직접 확인했고, 5·8·9의 실행 결과(브라우저, 전체 회귀, Django 점검)는 이 문서의 증거로 판단했다(검토 역할에는 실행 도구가 없다). 잔여 위험:

- TDD 4번이 계획한 새 테스트 이름이 아니라 기존 테스트에 단언을 더했다. 변이로 유효성은 확인했으나 계획의 테스트 목록과 이름이 다르다("계획에서 달라진 점").
- 고친 칸에 남는 오류 표시, 스낵바 타이머와 되돌리기 요청 경합("남은 일").
- 브라우저 상호작용 사후 검토에는 다크 모드 증거를 넘기지 않았다. 다크 모드 확인 자체는 위 브라우저 검증에 있다.

## 검증 명령

2026-10-07, 마지막 코드 변경 뒤 실행했다.

| 명령 | 결과 |
|---|---|
| `conda run -n knou-life-diary pytest apps/users/test_goal_page.py --tb=short` | 26 passed |
| `conda run -n knou-life-diary pytest -q` | 721개 통과, 실패·오류·건너뜀 0, exit 0. `-q`가 `pytest.ini` addopts와 겹쳐 요약 줄은 나오지 않았다. 기존 테스트에 단언만 더해 기준선 721과 개수가 같다 |
| `python manage.py check` | 이슈 0건 |
| `python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR` | exit 0. W009(로컬 SECRET_KEY 길이, 기존과 같음) |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `node --check apps/users/static/users/js/goals.js` | 통과 |

새 사용자 문자열이 없어 번역 카탈로그는 바꾸지 않았다.

## 남은 일

- 오류 칸을 고쳐도 재제출 전까지 `aria-invalid`·`aria-describedby`와 오류 배경이 남는다. 스크린리더는 이미 고친 칸도 오류로 읽는다(브라우저 상호작용 검토 Medium, 계획 수락 기준 밖). 입력 시 그 칸의 표시를 지우는 방안이 있으나 중복 오류처럼 두 칸이 함께 걸린 경우의 규칙을 따로 정해야 한다.
- 스낵바 8초 타이머가 진행 중인 되돌리기 요청을 기다리지 않는다. 7.9초쯤 되돌리기를 누르면 응답 전에 스낵바가 사라질 수 있다(결과와 포커스는 맞다. 검토 Low).
- 스낵바에 라이브 리전이 없어 "삭제했습니다" 문구가 스크린리더에 전달되지 않는다. 포커스가 되돌리기 버튼으로 가는 것만 전달된다(기존 결함).
- 전역 `busy` 플래그가 다른 행 저장을 조용히 무시한다. `dashboard.js` 다시 그리기에도 포커스 복원이 없다(검토자 보고, 범위 밖).
- 확인하지 않은 것: 실제 스크린리더(NVDA·VoiceOver, 접근성 트리로만 확인), 실제 모바일 기기, 마우스 클릭 뒤 `:focus-visible` 모양.
