# Dashboard 저장형 DOM-XSS 제거와 삭제 상태 진실화 (Lane B)

실행일: 2026-08-16 (계획 문서 기준일 2026-08-15)

- 계획: `docs/plans/2026-08-15_critical-remediation-plan.md` Task 10~11
- 역할: Frontend Implementation Engineer 구현, Web Experience Designer /
  Browser Interaction Reviewer 사전·사후 이중 리뷰 (아래 판정)
- Review depth: High — DOM sink, 상태 경계, 전 페이지 재사용 그리드

## 사전 리뷰 게이트 (편집 전 완료)

두 리뷰어가 계획서 기준을 현재 소스 라인에 재매핑했다. 핵심 확인:

- `dashboard.js:71` `slotTagInfo()`가 `title` 속성을 ` · `로 재파싱 →
  `:622 inlineEl.innerHTML` 주입. `:594/:618` inline `onclick`.
- `selectTag()`(`:632-638`)가 암묵 전역 `event` 의존, 유일 호출처는
  위임 핸들러 `:126`.
- **활성 결함 발견**: `deleteSlot()` `:901`의 `slotIndexes`는 미정의
  변수(ReferenceError) — 단일 try/catch라 서버 삭제 성공 후에도
  `restoreRows()` + "삭제 실패"가 항상 실행. 편집 전 브라우저에서 실증:
  삭제 클릭 → DB 행 삭제됨(sqlite 확인) vs 화면은 행 복원 +
  `삭제 실패: slotIndexes is not defined` 알림.
- 편집 전 XSS 실증: memo `<img src=x onerror="window.__memoXss=1">`
  슬롯 선택 → `window.__memoXss === 1`, 패널에 `<img>` 주입.
- 저장형 사용자 문자열이 escape 없이 `innerHTML`에 닿는 파일은
  `dashboard.js`뿐임을 저장소 전수 grep으로 확인(리뷰어 보고).

## 구현 (소스 diff 요약)

### `apps/dashboard/templates/dashboard/_day_row.html`
- 채워진 블록에 `data-tag-name="{{ run.tag.name }}"`,
  `data-memo="{{ run.memo }}"` 추가 (Django autoescape가 속성 escape).
- `title`은 tooltip 전용으로 유지, 상태 원천으로 쓰지 않는다.

### `apps/dashboard/static/dashboard/js/dashboard.js`
- `slotTagInfo()`: title 파싱 제거, `dataset.tagName`/`dataset.memo` 읽기.
- `buildBlock()`: JSON 응답에서 같은 dataset 두 필드 설정(SSR과 대칭).
- `showSlotInfo()` 전면 재작성: `replaceChildren()` + `createElement` +
  `textContent`. 빈 상태 분기 포함, 남은 `innerHTML` 분기 없음.
  helper 3개(`slotInfoIcon`(aria-hidden), `slotInfoLine`,
  `slotInfoSmallLine`). 삭제 버튼은 `type="button"` +
  `addEventListener('click', deleteSlot)` — inline onclick 제거.
- `selectTag(targetBtn, ...)`: 클릭 대상을 명시 전달, 전역 `event` 미사용.
  위임 핸들러가 `el`을 넘긴다.
- `deleteSlot()` 3단계 분리:
  1) HTTP 실패만 `restoreRows` + `삭제 실패` (error)
  2) commit 후 렌더 실패는 신규 경고 문구(warning), 복원 금지
  3) `time-blocks-saved` consumer 예외는 console 기록만.
  event detail은 실제 삭제한 `filledSlots` (기존 미정의 `slotIndexes` 교체).

### 카탈로그
- ko/en `djangojs.po`에 신규 문자열 1건:
  `삭제되었지만 화면을 새로 고치지 못했습니다. 페이지를 새로고침해주세요.`
  (en: `Deleted, but the screen could not refresh. Please reload the page.`)

## 브라우저 검증 매트릭스 (2026-08-16, 격리 샌드박스)

환경: scratchpad의 일회용 SQLite + `runserver 8765`(dev DB 무접촉),
Chrome DevTools MCP, 1024×800과 **디바이스 에뮬레이션 375×812(mobile+touch)**.

