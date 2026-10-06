# 목표 기한 실행 로그 (2026-10-06)

- 계획: `docs/plans/2026-10-06-goal-due-date-plan.md`
- 브랜치: `feat/goal-due-date`
- 범위: 계획의 승인 범위 전부. 이메일·푸시 알림, 배너 닫기, 기한 지난 목표 자동 처리는 계획대로 제외했다.

## 한 일

| 영역 | 내용 |
|---|---|
| 모델 | `UserGoal.due_date`(NULL = 기한 없음), 마이그레이션 `users/0005_usergoal_due_date` |
| 상태 규칙 | `apps/users/goal_deadline.py` `deadline_state(due_date, today)` → `none` / `upcoming` / `due_today` / `overdue` + 일수 |
| 폼 | `no_due_date`가 날짜보다 우선, 빈 날짜 제출은 거부, 기한 칸을 보내지 않으면 기한 없음, 새로 정하거나 바꾼 과거 날짜만 거부, 되돌리기(`restore`)는 지난 기한도 복원 |
| 유즈케이스 | `GoalData.due_date`, `SaveGoalUseCase`가 저장, `ListDueSoonGoalsUseCase`(지난 지 3일 ~ 7일 뒤, 기한 이른 순) |
| 통계 | 진행 행에 `due_date`만 캐시, 통계 뷰가 캐시에서 꺼낸 뒤 `with_deadline_states`로 오늘 기준 상태를 붙인다. 캐시 키 `:v3` → `:v4` |
| 목표 페이지 | 진행률 카드와 표 행에 배지, 표에 기한 열(체크박스 + 날짜), 거부 시 입력값 유지 |
| 대시보드 | 날짜 제목 아래 한 줄 배너. 가장 급한 1건 + "그 외 N건", 목표 페이지 링크 |
| 번역 | 새 문자열 14개 ko/en |

## 계획에서 달라진 점

- 테스트 8a를 8번 앞에 끼웠다. 폼이 기한을 무시하던 상태에서 8번(체크박스 우선)은 Red 없이 통과하기 때문이다.
- 테스트 17을 17a(행에 상태를 붙이는 함수, 단위)와 17(통계 뷰 연결)로 나누고, 목표 페이지 context 테스트 17c(진행률 카드)와 17d(표 행 `goal_items`)를 더했다. 계획의 화면 범위(목표 페이지 배지)를 백엔드 테스트로 받친 것이다.
- 기존 테스트 `test_a_rejected_add_keeps_what_the_user_typed`는 `add_values` 전체를 비교한다. 새 키 `due_date`, `no_due_date`를 기대값에 더했다(계약 확장).
- 캐시 키 버전 `:v4`는 테스트 없이 바꿨다. 배포 전에 캐시된 행에는 `due_date`가 없어서, 버전을 그대로 두면 통계 화면이 `KeyError`로 500을 낸다. 옛 키 문자열을 테스트에 박으면 구현을 따라가는 테스트가 된다.
- 목표 표: 기한 열이 계획의 190px로는 들어가지 않는다(체크박스 라벨 + 날짜 + 배지). 열을 296px로, 목표 페이지 전용 패널(`settings-panel--wide`)을 720px → 920px로 넓혔다. 영어 "No deadline"·"Overdue"에서 272px가 최대 19px 넘쳐 296px로 정했다.
- 목표 표가 세로로 쌓이는 기준을 768px 미만에서 992px 미만으로 바꿨다. 768~991px에서는 Bootstrap 컨테이너가 720px라 5열에서 태그 칸이 2px로 줄어 선택 상자가 사라졌다(820px에서 확인).
- 모바일에서 저장/삭제를 2행에서 3행(기한 칸 옆)으로 옮겼다. 화면 순서가 DOM 순서(태그 → 기간 → 시간 → 기한 → 삭제)를 따르게 하기 위해서다.
- 배너는 `.page-head` 위가 아니라 바로 아래에 두었다. h1이 DOM에서 먼저 오도록 한 브라우저 상호작용 기준을 따랐다.
- 배지 중립 톤은 `--color-text-meta`(흰 바탕 3.07:1) 대신 `--color-text-muted`(약 4.5:1)를 썼다.
- 날짜 칸의 비활성화는 서버 HTML이 아니라 `goals.js`가 붙인다. JS가 없어도 체크를 풀고 날짜를 입력할 수 있고, 둘 다 오면 서버에서 체크박스가 이긴다.

