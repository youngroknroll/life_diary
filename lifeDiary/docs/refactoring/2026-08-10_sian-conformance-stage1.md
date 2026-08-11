# 시안 정합 재작업 1단계 실행 로그

계획: `docs/plans/2026-08-10_sian-conformance-remediation-plan.md`
범위: C1 · C2 · B5 · B6 · D4 + 공용 `.table-scroll`

## 한 것

### D4 비밀번호 변경 (신규)

로그인 상태에서 현재 비밀번호를 확인하고 바꾸는 흐름이 없었다.
`password_reset_*`은 비로그인 찾기 흐름이라 대체가 안 된다.

- `users:password_change` · `users:password_change_done` 라우트
- `password_change_form.html` · `password_change_done.html` — 인증 화면 스킨
  (`auth-panel`, `btn-sian`, 필드 인라인 오류)
- 설정 › 계정에 진입 행 추가

### 공용 접근성 글루

`apps/core/templatetags/form_fields.py`의 `form_field` 태그가 오류 시 입력에
`aria-invalid`와 `aria-describedby`를 붙이고, `shared/_field_errors.html`이
같은 id로 오류 노드를 렌더한다. 로그인·회원가입·비밀번호 변경이 공유한다.

`invalid=True` 인자는 폼 전역 오류(인증 실패)를 특정 필드에 귀속시킬 때 쓴다.

### B5 로그인

- 상단 `alert alert-danger` 배너 제거 → 비밀번호 필드 아래 인라인 오류
- "비밀번호가 맞지 않습니다 · N회 남음". 횟수는 **오류와 같은 노드**에 넣어
  스크린리더가 한 번만 읽는다
- `_login_attempts_remaining()` — 실패 전에는 `None`이라 첫 방문자에게
  남은 횟수를 광고하지 않는다
- 실패 후 첫 오류 필드로 포커스 이동(`auth-enhance.js`)
- 라벨 "사용자명" → "아이디"

### B6 회원가입

- `SignupForm.consent` 필수 불리언 + 전용 오류 문구
- 약관·개인정보처리방침 링크를 품은 체크박스 행(탭 순서상 확인 다음, 제출 앞)
- 버튼 "회원가입" → "가입하고 시작하기", `btn-sian` 스킨

### C1 · C2

- `btn btn-*` 잔재 제거 — `tags/index.html`, `_tag_modal.html`, `mypage.html`,
  `signup.html`
- 인라인 `<style>` 제거 2곳 — `mypage.html`, `usergoal_list.html`
  (후자의 `.goal-table` 규칙은 `style.css`로 옮김)

### `.table-scroll`

상호작용 리뷰가 "`.data-table`에 반응형 래퍼가 코드베이스 어디에도 없다"를
잡았다. 2·3단계가 표 세 개를 늘리거나 신설하므로 공용 유틸리티를 먼저 만들었다.

**CSS만으로는 포커스를 줄 수 없다.** 소비하는 쪽이 반드시
`<div class="table-scroll" tabindex="0" role="region" aria-label="...">`로
렌더해야 키보드로 잘린 열에 닿는다. 규칙 주석에 계약으로 박아 두었다.
(초판에 "포커스 가능"이라고 잘못 적었던 것을 사후 리뷰가 잡았다.)

## 검증

| 검사 | 결과 |
|---|---|
| 비밀번호 변경 | RED 6 실패 → GREEN 6/6 |
| 남은 시도 횟수 | RED 5 실패 → GREEN 5/5 |
| 동의 검증 | RED 2 실패 → GREEN 3/3 |
| 전체 회귀 | **419/419 통과** |
| `manage.py check` | 0 issues |
| 마이그레이션 드리프트 | No changes detected |
| prod `--deploy` | 에러 0 (SECRET_KEY 경고는 환경 문제, 기존) |
| `node --check` | `auth-enhance.js` 통과 |
| `msgfmt --check-format` | ko · en 통과 |

브라우저(360px, Chrome DevTools) —

- 로그인 실패 2회: 카운트 4 → 3 감소 확인
- 비밀번호 입력 `aria-invalid="true"`,
  `aria-describedby="id_password_error"`가 오류 노드 id와 일치
- 접근성 트리 description = `"비밀번호가 맞지 않습니다 4회 남음"` (단일 노드)
- 실패 후 `document.activeElement` = `id_password`
- 상단 배너 없음, 페이지 가로 스크롤 없음(`scrollWidth === clientWidth`)
- 동의 체크박스: `required`, 기본 해제, `label for` 일치, 링크 실주소,
  라벨 속 링크 클릭이 체크박스를 토글하지 않음
- 탭 순서: 아이디 → 이메일 → 비밀번호 → 확인 → 동의 → 제출
- 콘솔 에러·경고 0

## i18n 사고

`makemessages`가 새 문자열에 비슷한 기존 번역을 fuzzy로 물려줬는데, 내용을
검사하기 전에 플래그부터 걷어 한때 잘못된 번역이 활성화됐다. 특히
`비밀번호가 맞지 않습니다` → `비밀번호가 변경되었습니다`는 실패를 성공으로
말하는 오역이었다. 16개 항목을 ko·en 모두 교정했다.

**다음부터의 순서** — fuzzy 항목은 *내용을 확인한 뒤에* 플래그를 걷는다.
`msgfmt --check-format`은 포맷 지시자만 보므로 오역을 잡지 못한다.

## 남긴 것

- 터치 타깃: `.btn-sian` 40px, `.password-toggle` 38×28px. WCAG 2.5.8 AA
  (24px)는 넘지만 리뷰가 제시한 44px 게이트에는 못 미친다. 저장소 전역
  디자인 토큰이라 이번 범위에서 바꾸지 않았다 — 사용자 판단 대기
- "N회 남음"의 대상은 잠금이 아니라 reCAPTCHA 게이트다.
  `AXES_FAILURE_LIMIT`이 prod 기본 1000, dev는 axes 비활성이라 실제 잠금이
  없다. 시안 문구는 잠금을 암시한다 — 문구를 고칠지 잠금을 도입할지 미결
- 회원가입 이메일이 여전히 필수다. 시안 6f는 선택으로 그렸으나 계정 복구
  경로에 닿아 이번 범위에서 제외했다
- 카탈로그 빈 항목 ko 30 · en 18건은 이 작업 이전부터의 백로그다