| 시나리오 | 결과 | 증거 |
|---|---|---|
| FE-XSS-01 (375·1024) | Pass | memo가 문자 그대로 표시, 패널 `img` 0개, `window.__memoXss` unset, inline handler 0개 |
| FE-XSS-02 (375·1024) | Pass | SSR 로드와 저장 후 부분 렌더(buildBlock) 모두 `<b x="'">태그`·따옴표 memo가 동일한 리터럴 텍스트, 신규 element 0 |
| FE-TAG-01 | Pass | 실제 클릭(active + 저장 활성) + event dispatch 밖 프로그램 호출 모두 정상 — `window.event` 의존 없음, console 오류 0 |
| FE-DEL-01 (포인터+키보드) | Pass | 삭제 유지, 스낵바 표시, event detail `{date, slotIndexes:[100]}`(실제 삭제 인덱스), 실패 알림 없음. 버튼 focus 가능, 재렌더 3회 후 활성화 1회 = confirm 1회(중복 listener 없음), confirm 취소 시 행 유지 |
| FE-DEL-02 | Pass | 던지는 listener → console 오류 기록만, 행 삭제 유지, 복원·거짓 실패 없음 |
| 레이아웃 | Pass | 375px에서 body/panel overflow-x 0, 계층·라벨·아이콘 순서 불변(스크린샷 확인) |

정적 검증: `node --check apps/dashboard/static/dashboard/js/dashboard.js`
exit 0, `msgfmt --check-format` ko/en djangojs 통과.

### FE-SOC-01 (Lane C 프런트, 2026-08-16 같은 샌드박스)

allauth의 `socialaccount_sociallogin` 세션 stash를 직접 만들어 provider
왕복 없이 `/accounts/3rdparty/signup/`에 진입했다(격리 브라우저 컨텍스트).

- 프로젝트 템플릿(`templates/socialaccount/signup.html`) 렌더 확인 —
  Google 컨텍스트 문장, 아이디·이메일 프리필, 동의 체크박스,
  이용약관·개인정보처리방침 링크, CSRF, 로그인으로 돌아가기.
  (처음 `apps/users/templates/`에 두었더니 INSTALLED_APPS 순서상 allauth
  기본 템플릿이 이겨서 프로젝트 `templates/`로 옮겼다 — DIRS가 APP_DIRS보다
  우선.)
- 1차 제출(동의 없음): 같은 폼에 머물고 `.field-error`로
  "이용약관과 개인정보처리방침에 동의해야 가입할 수 있습니다." 표시. Pass
- 2차 제출(동의 체크): 가입 완료 → 로그인 상태로 홈 리다이렉트, 환영
  메시지. 샌드박스 DB에 User + SocialAccount 1 + seed 태그 11 확인. Pass
- 실제 Google OAuth 왕복은 provider 자격증명 없이 검증 불가(Unverified).

## 사후 리뷰 판정

- Web Experience Designer: **Conforms** — 계층·아이콘·순서·dataset 대칭·
  경고 문구/severity가 사전 사양과 일치, 브라우저 증거로 확증. 잔여 위험:
  `utils.js showNotification`의 innerHTML(기존 공용 유틸, 이번 문자열은
  정적 gettext 리터럴), 렌더 실패 분기(source-only).
- Browser Interaction Reviewer: **Conforms** — 사전 기준 6개 전부 충족을
  file:line으로 확인, 저장소 전수 grep으로 미탈출 저장형 sink 잔존 없음.
  지적: `apps/dashboard/tests.py`의 JS 소스 문자열 검사 테스트(중복 정의)가
  깨질 예정 → Frontend Work Policy에 따라 본 작업에서 삭제함.
  `index.html:237`의 인자 없는 `onclick="saveSlot()"`은 사용자 값이 닿지
  않아 기준 위반 아님(후속 정리 후보).
- Quality Verification Lead 완료 판정: 두 판정 모두 Conforms이고 FE
  시나리오 5종 + 중복 listener·취소 경로가 브라우저 실측으로 통과했으므로
  Lane B 완료로 판정. 단 렌더 실패 경고 분기 브라우저 실행과 스크린리더
  실통과는 Unverified로 유지(아래 절).

## Unverified

- 렌더 실패 경고 경로(2단계 catch)의 브라우저 실행 — 소스 리뷰만
  (렌더 실패를 실제로 유발할 자연스러운 방법이 없어 injection 없이는
  관찰 불가; 문구·severity는 카탈로그·소스로 확인).
- 스크린리더 실통과.

## 관찰 (수정하지 않음)

- 1024px에서 긴 memo가 삭제 버튼 폭을 좁혀 버튼 라벨이 세로로 줄바꿈될
  수 있다(기존 flex 동작, 이번 변경과 무관).
- ko/en `djangojs.po`에 이번 변경 전부터 미번역 1건씩 존재
  (en: 색 안내·가입 동의 문구) — HEAD에서 재현, Lane B 범위 밖.
- `showNotification()`(`apps/core/static/core/js/utils.js`)의 message
  innerHTML 보간은 반사형(서버 오류 문자열) 경계로 이번 저장형 XSS
  범위 밖 — 후속 하드닝 후보(리뷰어 권고).
