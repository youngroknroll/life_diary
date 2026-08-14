# 분석 화면 엑셀 내보내기 — 상호작용 결함 2건 수정

날짜: 2026-08-13

## 배경

`stats:index` 의 엑셀 내보내기 버튼(`#statsExportBtn`)이 제출 시
"다운로드" → "내보내는 중…" 으로 라벨을 바꾸고 4초 뒤 되돌리는 기존 동작에서
두 결함이 지적됐다.

- 결함 1 (High): 라벨 전환이 스크린리더에 알려지지 않는다.
- 결함 3 (Medium): `button.disabled = true` 가 포커스를 `<body>` 로 떨어뜨리고,
  4초 뒤 복구하지 않는다.

두 리뷰어(Web Experience Designer, Browser Interaction Reviewer)의 구현 전
설계가 확정되어 그대로 구현했다.

## 변경 파일

- `apps/stats/templates/stats/index.html`: `#statsExportBtn` 바로 뒤에
  `#statsExportStatus` (`role="status"`, `aria-live="polite"`, 시각적으로는
  숨김) 라이브 리전 추가. 저장소 관례
  (`apps/dashboard/templates/dashboard/index.html:156,253`,
  `apps/users/templates/users/mypage.html:53`,
  `apps/users/templates/users/welcome.html:46`)를 따랐다.
- `apps/stats/static/stats/js/stats.js`: 제출 시 `statusEl.textContent` 를
  `busyLabel` 로 채우고 4초 뒤 빈 문자열로 비운다(완료 문구 없음 — 4초는
  추측이지 완료 신호가 아니다). 제출 시점에 버튼이 포커스를 갖고 있었고
  (`restoreFocus`) 4초 뒤에도 포커스가 `<body>` 에 남아 있을 때만
  `button.focus()` 로 되돌린다. 실제 `disabled` 는 유지
  (`apps/core/static/core/js/utils.js:113-129` 관례와 일치).
- `apps/core/static/core/css/style.css`: `#statsExportBtn` 에
  `min-width: 132px` 추가. "다운로드"(4자) ↔ "내보내는 중…"(6자+공백)
  전환으로 버튼 폭이 바뀌어 360px 에서 select 를 밀어내는 것을 막는다.

## 검증

- `node --check apps/stats/static/stats/js/stats.js` — exit 0.
- `conda run -n knou-life-diary python manage.py check` — 이슈 없음.
- `conda run -n knou-life-diary python manage.py collectstatic --noinput` —
  정적 파일 반영 완료.
- 브라우저 검증(포커스 3가지 경우, 360px 레이아웃, 다크 테마)은 사용자가
  직접 수행하기로 했다. 이 세션에는 브라우저 도구가 없어 `min-width: 132px`
  값은 리뷰어가 제시한 시작값을 그대로 쓴 것이며, 실측 확인은 이루어지지
  않았다.

## 남은 일

- 사용자의 브라우저 실측 결과에 따라 `min-width` 값 조정이 필요할 수 있다.
- Web Experience Designer, Browser Interaction Reviewer의 구현 후 검증과
  Quality Verification Lead의 완료 판정은 브라우저 검증 완료 후 별도로
  진행되어야 한다.