## TDD 증거

| # | 테스트 | Red | Green |
|---|---|---|---|
| 1 | `test_a_goal_without_a_due_date_has_no_deadline` | 모듈 없음(수집 오류) | 통과 |
| 2 | `test_a_future_due_date_counts_the_days_remaining[1,7]` | 2 failed | 통과 |
| 3 | `test_a_due_date_of_today_is_due_today` | 1 failed | 통과 |
| 4 | `test_a_past_due_date_counts_the_days_overdue[1,5]` | 2 failed | 통과 |
| 5 | `test_a_goal_has_no_due_date_unless_one_is_given` | 1 failed | 통과 |
| 6 | `test_saving_a_goal_keeps_its_due_date` | `AttributeError: 'UserGoal' object has no attribute 'due_date'` | 통과 |
| 7 | `test_saving_without_a_due_date_clears_the_old_one` | 6번 구현으로 바로 통과. 대입을 조건부로 바꾸는 변이에서 실패 확인 | 통과 |
| 8a | `test_a_goal_added_with_a_due_date_keeps_it` | 1 failed | 통과 |
| 8 | `test_checking_no_due_date_wins_over_a_typed_date` | 1 failed | 통과 |
| 9 | `test_an_empty_date_without_no_due_date_is_rejected` | 1 failed | 통과 |
| 10 | `test_a_new_goal_cannot_start_with_a_past_due_date` | 1 failed | 통과 |
| 11 | `test_moving_a_due_date_into_the_past_is_rejected` | 10번 규칙으로 바로 통과(특성 테스트) | 통과 |
| 12 | `test_a_goal_already_past_its_due_date_can_still_be_edited` | 1 failed | 통과 |
| 13 | `test_a_rejected_add_keeps_the_typed_due_date` | 1 failed | 통과(기존 전체 비교 테스트 기대값 갱신) |
| 14 | `test_a_form_without_a_deadline_field_adds_a_goal_without_one` | 9번 구현으로 바로 통과. `"due_date" in self.data` 조건 제거 변이에서 실패 확인 | 통과 |
| 15 | `test_undoing_a_delete_restores_a_past_due_date` | 1 failed | 통과 |
| 16 | `test_a_row_carries_the_goals_due_date` | 1 failed | 통과 |
| 17a | `test_rows_get_their_deadline_as_of_the_given_day` | `ImportError` | 통과 |
| 17 | `test_goal_rows_show_the_deadline_as_of_today` | `KeyError: 'deadline'` | 통과 |
| 18 | `test_cached_goal_rows_keep_the_due_date_but_not_its_daily_state` | 설계 불변식이라 바로 통과. 상태를 캐시 행에 넣는 변이에서 실패 확인 | 통과 |
| 17c | `test_the_progress_card_shows_each_goals_deadline` | `KeyError: 'deadline'` | 통과 |
| 17d | `test_the_goal_table_pairs_each_goal_with_its_deadline` | `KeyError: 'goal_items'` | 통과 |
| 19 | `test_lists_goals_from_three_days_overdue_to_a_week_ahead` | `ImportError` | 통과 |
| 20 | `test_goals_without_a_due_date_are_not_listed` | 범위 조건으로 바로 통과 | 통과 |
| 21 | `test_another_users_goals_are_not_listed` | 바로 통과. `user=` 필터 제거 변이에서 실패 확인. 보안 경계라 필터 없는 구현을 거치지 않았다 | 통과 |
| 22 | `test_the_earliest_due_date_comes_first` | 1 failed | 통과 |
| 23 | `test_the_dashboard_carries_goals_whose_deadline_is_near` | `KeyError: 'goals_due_soon'` | 통과 |

## 브라우저 검증

격리된 SQLite(스크래치 디렉터리)에 dev 설정으로 서버를 띄웠다. dev DB에는 쓰지 않았다. 목표 다섯 개(기한 없음, D-10, D-2, D-day, 1일 지남)로 확인했다.

