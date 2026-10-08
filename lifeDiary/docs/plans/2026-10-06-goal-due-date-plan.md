# 목표 기한(due date) 계획 (2026-10-06)

- 브랜치: `feat/goal-due-date`
- 상태: 구현 완료 (2026-10-06), PR 대기

## 배경

목표(`UserGoal`)는 태그 × 기간(일간/주간/월간) × 목표 시간으로 이뤄진 반복형 목표이고, "언제까지"가 없다. 사용자가 목표에 기한을 정하고, 남은 일수를 화면에서 보고, 대시보드에서 상기받기를 원한다. 기한 없음도 고를 수 있어야 한다.

## 사용자 결정 (2026-10-06)

| 항목 | 결정 |
|---|---|
| 알림 형태 | 화면 내 D-day 배지 + 대시보드 상단 상기 배너. 이메일·푸시 없음 |
| 기한 지난 목표 | 유지. 진행률·통계는 그대로, 배지만 "기한 지남" |
| 입력 | 날짜 칸 + 별도 "기한 없음" 체크박스 |
| 과거 날짜 | 새로 정하거나 바꿀 때만 거부. 이미 지난 기한은 다른 칸을 고칠 때 그대로 저장 가능 |
| 체크 해제 + 날짜 빈칸 | 오류 ("기한을 정하거나 '기한 없음'을 선택하세요") |
| 배너 범위 | D-7 이내(오늘 포함) + 지난 지 3일 이내. 가장 급한 1건 + "그 외 N건" |

## 승인 범위

1. `UserGoal.due_date = DateField(null=True, blank=True)` 추가. NULL = 기한 없음. 마이그레이션 1개.
2. 순수 함수 `deadline_state(due_date, today)` (`apps/users/goal_deadline.py`): `none` / `upcoming`(남은 일수) / `due_today` / `overdue`(지난 일수).
3. `UserGoalForm`에 `due_date`와 비모델 필드 `no_due_date` 추가. 검증 규칙은 아래 "폼 규칙".
4. `GoalData.due_date: date | None = None`, `SaveGoalUseCase`가 저장.
5. 목표 페이지 행·추가 폼에 날짜 칸 + 체크박스, 행에 D-day 배지. 진행률 카드(목표 페이지 상단, 통계 탭)에도 배지.
6. 통계 목표 진행 행(`_goal_progress_row`)에 `due_date`를 싣고, 통계 뷰가 캐시에서 꺼낸 뒤 요청 시점의 오늘로 상태를 계산해 붙인다. 캐시 키 버전 `v3` → `v4`.
7. 대시보드 상단 배너. 조건에 맞는 목표가 없으면 렌더하지 않음.
8. 새 문자열 ko/en 번역.

### 폼 규칙

- `no_due_date` 체크 → 날짜값이 와도 `due_date = None`. 체크박스가 우선한다(JS 없는 환경 포함).
- 체크 해제 + 날짜 칸이 빈 값으로 제출됨(`due_date` 키가 있고 값이 빈 문자열) → 오류.
- `due_date` 키와 `no_due_date` 키가 둘 다 없음 → 기한 없음으로 저장. 기한 칸이 없는 기존 호출자를 깨지 않기 위한 규칙이다(아래 "기존 호출자").
- 날짜 < 오늘 이고 (새 목표이거나 기존 값과 다름) → 오류.
- 날짜 < 오늘 이지만 기존 값과 같음 → 통과(다른 칸 수정 허용).
- 삭제 되돌리기(`restore` 표시가 붙은 생성 요청)는 과거 날짜 검사를 건너뛴다. 기한이 지난 목표를 지웠다가 되돌릴 때 기한까지 복원하기 위해서다. 과거 날짜 검사는 오입력 방지용이고 권한 경계가 아니므로 클라이언트 표시로 건너뛰어도 남의 데이터에 닿지 않는다.
- 새 목표 추가 폼의 기본값은 "기한 없음" 체크.

### 기존 호출자

`UserGoalForm`으로 목표를 만드는 곳은 세 군데이고, 그중 두 곳은 기한 칸을 보내지 않는다.

