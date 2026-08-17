# 목표 관리 페이지 — 시안 5·6 + 진행률 카드 이식 계획

작성 2026-08-17. 브랜치 `feat/goal-management-page`.

## Context

`/users/goals/`(`users:usergoal_list`)가 껍데기 없는 조각을 렌더한다. 6단계에서
마이페이지의 인라인 목표 편집을 걷어내면서 설정의 "목표 관리" 행을
`usergoal_list.html`(= `{% extends %}` 없는 partial)의 URL로 바로 연결한 결과다.

테스트 DB 렌더 실측(HTTP 200, 625바이트):

```
HAS_DOCTYPE False / HAS_HEAD False / HAS_STYLESHEET False
HAS_NAV False / HAS_GOALS_JS False / HAS_CREATE_LINK False
FIRST_80 '\n\n<div class="table-scroll" ...'
```

그 결과 이 페이지에서 실제로 되는 것은 **리스트 표시**와 **삭제 링크** 둘뿐이다.
사용자 요구는 "리스트·생성·추가·삭제·수정이 모두 이 페이지에서" + "가장 위에
현재 진행률 리스트".

## 출처 문서

Claude Design 프로젝트 `a76fc6a6-816e-4865-a42d-d673ab2bca93`에서 읽었다.

| 문서 | 담당 |
|---|---|
| `Life Diary 목표 관리.dc.html` | 진행률 카드, 추가 폼, 상태·스낵바, 검증 규칙 (최신) |
| `Life Diary 반영 점검 시안.dc.html` §6 (6a·6b) | CRUD 표 전체 레이아웃, 행 안 삭제 확인, 상태 3종 |
| 같은 문서 §5 (5a·5b·5c) | 페이지 껍데기, 모바일 360px, 빈 상태 |

문서 안에서 시안끼리도 갱신 관계가 있다. §6 본문이 "5b의 별도 패널 프레임은
이걸로 대체됩니다"라고 명시하므로 **추가 UI는 5b의 접이식 패널이 아니라 6a의
표 마지막 줄 상주 행**을 채택한다.

## 조사로 확정한 사실

- `build_goal_progress_rows(user, selected_date, today=None)`
  (`apps/stats/aggregation/goal_progress.py`)가 진행률 카드가 필요로 하는 값을
  이미 전부 돌려준다: `tag_name`·`tag_color`·`category_line_color`·`period`·
  `current_hours`·`target_hours`·`percentage`·`pace_percentage`·`is_under_target`.
- `.goal-progress__head/row/label/value/track/fill/pace/empty` CSS가
  `style.css:1638~`에 이미 있고, 분석 요약 탭이 쓰는 마크업이 시안의 진행률
  카드와 사실상 같은 구조다. **진행률 카드는 신규 개발이 아니라 재사용이다.**
- `UserGoal.clean()`이 기간별 상한(일 24 / 주 100 / 월 300)을 이미 검증한다.
  `SaveGoalUseCase`가 `full_clean()`을 호출하므로 상한은 백엔드에서 보장된다.
- `UserGoal`에 (user, tag, period) 유니크 제약이 **없다**. 시안의 "이미 있습니다"
  중복 오류는 신규 규칙이다.
- `usergoal_update`는 이미 `tag`·`period`를 폼 필드로 받는다. 현재 템플릿이
  hidden으로 넘길 뿐이라, **select로 노출만 하면 백엔드 변경 없이 태그·기간
  수정이 열린다**(6a 주석과 일치, 코드로 확인함).
- `usergoal_create`·`usergoal_update`·`usergoal_delete` 셋 다
  `redirect("users:mypage")`다.
- `goals.js`의 AJAX 부분(`goalAddForm`·`goalListBlock`·`goalSaveStatus`·
  `partialUrl`)은 참조 템플릿이 0건인 죽은 코드다. `mypage_goals_partial` 뷰도
  같은 이유로 도달 불가다. 이번 설계는 **이 둘을 되살려 쓴다**.
- `usergoal_form.html`은 구 부트스트랩(`container mt-4`·`alert alert-info`·
  `btn btn-success`·인라인 `<style>`)이라 현재 디자인 언어와 어긋난다.

## 화면 구성 (위에서 아래로)

신규 `users/goals.html`이 `base.html`을 extends 하고 다음을 담는다.