- 날짜만 바꾸면 저장 버튼이 뜨고, 저장하면 행과 진행률 카드 배지가 D-10 → D-14로 바뀐다.
- 체크하면 날짜는 값을 유지한 채 비활성화되고 포커스는 체크박스에 남는다. 해제하면 날짜가 활성화되고 포커스가 날짜로 간다.
- 과거 날짜는 422로 거부되고 문구가 행 아래에 나오며 입력값이 남는다.
- 지난 기한(2026-10-05) 목표를 지우고 되돌리면 기한과 "기한 지남"까지 돌아온다. 기한 없는 목표는 기한 없음으로 돌아온다.
- 추가 폼은 기본으로 "기한 없음"이 체크되어 있고, 체크를 풀면 날짜를 넣어 추가할 수 있다.
- 대시보드 배너: "기한 지남 코딩 목표 기한이 지났습니다 · 그 외 3건", 링크 `/accounts/goals/`, 높이 44px, Tab 포커스 링 보임.
- 통계 탭: 진행 행 6개 모두 배지가 맞고, 재요청(캐시 적중)에도 같다. 서버 로그에 Traceback 0건.
- 영어: 배너 "Overdue 코딩 goal deadline has passed · 3 more", 표 라벨 "No deadline".
- 폭: 375px 가로 넘침 없음, 체크박스 라벨 터치 영역 73×44px. 820px 쌓기 레이아웃, 태그 칸 575px. 992px·1280px 5열, 기한 칸 넘침 0, 태그 칸 226px.
- 콘솔 오류·경고 0건. 다크·라이트 모두 확인했다.

## 프런트 검토 판정

- Web Experience Designer: **Conforms**. 편차 6건(기한 열 296px·패널 920px, 모바일 저장/삭제 3행, 배너 위치, 배지가 날짜 오른쪽, 중립 톤 `text-muted`)을 근거 있는 조정으로 수용했다. 오류 행의 시간 칸 강조는 차단 사유가 아닌 후속 과제로 봤다.
- Browser Interaction Reviewer: **Conforms**, 신규 결함 없음. 체크박스 우선 규칙의 단일 결정 지점, 되돌리기 두 경로(기한 있음/없음), JS 없는 경로, dirty 판정, live region 미알림을 코드와 증거로 확인했다. 사후 검토가 미검증으로 남긴 "체크 해제 + 빈 날짜" 거부는 이후 브라우저에서 확인했다(추가 거부, 목표 수 6개 유지, 입력값 유지).
- 두 검토자가 기존 결함 2건을 보고했다(아래 "남은 일").
- Quality Verification Lead: **Complete with residual risk**. 수락 기준 12개 모두 Verified. 잔존 위험: 설정 화면(`mypage`) POST 경로를 직접 호출하는 테스트가 없다(같은 `UserGoalForm`을 쓰고, 온보딩은 `usergoal_create`로 보내 테스트 14와 같은 요청이다). 캐시 키 `:v4` 전환은 설계로만 보장된다.

## 검증 명령

2026-10-06, 마지막 코드 변경 뒤 실행했다.

| 명령 | 결과 |
|---|---|
| `conda run -n knou-life-diary pytest` | 721 passed, 0 failed (528s). 기준선 692 |
| `python manage.py check` | 이슈 0건 |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR` | exit 0. 경고 W009(로컬 SECRET_KEY 길이, 이번 변경과 무관) |
| `msgfmt --check-format -o /dev/null locale/{en,ko}/LC_MESSAGES/django.po` | 통과. fuzzy en 0, ko 1(헤더, 기준선과 같음) |
| `node --check apps/users/static/users/js/goals.js` | 통과 |

## 남은 일

- 목표 저장 후 포커스 복원과 오류 칸의 `aria-invalid`/`aria-describedby`: 기존 `goals.js` `swapBody`가 본문을 갈아끼우며 포커스를 잃는다. 기한 기능 이전부터 있던 결함이라 계획에서 후속 과제로 뺐다.
- 오류 행에서 목표 시간 칸까지 빨갛게 칠해진다. 기존 `.goal-row.has-error .goal-row__input` 규칙이 오류 원인과 무관하게 행의 숫자 칸을 칠한다. 기한 오류는 이번에 생긴 새 경로라 사용자가 처음 보게 된다. 필드 단위 오류 표시로 바꾸는 것을 접근성 트랙에서 함께 다룬다.
- 쌓기 레이아웃의 탭 순서: DOM은 태그 → 기간 → 시간인데 화면은 시간이 1행, 기간이 2행이다. 원래 768px 미만에만 있던 어긋남이, 쌓기 기준을 992px로 올리면서 768~991px에도 생겼다. 5열 표에서 태그 선택 상자가 사라지는 문제보다 작다고 판단했다.
- 스크린리더 실기기 확인, 실제 모바일 기기 확인은 하지 않았다.