| 호출자 | 보내는 칸 | 이번 변경 |
|---|---|---|
| 목표 페이지 행·추가 폼 (`_goal_manager.html`) | 기한 칸 추가 | 변경 |
| 온보딩 3단계 (`welcome.html:103` → `usergoal_create`) | tag, period, target_hours | 변경 없음. 기한 없음으로 저장 |
| 설정 화면 POST (`views.py:934` `mypage`) | tag, period, target_hours | 변경 없음. 기한 없음으로 저장 |

기존 테스트의 목표 POST(18건)도 세 칸만 보내므로 수정 없이 통과해야 한다.

### 배지 규칙

| 상태 | 문구(ko / en) | 톤 |
|---|---|---|
| 기한 없음 | 배지 없음 | — |
| D-4 이상 | `D-{n}` | 중립 (`--color-text-meta`) |
| D-3 ~ D-1 | `D-{n}` | 경고 (노트 박스 토큰) |
| 당일 | `D-day` | 경고 |
| 지남 | `기한 지남` / `Overdue` | 위험 (`--color-danger-*`) |

새 색 토큰은 만들지 않는다.

### 배너 규칙

- 대상: 본인 목표 중 `오늘-3 <= due_date <= 오늘+7`.
- 정렬: `due_date` 오름차순(가장 오래 지난 것이 먼저), 같으면 id 순.
- 표시: 첫 1건 문구 + 나머지가 있으면 "그 외 N건". 배너 전체가 목표 페이지 링크(`<a>`).
- 문구: "{태그} 목표 기한이 {n}일 남았습니다" / "오늘입니다" / "지났습니다" (en 대응).
- 닫기 버튼 없음.

## 제외 범위

- 이메일·푸시·데스크톱 알림
- 기한 지난 목표의 자동 삭제·비활성화·진행률 제외
- 배너 닫기/숨김 상태 저장, 배너 기간 사용자 설정
- 기간(일간/주간/월간) 계산 로직 변경
- 목표 저장 후 포커스 복원(기존 결함, 아래 후속 과제)

## 수락 기준

1. `deadline_state(due_date, today)`가 None/미래/당일/과거에 대해 `none`/`upcoming,N`/`due_today`/`overdue,N`을 돌려준다.
2. 체크박스 체크 시 날짜가 함께 와도 `due_date`가 NULL로 저장된다.
3. 체크 해제 + 빈 날짜 → 목표가 저장되지 않고 오류가 표시된다. 기한 칸을 아예 보내지 않는 요청(온보딩, 설정 화면)은 기한 없음으로 저장된다.
4. 새 목표·변경된 기한이 과거면 거부되고, 이미 지난 기한을 그대로 둔 채 목표 시간을 고치면 저장된다.
5. 거부된 제출은 입력한 기한·체크 상태를 화면에 유지한다(`add_values`/`row_values`).
6. 통계 화면의 목표 진행 행에 요청 시점 기준 기한 상태가 실린다. 캐시에는 `due_date`만 들어가고 상태는 들어가지 않는다. 기존 진행률 테스트는 수정 없이 통과한다.
7. 대시보드 context의 배너 목록은 본인 목표 중 범위 안(-3~+7일)만, 정렬 규칙대로 담는다. 기한 없는 목표·범위 밖·타인 목표는 빠진다.
8. 기한만 바꿔도 행의 저장 버튼이 활성화된다(`goals.js` dirty 판정).
9. 기한이 있는 목표를 삭제 후 되돌리면 기한도 복원된다. 기한이 이미 지난 목표도 같다.
10. 375px에서 기한 칸이 겹치지 않고, 체크박스 터치 영역이 44px 이상이다.
11. 새 문자열은 ko/en msgstr가 비어 있지 않고 `msgfmt --check-format`이 통과한다.
12. 전체 pytest, `manage.py check`, prod deploy check, `makemigrations --check`가 통과한다.

## Activated Roles

