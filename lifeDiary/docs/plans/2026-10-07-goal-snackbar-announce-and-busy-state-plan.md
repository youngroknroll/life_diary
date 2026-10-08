# 목표 표 삭제 알림 전달·요청 중 상태 표시 계획 (2026-10-07)

- 브랜치: `feat/goal-due-date` (PR #89에 이어 붙인다)
- 상태: 구현 완료 (2026-10-07), PR #89에 포함

## 배경

`docs/refactoring/2026-10-07-goal-form-invalid-clear-and-undo-timer.md` "남은 일"에서 범위 밖으로 미룬 두 건. 사용자가 2026-10-07에 "범위 밖으로 밀려난 위험을 해결하고, 검토하면서 생기는 문제도 남기지 말라"고 지시했다.

1. 삭제 뒤 스낵바(`#goalSnackbar`)에 라이브 리전이 없어 "○○ 일간 목표를 삭제했습니다" 문구가 스크린리더에 전달되지 않는다. 포커스가 "되돌리기" 버튼으로 옮겨지므로 버튼 이름만 들린다. 삭제 성공은 `#goalSaveStatus`(role=status)에 빈 문구를 보내므로 그쪽으로도 전달되지 않는다.
2. `goals.js`의 전역 `busy` 플래그가 요청 하나가 진행 중일 때 들어온 다른 저장·추가·삭제·되돌리기를 조용히 무시한다(`submitForm` 첫 줄 `if (busy) return;`). 누른 버튼은 잠기지 않고, 상태 문구도 바뀌지 않아 사용자는 눌렀는지조차 알 수 없다.

계획을 세우며 확인한 연관 문제(같은 원인 묶음이라 이번에 함께 고친다):

3. 응답이 오면 `swapBody`가 `#goalManagerBlock` 전체를 서버 본문으로 갈아끼운다. 그 순간 다른 행이나 추가 폼에 입력 중이던 값이 모두 사라진다. 요청 하나가 진행되는 몇백 ms~몇 초 사이에 다른 행을 고치기 시작했거나, 목표를 지운 뒤 다른 행을 고치다가 8초 안에 "되돌리기"를 누른 경우가 여기 해당한다. 2번을 "기다리라"고 보이게 고치면 "기다리는 동안 고친 것은 어디로 갔나"가 바로 드러나므로 함께 해결한다.
4. 다른 요청이 진행 중일 때 8초 타이머가 스낵바를 숨길 수 있다. 2번에서 되돌리기 버튼을 요청 중에 잠그면, 잠긴 동안 스낵바가 사라지는 경우가 생기므로 타이머가 요청이 끝난 뒤에 숨기게 한다.

## 승인 범위

### A. 삭제 문구를 스크린리더에 전달

- `goals.html`의 되돌리기 버튼에 `aria-describedby="goalSnackbarText"`를 붙인다. 삭제 성공 뒤 포커스가 이미 이 버튼으로 가므로(2026-10-07 첫 작업), 스크린리더는 버튼 이름과 함께 "○○ 일간 목표를 삭제했습니다"를 읽는다.
- 스낵바 자체를 라이브 리전으로 만들지 않는다. 스낵바는 `hidden`(display: none)으로 숨겨 두었다가 문구를 넣는 것과 같은 순간에 보이게 한다. 접근성 트리에 없던 영역이 내용과 함께 나타나는 경우는 스크린리더가 읽는다는 보장이 없다(`dashboard.js`의 `#undoSnackbar`도 같은 구조인데 실기기 확인이 없다). 보이기 전에 영역을 먼저 두고 한 박자 뒤 문구를 넣는 방식은 타이밍에 기대는데 실기기로 확인할 수 없다.
- `#goalSaveStatus`로 같은 문구를 보내지 않는다. 화면에 같은 문구가 두 번 보이고, 스크린리더에도 두 번 들린다.
- 새 문자열·CSS 없음.

### B. 요청 중 상태를 보이게 하고 편집 내용을 지키기

- B1. 요청이 나가면 누른 버튼은 스피너로 잠그되 `disabled` 대신 `aria-disabled="true"`를 쓴다(`.is-busy`가 이미 `pointer-events: none`이고, 키보드로 다시 눌러도 `busy` 확인이 막는다). 지금은 `lock()`이 누른 버튼을 `disabled`로 바꿔 Chrome이 포커스를 `<body>`로 떨어뜨리고 요청이 끝날 때까지 그대로 둔다(브라우저 상호작용 사전 검토 High). 그 밖의 제출 버튼(각 행 저장, 삭제 확인의 "삭제", 추가, 되돌리기)은 `disabled`로 잠근다. 요청이 끝나면(`finally`) 그 시점에 잠겨 있는 제출 버튼을 다시 질의해 전부 푼다(요청 중 새로 생긴 확인 줄 "삭제"도 포함). 성공·422로 본문을 다시 그리면 새 버튼은 처음부터 열려 있고, 되돌리기 버튼은 본문 밖이라 `finally`가 푼다.
  - 행 칸에서 Enter로 하는 암묵 제출은 기본 버튼이 `disabled`면 일어나지 않는다(HTML 명세). 브라우저에서 확인한다.
  - 요청 중에 삭제 링크를 누르면 확인 줄은 지금처럼 열리되 "삭제" 버튼은 잠긴 채 만들고, 포커스는 "취소"로 보낸다. 요청이 끝나면 "삭제"가 풀린다.
  - 잠긴 버튼이 잠긴 것으로 보이도록 CSS 한 규칙을 더한다: `.goal-manager button:disabled:not(.is-busy)`와 `.goal-snackbar__undo:disabled:not(.is-busy)`에 `opacity`와 `cursor: default`. `.btn-sian`에는 disabled 모양이 없어 지금은 잠겨도 똑같이 보인다. 새 색 토큰 없음.
  - 포커스된 요소가 `disabled`로 바뀌는 경우는 없다. 누른 버튼은 `aria-disabled`라 포커스를 유지하고, 나머지 버튼은 요청 시작 시점에 포커스를 갖고 있지 않다. `finally`의 "포커스가 `<body>`면 누른 버튼으로" 복귀는 안전장치로 남긴다.
  - 요청 전에 삭제 확인 줄(`is-confirming`)이 열려 있던 행을 기록해 두고, 다시 그린 뒤 같은 행이 있으면 같은 라벨로 확인 줄을 다시 연다. 포커스는 옮기지 않는다(웹 경험 사전 검토 결함 1). 확인 줄 열기와 포커스 이동을 나눠, 사용자 조작(`askDelete`)만 포커스를 옮긴다.
- B2. 본문을 갈아끼우기 전에 제출한 폼이 아닌 폼 중 바뀐 것(행: 바인딩 시점 값과 다름, 추가 폼: 빈 폼과 다름)의 값을 목표 id(추가 폼은 자기 자신)로 모아 두고, 갈아끼운 뒤 같은 행이 있으면 값을 되돌려 넣고 색 견본·시간 상한·기한 비활성·dirty 표시를 다시 맞춘다. 사라진 행(삭제됨)은 건너뛴다. 제출한 폼은 서버 응답(성공은 저장된 값, 422는 거부된 값과 오류)을 따른다.
  - 추가 폼의 기준을 "빈 폼"으로 두는 이유: 422로 다시 그린 추가 폼은 사용자가 넣은 값을 들고 있는데, 이를 기준으로 삼으면 그 값이 "깨끗한" 것이 되어 다음 갈아끼우기에서 사라진다.
  - 행의 기준을 "바인딩 시점 값"으로 두는 이유: 지금의 dirty 판정과 같다. 422로 다시 그린 행은 거부된 값이 기준이 되어 그대로 두면 다른 요청 뒤 저장된 값으로 돌아간다(거부된 값이라 잃는 것이 없다). 거기서 더 고치면 dirty가 되어 지켜진다.
  - 되돌려 넣는 값으로 `change`·`input` 이벤트를 흉내 내지 않는다(`toggleDueDate`가 포커스를 옮긴다). 동기화 함수를 직접 부른다. dirty 표시는 바인딩 기준값과 다시 비교해 켠다(강제로 켜지 않는다). 그러려면 `bindRow` 안에 갇힌 `refreshDirty`와 `clean`을 모듈 함수와 `WeakMap`으로 올린다.
  - 되돌리기는 `bind()` 뒤, `focusRow`·`focusInvalid`·`focusAddTag` 전에 끝나고 `.focus()`를 부르지 않는다.
  - 전역 상태를 늘리지 않는다. 모아 둔 값은 `submitForm` 한 번의 지역 변수다.
- B3. 8초 자동 숨김이 요청 중에 울리면 숨기지 않고 보류 표시만 해 두고(스낵바당 하나인 모듈 상태), 요청의 `finally`에서 보류 중이면 8초를 다시 건다. 되돌리기 요청 자체는 지금처럼 타이머를 멈추고 실패하면 다시 건다. 되돌리기 성공의 `hideSnackbar()`(`busy`가 아직 참인 `onSuccess` 안)는 타이머 경로와 별개이므로 `busy` 확인을 타이머 콜백에만 둔다.
- 여전히 한 번에 요청 하나다. 본문 전체를 갈아끼우는 구조에서 동시 요청은 응답 순서가 뒤바뀌면 오래된 본문이 남는다. 행 단위 잠금은 하지 않는다.
- 새 문자열 없음. `.goal-manager`·`.goal-snackbar__undo` disabled 모양 CSS 한 규칙(`opacity: .55; cursor: default`, 웹 경험 사전 명세 제안값. 다크·라이트 스크린샷으로 잠긴 것이 읽히는지 보고 .5~.65 사이에서 조정 가능).

## 제외 범위

- 스낵바를 라이브 리전으로 만드는 것(위 A의 이유).
- 요청 중 누른 제출을 큐에 넣어 자동으로 다시 보내는 것. 값은 B2로 남으니 사용자가 다시 누르면 된다.
- 행 단위 `busy`, 동시 요청.
- `dashboard.js` 다시 그리기의 포커스 복원(다른 화면, 다른 그리기 구조).
- 자동 숨김으로 포커스가 추가 폼 태그 칸으로 갈 때 이유를 알리는 것(기존 수용).

## 수락 기준

1. 삭제 뒤 포커스가 간 되돌리기 버튼의 접근성 트리 `description`이 "○○ ○○ 목표를 삭제했습니다"다(ko·en). 같은 문구가 `#goalSaveStatus`에는 들어가지 않는다.
2. 요청이 진행되는 동안 누른 버튼은 스피너, 다른 행의 저장·추가·되돌리기 버튼은 `disabled`이고 잠긴 모양이다. 요청이 끝나면(성공·422·네트워크 실패 모두) 전부 풀린다.
3. 요청 중 다른 행 칸에서 Enter를 눌러도 요청이 나가지 않고(네트워크 기록 0건), 그 행의 편집 값은 응답 뒤에도 남아 있고 저장 버튼이 보인다.
4. 요청 중 추가 폼에 입력한 값은 응답 뒤에도 남아 있다. 추가 폼 422 뒤 다른 행을 저장해도 추가 폼 값이 남아 있다.
5. 목표를 지운 뒤 다른 행을 고치고 되돌리기를 누르면, 복원 뒤에도 고친 행의 값과 저장 버튼이 남아 있고 포커스는 복원된 행 태그 칸이다.
6. 요청 중 삭제 링크를 누르면 확인 줄의 "삭제"는 잠겨 있고 포커스는 "취소"다. 요청이 끝나면 "삭제"가 풀린다.
7. 요청 시작 시점과 요청 중에 `document.activeElement`가 `<body>`로 떨어지지 않는다. 키보드로 저장 버튼에 포커스를 두고 Enter로 제출해도 요청 내내 포커스가 그 버튼에 남는다(`aria-disabled`, 스피너).
7a. 삭제 확인 줄을 연 행이 다른 요청의 응답으로 다시 그려지면 같은 라벨의 확인 줄이 다시 열려 있고, 포커스는 그 응답의 규칙(저장 → 같은 칸 등)을 따른다.
8. 스낵바가 보이는 동안 8초를 넘기는 다른 요청이 진행되면 스낵바는 요청이 끝날 때까지 남고, 끝난 뒤 8초 안에 숨는다.
9. 되돌리기 성공·실패·422의 기존 동작(2026-10-07 두 번째 작업 수락 기준 8~10)이 그대로다.
10. 다시 그린 뒤 포커스 착지(저장 성공 → 같은 칸, 422 → 첫 오류 칸, 추가 성공 → 추가 폼 태그, 삭제 → 되돌리기 버튼)가 그대로다.
11. 새 문자열·색 토큰 없음. 1280·375px 가로 넘침 없음, 44px 터치 영역 유지. 콘솔 JS 오류 0건, `node --check` 통과. 다크·라이트 × ko·en을 지난 두 작업과 다른 조합으로 확인한다(1280px 라이트 en, 375px 다크 ko).
12. 전체 pytest 통과.

## Activated Roles

- Web Experience Designer: 사전 명세, 구현 후 판정 (잠긴 버튼 모양, 알림 전달 방식, 편집 보존 흐름)
- Browser Interaction Reviewer: 사전 기준, 구현 후 판정 (잠금·해제 경로, 포커스, 암묵 제출, 타이머, 보존 값의 동기화)
- Frontend Implementation Engineer: `goals.js`, `goals.html`, `style.css`, 작업 로그·상태 문서
- Quality Verification Lead: 증거와 수락 기준 대조

## Not Activated

- Product Scope Owner: 사용자가 해결할 항목을 지정했다. 3·4번 연관 문제는 이 계획 승인으로 범위에 넣는다.
- Backend TDD Coach, Backend & Integration Engineer, Domain Architecture Reviewer: 서버 동작·context·경계 변경이 없다.
- Security & Resilience Reviewer: 새 요청 경로·권한 변경 없음. 한 번에 요청 하나인 구조는 그대로다.
- Deployment & Operations Reviewer: 배포·설정 변경 없음.
- AI Automation Architect: 해당 없음.

## 도메인 경계와 의존 방향

브라우저 상태만 바뀐다. 서버 응답 형식과 오류 판정은 그대로다.

## 결합도와 응집도

- 값 읽기·쓰기·dirty 판정을 `goals.js` 안의 함수 셋으로 모은다. 행 dirty 판정(`currentValues`)이 이미 있으므로 그것을 읽기 함수 위에 올린다.
- 잠금 범위는 `submitForm` 하나가 관리한다. 호출부는 바뀌지 않는다.

## 파일과 단계

| 파일 | 변경 |
|---|---|
| `apps/users/templates/users/goals.html` | 되돌리기 버튼 `aria-describedby="goalSnackbarText"` |
| `apps/users/static/users/js/goals.js` | B1 누른 버튼 `aria-disabled`, 다른 제출 버튼 잠금·재질의 해제, 확인 줄 "삭제" 잠금·확인 줄 재등장, B2 편집 값 모으기·되돌리기와 dirty 기준(행: 바인딩 값, 추가 폼: 빈 폼), `refreshDirty`·기준값을 모듈 수준으로, B3 요청 중 자동 숨김 보류 |
| `apps/core/static/core/css/style.css` | 잠긴 제출 버튼 모양 한 규칙. 구현 중 추가 명세: 375px 스낵바(탭바 위 배치, 되돌리기 44px, 줄바꿈 금지) |

## Frontend Review Evidence

### 검토 깊이: High

비동기 요청 중의 잠금 상태, 포커스, 본문 교체를 가로지르는 값 보존을 다룬다.

### Web Experience Designer 사전 명세 (요약)

- 상태 채널은 셋을 유지한다: `#goalSaveStatus`(처리 중·성공·오류 문구), 누른 버튼의 스피너, 다른 버튼의 잠긴 모양. 삭제 문구는 되돌리기 버튼 설명으로만 간다. 기대 읽기 순서: "되돌리기" → button → "○○ ○○ 목표를 삭제했습니다".
- 잠긴 모양: `.goal-manager button:disabled:not(.is-busy)`, `.goal-snackbar__undo:disabled:not(.is-busy)`에 `opacity: .55; cursor: default`. 스낵바는 테마에 따라 배경이 반전되므로 고정 색 대신 opacity가 맞다. "취소"는 활성 유지. 상태 필은 "처리 중..." 하나로 충분.
- B2 복원 뒤 보여야 하는 것: dirty 배경·테두리, 저장 버튼, 색 견본, 시간 상한, 기한 칸 비활성. 422 행을 일부 고친 뒤 다른 응답이 오면 값은 남고 서버가 심은 오류 표시는 사라진다(수용, 서버가 재검증).
- 결함 1: 확인 줄이 열린 행이 다른 응답으로 조용히 닫힌다 → 기록해 두고 같은 라벨로 다시 연다(포커스 이동 없음). 결함 2: `askDelete`가 요청 중이면 "삭제"를 잠그고 포커스를 "취소"로 보내는 분기를 명시한다.

### Browser Interaction Reviewer 사전 기준 (요약)

- A1 되돌리기 버튼 description이 삭제 문구(ko·en). A2 `#goalSaveStatus`에 삭제 문구 없음. A3 이미 포커스가 되돌리기 버튼에 있는 채로 재진입하는 경로가 없는지 구현 후 확인.
- B1-1 `#goalManagerBlock`의 `button[type=submit]` 전부와 `.goal-snackbar__undo`를 잠그고, "취소"·입력·셀렉트·삭제 링크는 활성. B1-2 해제는 완료 시점 재질의. B1-3 눌린 버튼의 포커스 `<body>` 드롭(High)을 결정할 것 → 이 계획은 `aria-disabled`로 결정. B1-4 요청 중 `askDelete`는 "삭제" 잠금·포커스 "취소". B1-5 네트워크 실패만 `finally` 해제에 의존.
- B2-1 행 기준은 바인딩 시점 값, 추가 폼 기준은 빈 폼 고정값. B2-2 동기화 함수 직접 호출, 이벤트 흉내 금지, dirty는 재계산. B2-3 복원은 `bind()` 뒤·포커스 이동 전, `.focus()` 호출 없음. B2-4 사라진 행은 건너뜀. B2-5 제출한 폼 제외. B2-6 되돌리기 폼 제외. B2-7 네트워크 실패는 복원 없음(DOM 그대로). B2-8 dirty 아닌 422 행이 DB 값으로 돌아가는 것은 결함 아님.
- B3-1 타이머가 `busy` 중 울리면 보류, `finally`에서 8초 재예약. B3-2 되돌리기 핸들러의 멈춤·재예약과 충돌 없음. B3-3 영원히 남는 경로 없음. B3-4 되돌리기 성공의 `hideSnackbar`와 구분. 위험 6: 보류 플래그는 전역 단일 상태.
- 저장소 확인: `goalManagerBlock`·`_goal_manager.html` 사용처는 `goals.html`과 `views.py`뿐. `dashboard.js` `#undoSnackbar`는 범위 밖.

### 계획된 브라우저 증거

- 격리 SQLite(스크래치 디렉터리), dev 설정, dev DB에 쓰지 않는다. `fetch`를 감싸 지연·실패를 흉내 낸다.
- A: 삭제 뒤 되돌리기 버튼의 접근성 트리 이름·description, `#goalSaveStatus` 내용.
- B1: 3초 지연 요청 중 버튼 상태 스크린샷, Enter 암묵 제출 시 네트워크 기록, 요청 종료 뒤 상태. 성공·422·오프라인 세 경로. 키보드(Tab+Enter)로 제출한 요청 중 `document.activeElement`. 확인 줄 열린 행의 재등장. 사전 확인: 기본 버튼이 `disabled`(겸 `hidden`)인 폼의 시간 칸에서 Enter → submit 0건, fetch 0건(Chrome 154).
- B2: 요청 중 다른 행·추가 폼 편집 → 응답 뒤 값·저장 버튼·색 견본·기한 비활성 확인. 삭제 → 다른 행 편집 → 되돌리기 → 값 유지·포커스 복원.
- B3: 스낵바 표시 중 10초 지연 요청 → 요청 종료 전 스낵바 유지, 종료 뒤 숨김.
- 1280px 라이트 en, 375px 다크 ko, 콘솔, `node --check`.
- 스크린리더 실기기는 확인할 수 없다. 접근성 트리로 대신한다.

### 구현 후 판정

- Web Experience Designer: Conforms, 위반 0건 (375px 스낵바 추가 명세 포함)
- Browser Interaction Reviewer: Conforms, 차단 결함 0건
- Quality Verification Lead: 실행 로그 "품질 검증 판정" 참조
- 상세: `docs/refactoring/2026-10-07-goal-snackbar-announce-and-busy-state.md`

## 검증 명령

```bash
node --check apps/users/static/users/js/goals.js
conda run -n knou-life-diary pytest apps/users/test_goal_page.py --tb=short
conda run -n knou-life-diary pytest
conda run -n knou-life-diary python manage.py check
```

## 커밋 단위

1. `docs(goals)`: 이 계획
2. `fix(goals)`: 삭제 문구를 되돌리기 버튼 설명으로 전달한다 (`goals.html`)
3. `fix(goals)`: 요청 중에는 다른 제출 버튼을 잠그고 편집 값을 지킨다 (`goals.js`, `style.css`)
4. `docs(goals)`: 작업 로그와 `docs/project-status.md`