1. **breadcrumb** `‹ 설정` — 태그 관리(`tags/index.html`)의 `.breadcrumb-trail`과
   같은 컴포넌트.
2. **page-head** — h1 "목표 관리" + 설명 "태그마다 기간과 목표 시간을 정합니다.
   달성률과 실제 기록 시간은 분석에서 봅니다." + 우측 모노 카운트 "N개".
3. **현재 진행률 카드** (사용자 명시 요구, 읽기 전용)
   - 헤더: "현재 진행률" + 모노 메타 "오늘 기준 · 세로선 = 페이스"
   - 행: 스와치 + 태그 + `· 기간라벨` | 모노 `현재 / 목표h · N%` + 8px 트랙
     (채움 = `percentage`, 페이스 마커 = `pace_percentage`)
   - 빈 상태: "목표를 추가하면 여기 진행률이 보입니다."
   - 각주: "진행률은 읽기 전용입니다 — 목표를 고치려면 아래 표에서."
4. **목표 표** (`usergoal_list.html` partial을 `{% include %}`)
   - 헤더 행: 태그 | 기간 | 목표 | (액션)
   - 데스크톱 그리드 `1fr 104px 116px 52px`, 행 최소 높이 56px
   - 각 행 = `usergoal_update` POST 폼 하나: 태그 select(스와치 포함) ·
     기간 select · 시간 number + `h` · 액션 칸
   - 액션 칸: 기본 `✕`(삭제 요청) → 값이 바뀌면 `저장` 버튼 → 삭제 요청 시
     행 전체가 확인 줄로 바뀜(danger 배경 + 좌측 2px 라인 + "독서 월간 20h
     목표를 삭제합니다." + 삭제/취소)
   - 마지막 줄 = **목표 추가 행**: 태그 select("태그 선택") · 기간 select ·
     시간 · `＋` 버튼, 아래 힌트 "일간 최대 24h · 주간 100h · 월간 300h"
5. **상태 영역** — `aria-live="polite"`, "✓ 운동 주간 목표를 6.5시간으로
   저장했습니다", 2.6초 후 사라짐. 기존 `goalSaveStatus` 영역을 그대로 쓴다.
6. **스낵바** — 삭제 후 "…목표를 삭제했습니다 / 되돌리기". 기록 저장 스낵바(4a)와
   같은 컴포넌트.

## 반응형 (5c, 사용자가 명시 요구)

같은 마크업에 미디어 쿼리만 얹는다. 새 템플릿을 따로 만들지 않는다.

| 폭 | 표 | 시간 입력 | 삭제 | 추가 |
|---|---|---|---|---|
| ≥768px | 4열 그리드, 헤더 행 표시 | 62–64px × 38px | 액션 칸 `✕` | 표 마지막 줄 |
| <768px | 그리드 해제, 행 단위 세로 배치. 헤더 행 숨김 | 우측 정렬, **높이 44px** | 행 아래 둘째 줄 텍스트 링크 | 전폭 버튼 "+ 목표 추가" |

- 태그·기간은 모바일에서 한 줄로 묶는다(`공부 · 일간`).
- 빈 상태는 중앙 정렬 문구 + "첫 목표 정하기" CTA(min-height 42px).
- 시안이 명시한 38px 컨트롤은 데스크톱 포인터 전용 값이다. 모바일에서는 44px로
  올린다 — 저장소의 44px 규칙과 5c의 44px 입력 명시가 같은 방향이다.

## 백엔드 변경

`views.py`만 바뀌고 모델·마이그레이션은 없다.

| 뷰 | 현재 | 변경 |
|---|---|---|
| `usergoal_list` | partial을 그대로 렌더 | `goals.html` 렌더 + 진행률 행·태그 목록·추가 폼 컨텍스트 |
| `usergoal_create` | GET=폼, POST 후 mypage | GET=목록으로 리다이렉트, POST 후 목록 |
| `usergoal_update` | GET=폼, POST 후 mypage | 같음 |
| `usergoal_delete` | GET=확인 화면, POST 후 mypage | POST 후 목록. GET 확인 화면은 **JS 없는 환경 폴백으로 유지**(6b) |
| `mypage_goals_partial` | 도달 불가 | 목표 페이지의 AJAX 갱신 경로로 되살림 |

- 중복 검증: `SaveGoalUseCase`에서 (user, tag, period) 중복이면
  "{태그} {기간} 목표가 이미 있습니다."로 거절. **DB 제약·마이그레이션은 넣지
  않는다** — 한 사용자만 쓰는 자원이라 경합 창이 없고, 스키마 변경은 별도 승인
  사안이다.
- 되돌리기: 소프트 삭제를 도입하지 않는다. 삭제 응답이 (tag, period, hours)를
  들고 오고, 스낵바의 "되돌리기"가 그 값으로 `usergoal_create`에 POST 한다.
- `apps.users`가 `apps.stats.aggregation.goal_progress`를 import 한다.
  역방향(`goal_progress` → `apps.users.repositories`)이 이미 있으므로 두 모듈
  사이 순환은 없지만, 의존 방향은 Domain Architecture Reviewer가 판단한다.

## 삭제·정리

- `users/usergoal_form.html` 삭제 (5b·6a가 모두 소멸을 명시).
- `usergoal_confirm_delete.html`은 **남긴다** — GET 폴백 경로가 계속 쓴다.
  대신 목록에서 그 화면으로 가는 링크는 없앤다(6b).
- `forms.py`의 `UserGoalForm` 위젯에서 인라인 `style="width: 50%"`와
  `onchange="updateTargetHoursMax()"` 제거. 상한 안내는 alert 박스가 아니라
  입력 옆 한 줄로 간다.
- 마이페이지 POST 목표 분기 제거는 **이번 범위 밖**이다. 백로그 B-1에 남긴다.

## 단계와 검증

### 1단계 — 백엔드 (Backend TDD Cycle)

Test List (한 번에 하나씩 Red → 최소 Green):

1. `usergoal_list`가 `base.html`을 상속한 완전한 문서를 돌려준다(`<html>` 포함).
2. `usergoal_list` 컨텍스트에 진행률 행이 들어 있고, 목표가 없으면 빈 리스트다.
3. `usergoal_create` GET은 목록으로 리다이렉트한다.
4. `usergoal_update` GET은 목록으로 리다이렉트한다.
5. `usergoal_create` POST 성공 후 목록으로 리다이렉트한다.
6. `usergoal_update` POST 성공 후 목록으로 리다이렉트한다.
7. `usergoal_delete` POST 후 목록으로 리다이렉트한다.
8. 같은 (태그, 기간) 목표를 또 만들면 거절되고 기존 개수가 그대로다.
9. 수정 시 자기 자신은 중복으로 치지 않는다.
10. 남의 목표에는 접근할 수 없다(기존 `get_or_404` 보장 회귀 확인).
11. 일간 목표의 `pace_percentage`가 조회일이 과거면 100이다.
12. 일간 목표의 `pace_percentage`가 오늘이면 주입한 `now`의 경과 비율이다.
13. `percentage`가 `pace_percentage`보다 작으면 `is_behind_pace`가 참이다.
14. 페이스와 같거나 앞서면 `is_behind_pace`가 거짓이다.

`conda run -n knou-life-diary pytest apps/users --tb=short`로 단계마다 확인한다.

### 2단계 — 프런트엔드 (Frontend Dual Review Gate)

구현 전 Web Experience Designer · Browser Interaction Reviewer 산출물을 실제로
작성하고, 구현 후 두 역할의 `Conforms`/`Deviates`/`Unverified` 판정을 남긴다.
템플릿·CSS·브라우저 JS에는 테스트를 쓰지 않는다(Frontend Work Policy).

브라우저 실측 항목:

- 1440px / 375px, 라이트 / 다크
- 값 변경 시에만 저장 버튼 노출, 세 필드(태그·기간·시간) 모두 감지
- 삭제 → 행 안 확인 → 확정 → 스낵바 → 되돌리기 → 행 복귀
- 상한 초과 입력 시 오류 문구와 붉은 테두리
- 중복 (태그, 기간) 추가 시 오류 문구
- JS 끈 상태에서 추가·수정·삭제가 모두 동작(저장 버튼 상시 노출, 삭제는 확인
  화면 경유)
- 키보드만으로 전 경로 통과, 포커스 링 보임
- 모바일 44px 타깃, 진행률 카드가 접히지 않고 읽히는지
- 콘솔 에러 0건
- **대기 상태**: Slow 3G + 응답 지연 상태에서 저장·추가·삭제·되돌리기 네 버튼이
  각각 스피너로 바뀌고 `disabled`가 되며, 연타해도 요청이 한 번만 나가는지
  (Network 패널로 확인). 응답 후 원상 복구, 실패 시 오류 문구 노출.
- 페이스보다 뒤처진 목표의 숫자가 붉게 나오고, 분석 요약 탭의 같은 목표도
  같은 색인지 두 화면 대조

### 3단계 — i18n·마감

`makemessages` → **ko msgstr 직접 채움** → `compilemessages` →
`msgfmt --check-format`으로 fuzzy 0건 확인. 새 문자열이 요일·기존 문구를
오상속하지 않는지 개별 확인한다(이 저장소에서 반복된 함정).

## 최종 검증

```bash
conda run -n knou-life-diary pytest
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
node --check apps/users/static/users/js/goals.js
```

## 사용자 결정 (2026-08-17)

### 1. 진행률 값이 붉어지는 조건 — 시안대로

`percentage < pace_percentage`(페이스보다 뒤처짐)를 danger 조건으로 쓴다.
4단계의 `is_under_target`(기간 종료 후 확정 미달)만 쓰던 규칙을 대체하며,
**분석 요약 탭도 같은 규칙으로 함께 바꾼다** — 같은 목표가 두 화면에서 다른
색으로 보이면 안 된다.

이 결정은 집계에 두 가지를 요구한다.

- `_pace_percentage`가 `daily`에 `None`을 돌려주고 있다. 시안은 일간에도 페이스
  선을 그리므로(`PACE.daily = 70`), 일간 페이스를 **그날 경과 비율**로 채운다:
  조회일이 과거면 100%, 오늘이면 `(경과 분 / 1440)`, 미래면 0%.
- 시각 의존이 생기므로 `build_goal_progress_rows(user, selected_date, today=None)`에
  `now=None`을 추가해 주입 가능하게 한다. `today`를 분리한 것과 같은 이유다
  (전역 시각 모킹 없이 테스트).

`is_under_target`은 계산은 유지하되 색 결정에서는 손을 뗀다. 지우지 않는 이유는
"기간이 끝났고 못 채웠다"와 "지금 뒤처져 있다"가 다른 사실이고, 전자를 쓰는
자리가 나중에 생길 수 있어서다. 이번 트랙에서 화면이 쓰는 것은 `is_behind_pace`
하나다.

### 2. 서버 호출 중 대기 상태 표현 — 전부 필요

추가·수정·삭제·되돌리기 등 **서버를 부르는 모든 조작**은 응답이 늦을 수 있다는
전제로 대기 상태를 보여준다. 요구사항은 화면 장식이 아니라 이중 제출 방지와
같은 문제다.

공통 규칙:

- 버튼은 요청 시작 시 `disabled` + `aria-busy="true"` + 인라인 스피너.
  스피너는 기존 `@keyframes spin`(style.css)을 재사용하고, 버튼 폭이 흔들리지
  않도록 라벨 자리를 유지한 채 스피너만 얹는다.
- 스크린리더에는 `aria-live` 상태 영역이 "저장 중…"을 읽어준다. 시각 표시만으로
  끝내지 않는다(2026-08-13 내보내기 버튼에서 같은 결함을 이미 겪었다).
- 같은 버튼의 재진입을 플래그로 막는다. 응답 도착·실패·타임아웃 어느 경로로든
  반드시 원상 복구한다(`finally`).
- 실패 시 버튼을 되살리고 상태 영역에 오류를 남긴다. 조용히 되돌리지 않는다.
- 대상: 행 저장, 행 삭제 확정, 목표 추가 `＋`, 스낵바 되돌리기.
- `prefers-reduced-motion: reduce`에서는 회전을 멈추고 정적 표시로 바꾼다.

느린 응답을 실제로 확인하기 위해, 브라우저 실측은 DevTools 네트워크 스로틀링
(Slow 3G)과 서버 응답 지연을 넣은 상태에서 한 번 더 돈다.

## Deferred

- 마이페이지 POST 목표 분기 제거 (백로그 B-1)
- (user, tag, period) DB 유니크 제약 — 스키마 변경이라 별도 승인
- `.segmented__item` 44px 등 전역 터치 타깃 규칙 (백로그 C-4)