- Product Scope Owner: 범위·수락 기준 (완료)
- Domain Architecture Reviewer: 규칙 위치, 의존성, 캐시, 마이그레이션 (완료)
- Backend TDD Coach: 테스트 목록 (완료)
- Backend & Integration Engineer: 모델·폼·유즈케이스·뷰·마이그레이션·i18n·문서
- Web Experience Designer: 경험 명세 (완료), 구현 후 판정
- Browser Interaction Reviewer: 상호작용 기준 (완료), 구현 후 판정
- Frontend Implementation Engineer: 템플릿·CSS·`goals.js`
- Quality Verification Lead: 증거 ↔ 수락 기준 대조

## Not Activated

- Security & Resilience Reviewer: 새 엔드포인트 없음. 소유자 범위는 기존 `user=` 필터를 그대로 쓰고 수락 기준 7의 테스트로 확인한다.
- Deployment & Operations Reviewer: nullable 컬럼 추가뿐이라 Postgres에서 백필·잠금 위험 없음(도메인 검토 확인).
- AI Automation Architect: 해당 없음.

## 도메인 경계와 의존 방향

- `users`가 `due_date`, 상태 규칙(`goal_deadline.deadline_state`), 폼 검증, 배너 대상 조회를 모두 소유한다.
- `stats`는 기존처럼 `users.repositories.GoalRepository`를 읽고, 상태 규칙은 `apps.users.goal_deadline`을 호출만 한다.
- `dashboard` → `users`: 새 의존. 도메인 검토는 `apps/users/ports.py`에 `GoalReader` Protocol을 두자고 권했다. 계획은 이미 있는 선례를 따른다. `dashboard/views.py`가 `apps.tags.use_cases.ListFrequentTagsUseCase`를 호출하듯, `apps.users.use_cases.ListDueSoonGoalsUseCase`를 호출한다. 이 방식은 포트·주입 계층 없이 같은 모양(소유 앱 유즈케이스 경유, 읽기 전용)을 유지한다. 리포지토리를 직접 import하지 않는다.
- 금지: `users → dashboard/stats`, `dashboard → users.models/repositories`.

## 결합도와 응집도

- 상태 규칙은 함수 하나라 세 화면이 같은 결과를 낸다. 템플릿은 상태값으로 배지만 고른다.
- 통계 캐시에는 시각에 따라 변하지 않는 값(`due_date`)만 넣는다. 오늘에 따라 달라지는 상태는 캐시 밖에서 계산한다.
- 배너 범위(-3, +7)와 정렬은 `ListDueSoonGoalsUseCase` 한 곳에만 둔다.

## Pythonic 설계

- `deadline_state(due_date, today)`는 `today`를 주입받는다(`build_goal_progress_rows`와 같은 이유: 전역 시각 모킹 회피). 반환은 `frozen dataclass DeadlineState(state, days)`.
- 규칙은 TDD 코치 제안대로 순수 모듈 `apps/users/goal_deadline.py`에 둔다(`verification_policy.py`와 같은 모양). 도메인 검토가 권한 모델 메서드는 쓰지 않는다. 통계 화면은 캐시에서 꺼낸 행(dict)의 `due_date`로 상태를 계산해야 해서, 목표 객체가 아니라 날짜를 받는 함수가 필요하다.
- 새 서비스 계층·포트는 만들지 않는다.

## 파일과 단계

### 백엔드 (TDD)

| 파일 | 변경 |
|---|---|
| `apps/users/models.py` | `due_date` 필드 |
| `apps/users/goal_deadline.py` | 새 파일. `DeadlineState`, `deadline_state(due_date, today)` |
| `apps/users/migrations/0005_usergoal_due_date.py` | 생성 |
| `apps/users/forms.py` | `due_date`, `no_due_date`, `restore`, `clean()` 규칙 |
| `apps/users/use_cases.py` | `GoalData.due_date`, `SaveGoalUseCase` 저장, `ListDueSoonGoalsUseCase` |
| `apps/users/repositories.py` | `GoalRepository.find_due_between(user, start, end)` |
| `apps/users/views.py` | `_goal_data_from_form`, `_submitted_goal_values` |
| `apps/stats/aggregation/goal_progress.py` | 행에 `due_date` |
| `apps/stats/use_cases.py` | 캐시 키 `v3` → `v4`. 배포 직후 `due_date` 없는 옛 캐시 행을 읽지 않게 한다 |
| `apps/stats/views.py` | 캐시에서 꺼낸 진행 행에 오늘 기준 기한 상태를 붙인 새 목록을 context에 넣는다 |
| `apps/dashboard/views.py` | context `goals_due_soon` |

### TDD 체크포인트 (한 번에 하나, Red 확인 후 Green)

A. 상태 규칙 (`apps/users/test_goal_deadline.py`)
1. 기한이 없으면 `none`
2. 미래 기한은 `upcoming` + 남은 일수 (N=1, 7)
3. 오늘 기한은 `due_today`
4. 지난 기한은 `overdue` + 지난 일수 (N=1, 5)

B. 유즈케이스 (`apps/users/test_use_cases.py`)
5. `GoalData` 기본 `due_date`는 None (기존 `test_fields` 확장)
6. 저장 시 `due_date`가 남는다
7. 기존 기한을 None으로 지울 수 있다

C. 폼·뷰 (`apps/users/test_goal_page.py`)
8. 체크박스 체크 시 날짜가 와도 기한 없음으로 저장
9. 체크 해제 + 빈 날짜는 거부
10. 새 목표의 과거 기한은 거부
11. 기존 목표의 기한을 과거로 바꾸면 거부, 기존 값 유지
12. 이미 지난 기한을 그대로 두고 목표 시간만 고치면 저장
13. 거부된 추가는 입력한 기한을 `add_values`에 유지
14. 기한 칸을 아예 보내지 않는 생성 요청은 기한 없음으로 저장 (온보딩·설정 화면 계약)
15. 되돌리기 요청은 지난 기한도 그대로 복원

D. 통계
16. 진행 행은 목표의 `due_date`를 싣는다 (`apps/stats/aggregation/test_goal_progress.py`)
17. 통계 화면 context의 진행 행에 기한 상태가 붙는다 (`apps/stats/tests.py`)
18. 캐시에 저장된 진행 행에는 기한 상태가 없다 (`apps/stats/test_cache_invalidation.py`)

E. 배너 대상 (`apps/users/test_use_cases.py`, 대시보드는 context 데이터 1건)
19. 범위 경계: -3, 0, +7 포함 / -4, +8 제외
20. 기한 없는 목표 제외
21. 타인 목표 제외
22. 정렬: due_date 오름차순
23. 대시보드 context `goals_due_soon`이 유즈케이스 결과를 싣는다 (`apps/dashboard/tests.py`, 마크업 단언 금지)

### 프론트엔드 (테스트 없음, 브라우저 검증)

| 파일 | 변경 |
|---|---|
| `apps/users/templates/users/_goal_manager.html` | 표 머리글 "기한" 칸, 행·추가 폼 기한 칸, 배지, 진행률 카드 배지, 422 값 유지 |
| `apps/users/templates/users/goals.html` | 되돌리기 폼 hidden input에 `due_date`, `restore` |
| `apps/users/static/users/js/goals.js` | 체크박스 ↔ 날짜 동기화, `currentValues`, 삭제 `restore`·`showSnackbar`에 기한 |
| `apps/stats/templates/stats/index.html` | 진행률 행 배지 |
| `apps/dashboard/templates/dashboard/index.html` | 상단 배너 |
| `apps/core/static/core/css/style.css` | `--goal-grid` 5열, 모바일 배치, 배지·배너 스타일 |
| `locale/{ko,en}/LC_MESSAGES/django.po` (+ `djangojs.po` 필요 시) | 새 문자열 |

## Frontend Review Evidence

### 검토 깊이: Standard

폼 행 레이아웃, 반응형 배치, 새 대시보드 배너. 탐색 구조·모달·드래그 변경은 없다.

### Web Experience Designer 사전 명세 (요약)

- 데스크톱 `--goal-grid`: `minmax(0,1fr) 104px 116px 190px minmax(96px,auto)`. 기한 열은 목표 시간 뒤, 저장/삭제 앞.
- 375px: 기한 칸은 `grid-column: 1 / -1`로 기간/시간 행 다음 3행. 안쪽은 체크박스+라벨 → 날짜+배지 순으로 줄바꿈 허용. 저장/삭제 위치 불변.
- 배지는 진행률 카드의 `goal-progress__label` 기간 텍스트 뒤에 붙여 목표 페이지·통계 탭에 같은 규칙 적용.
- 배너는 `.page-head` 위 한 줄, 저채도. 조건 없으면 DOM 미렌더(`empty-nudge` 패턴).
- 라벨: visually-hidden "{태그} 목표 기한", 체크박스는 보이는 라벨 "기한 없음".
- 배지는 텍스트로 의미 전달. 색만으로 구분하지 않는다.

### Browser Interaction Reviewer 사전 기준 (요약)

- 체크 → 날짜 `disabled`, 값은 지우지 않음(해제 시 복원). 해제 → 날짜에 포커스. 체크 시 포커스는 체크박스 유지.
- 서버가 체크박스 우선 규칙을 한 곳(폼)에서 결정.
- `_submitted_goal_values`에 `due_date`, `no_due_date` 포함, 행·추가 폼 템플릿에 반영.
- `goals.js` `currentValues`에 새 필드 포함. 누락 시 기한만 바꾸면 저장 버튼이 안 뜬다.
- 삭제 `restore`와 `goalUndoForm` hidden input에 새 필드 포함. 누락 시 되돌리기에서 기한이 사라진다.
- `change` 리스너에 체크박스 분기 추가(행, 추가 폼).
- DOM 순서 = 시각 순서(모바일 grid 배치 갱신). 체크박스 히트 영역 44×44px 이상(라벨 패딩).
- 토글 자체는 live region에 알리지 않는다. 서버 응답 후 기존 `setStatus`만.
- 배너는 `<a>` 링크, 본문 h1 근처 DOM 순서, live region 아님.
- 날짜 input에 `min` 없음(기존 `_date_selector` 패턴). 과거 거부는 서버 오류로 표시.

### 계획된 브라우저 증거

- 1280px, 375px 스크린샷: 목표 페이지(기한 없음/D-10/D-2/D-day/지남 행), 통계 탭 진행률, 대시보드 배너(1건, 여러 건, 없음)
- 클릭 확인: 체크박스 토글, 기한만 변경 → 저장, 과거 날짜 → 오류·값 유지, 삭제 → 되돌리기 → 기한 복원
- 콘솔 오류 0, `node --check apps/users/static/users/js/goals.js`
- 영어 로캘 화면 1장씩

### 구현 후 판정

- Web Experience Designer: Conforms (편차 6건 수용, 근거는 작업 로그)
- Browser Interaction Reviewer: Conforms, 신규 결함 없음
- Quality Verification Lead: Complete with residual risk. 수락 기준 12개 Verified. 잔존 위험은 설정 화면 POST 경로의 직접 테스트 부재와 캐시 키 `:v4` 전환의 테스트 부재
- 상세: `docs/refactoring/2026-10-06-goal-due-date.md`

## 검증 명령

```bash
conda run -n knou-life-diary pytest <targeted-test> --tb=short
conda run -n knou-life-diary pytest
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
msgfmt --check-format -o /dev/null locale/ko/LC_MESSAGES/django.po
msgfmt --check-format -o /dev/null locale/en/LC_MESSAGES/django.po
node --check apps/users/static/users/js/goals.js
```

## 커밋 단위

1. `feat(users)`: 목표 기한 필드·상태 규칙·폼·유즈케이스 (A~C)
2. `feat(stats)`: 진행률 행 기한, 캐시 밖 상태 계산 (D)
3. `feat(dashboard)`: 기한 임박 배너 대상 (E)
4. `feat(goals)`: 기한 입력·배지·배너 화면 + i18n
5. `docs`: 작업 로그, `docs/project-status.md`

## 후속 과제

```text
Deferred Refactoring Note
- Topic: 목표 행 저장 후 포커스 복원
- Why it is not part of the current scope: 기한 기능 이전부터 있던 결함(goals.js swapBody가 본문을 교체하며 포커스를 잃는다)
- Why it may be needed later: 키보드·스크린리더 사용자가 저장 후 위치를 잃는다
- Trigger condition: 접근성 개선 트랙
- Expected change location: apps/users/static/users/js/goals.js swapBody
- Related tests: 없음(브라우저 검증)
```
