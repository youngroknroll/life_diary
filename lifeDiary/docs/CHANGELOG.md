# LifeDiary 변경 기록

작업이 끝날 때마다 맨 위에 한 항목을 더한다. 계획은 채팅에서 승인받고, 끝난 일만 여기에 남긴다.
2026-08 이후는 날짜·유형·요약·검증·PR을 적고, 그 이전은 한 줄로 줄였다.
미뤄 둔 일은 맨 아래 "미해결"에 모은다. 로드맵 문서 네 개는 `docs/plans/`에 그대로 있다.

유형: feat 기능 · fix 결함 · perf 성능 · security 보안 · refactor 구조 · ci 배포·자동화 · docs 문서 · test 테스트

---

## 2026-10

### 2026-10-08 — 하네스 정비: 어댑터 한 벌, 프로젝트 훅 4종, 경로 한정 규칙 [docs]
- 어댑터를 `lifeDiary/.claude/agents/` 11개 한 벌로 합쳐 추적한다. git 루트 `.claude/agents/`의 구판 12개(8월 14일판. `prompt_plan.md`, `.docs/frontend-integration-changelog.md`, "work logs and project status", DRF를 참조했고 구현 역할 3개는 그 구판이 활성이었다)와 범용 `project-planner-pm.md`를 지웠다. `lifeDiary/.gitignore`는 `.claude/*` 중 agents·hooks·rules·settings.json만 추적한다.
- 훅을 전역 `~/.claude`에서 프로젝트 `.claude/settings.json`으로 옮기고 둘을 더했다. `bash_guard.py`: main에서 commit·push·merge, main으로 push, `gh pr merge`, 태그 생성, `conda run -n knou-life-diary` 밖의 pytest·manage.py·pip·.venv·uv 거부. `frontend_comment_guard.py`: 템플릿·CSS·JS에 새 주석 거부(`(사용자 승인 YYYY-MM-DD)` 표기는 통과). `changelog_defer_guard.py`, `defect_deferral_guard.py`는 옮기면서 Bash 검사를 명령 조각 단위로 바꿨다(다른 파일의 `sed -i`와 CHANGELOG `git add`가 한 명령에 있으면 거부하던 오탐을 이 작업에서 고쳤다).
- `AGENTS.md`: Prime Directive 6(에이전트 git 금지)이 커밋 규칙과 모순되던 것을 "에이전트가 커밋·push·PR, 머지·태그·main은 사용자"로 고쳤다. Test Authoring Policy는 `.claude/rules/backend-tests.md`, Frontend Work Policy·Dual Review Gate는 `.claude/rules/frontend.md`로 옮겨 해당 파일을 읽거나 고칠 때 자동으로 실리고, 본문에는 요약과 Test List 표만 남겼다(928→791줄). 절대 경로와 "status index" 참조를 지우고 "Enforced By The Harness" 표를 더했다. 실행 순서 4항(모바일 통계 UX·차트 지연 렌더)은 미해결 C-14로 옮겼다.
- `CLAUDE.md`(176줄): `.claude/` 구성, "Enforced Mechanically", "Communication"(한국어·결론 먼저·비유 없이) 절을 더했다.
- `deploy.yml` 제외 규칙에 `lifeDiary/.claude/`를 더했다.
- 검증: 훅 파이프 테스트 78건 통과(bash·주석 50, CHANGELOG 16+조각 단위 7, Stop 5), `python3 -m py_compile` 4개, `jq -e` 등록 4개, 어댑터 frontmatter 11개 파싱, 지워진 경로 참조 grep 0건, 제외 규칙 grep 확인. 세션 내 실증: 프로젝트 훅이 `pytest --version`, CSS 주석 Write, 미해결 결함 줄 Edit을 거부했다. Stop 훅은 턴이 끝날 때만 돌아 파이프 테스트로만 확인했다.
- PR #90.

### 2026-10-08 — 문서 정리: 작업별 계획·로그를 이 파일 하나로 [docs]
- `docs/plans` 67개, `docs/refactoring` 59개, `docs/frontend` 20개, `docs/project-status.md`를 지우고 이 변경 기록으로 합쳤다. 로드맵 계획 4개(데스크톱 인증·패키징, 배포·수익화, 광고 전략)는 남겼다.
- 작업 규칙을 바꿨다. 계획 문서 대신 채팅에서 계획을 승인받고, 끝나면 여기에 항목을 더한다(`AGENTS.md`, `CLAUDE.md`. 로컬 어댑터 `lifeDiary/.claude/agents`는 그때 gitignore 상태라 로컬에서만 맞췄고, 같은 날 하네스 정비 항목에서 한 벌로 합쳐 추적했다).
- 결함 미루기 금지 규칙을 더했다. 진행 중 발견한 결함은 그 작업 안에서 고치고, 미루는 것은 사용자가 승인한 항목만 "(사용자 승인 날짜)" 표기로 미해결에 적는다. 사용자 환경의 훅 두 개(Stop: 응답의 결함 미루기 문장 감지, PreToolUse: 미해결 절 결함 추가·Bash 우회 편집 거부)가 강제한다.
- README와 `docs/architecture` 가이드를 2026-10-08 코드 기준으로 갱신했다(커밋 31374af, dbcb051).
- PR #90 (#89 위에 쌓음).

### 2026-10-07 — 목표 표: 삭제 문구 전달, 요청 중 잠금, 편집 값 보존 [fix]
- 삭제 뒤 포커스가 가는 "되돌리기" 버튼에 `aria-describedby`로 스낵바 문구를 붙여 스크린리더가 어떤 목표를 지웠는지 읽는다.
- 요청 하나가 진행되는 동안 다른 행 저장·추가·확인 줄 "삭제"·되돌리기 버튼을 `disabled`로 잠그고 흐리게 보인다. 누른 버튼은 `aria-disabled`라 포커스가 `<body>`로 떨어지지 않는다. "처리 중..."이 요청이 끝날 때까지 남는다.
- 응답이 본문을 갈아끼울 때 다른 행·추가 폼의 편집 값과 열려 있던 삭제 확인 줄을 되돌려 넣는다. 다른 요청 중에는 8초 자동 숨김을 보류했다가 끝난 뒤 다시 8초.
- 375px에서 스낵바가 하단 탭바와 겹치고 되돌리기 버튼이 30px 폭으로 줄바꿈되던 것을 고쳤다(탭바 위 26px, 67×44px).
- 변경: `apps/users/static/users/js/goals.js`, `apps/users/templates/users/goals.html`, `apps/core/static/core/css/style.css`.
- 검증: 전체 pytest 721 passed, `manage.py check` 0건, `node --check` 통과. 브라우저(격리 DB, fetch 지연 12~25초·실패 흉내) 1280px 라이트 en, 375px 다크 ko, 820px. 두 프런트 검토자 Conforms, 품질 검증 Complete with residual risk(실기기 스크린리더·모바일 미확인).
- PR #89 (커밋 eb08535, 16b0be8).

### 2026-10-07 — 목표 표: 고친 칸의 오류 표시 해제, 되돌리기 중 스낵바 유지 [fix]
- 거부된 칸을 고치면 그 칸이 속한 묶음의 `aria-invalid`·오류 색을 바로 지운다(기한 ← 날짜·기한 없음, 시간 ← 시간·기간, 중복 ← 태그·기간). 남은 표시가 없으면 오류 문구를 지우고 추가 폼은 힌트를 되돌린다.
- 되돌리기 요청이 나가면 자동 숨김을 멈추고, 실패하면 스낵바를 남긴 채 8초를 다시 센다.
- 검증: 전체 pytest 721 passed. 브라우저 표시 해제 8가지, 타이머 4가지. 두 검토자 Conforms.
- PR #89 (커밋 46f7f7e, 67a2425).

### 2026-10-07 — 목표 표: 저장 뒤 포커스 복원, 원인 칸만 오류 표시, 쌓기 배치 탭 순서 [fix]
- 본문을 다시 그린 뒤 포커스를 경로별로 되돌린다(저장 → 같은 칸, 422 → 첫 오류 칸, 추가 → 추가 폼 태그, 삭제 → 되돌리기 버튼). Chrome은 포커스된 버튼이 `disabled`가 되면 포커스를 `<body>`로 떨어뜨린다는 사실을 확인했다.
- 뷰가 `error_field`를 넘기고 템플릿이 그 칸에만 `aria-invalid`·`aria-describedby`를 붙인다. CSS는 `[aria-invalid="true"]`만 칠한다. 중복 오류는 태그·기간 두 칸.
- 992px 미만 쌓기 배치의 시각 순서를 DOM 순서(태그 → 기간·시간 → 기한)에 맞췄다.
- 검증: `test_goal_page.py` 26 passed(TDD 4건, 특성 테스트 2건은 변이로 확인), 전체 721 passed. 375·820·991·992·1280px.
- PR #89 (커밋 62528de, 2830a5f, 920a599).

### 2026-10-06 — 목표 기한과 D-day 알림 [feat]
- `UserGoal.due_date`(선택)와 순수 모듈 `goal_deadline.deadline_state`. "기한 없음"이 날짜보다 우선, 체크를 풀고 비우면 거부, 과거 날짜는 새로 정하거나 바꿀 때만 거부(되돌리기는 예외).
- 배지: D-4 이상 중립, D-3~당일 경고, 지나면 "기한 지남". 목표 표·진행률 카드·통계 진행 행에 표시. 대시보드 배너는 지난 3일~앞 7일 중 가장 급한 1건 + "그 외 N건".
- 통계 캐시에는 `due_date`만 담고 상태는 요청한 날 기준으로 붙인다. 캐시 키 `:v3` → `:v4`.
- 변경: `apps/users/{models,forms,use_cases,repositories,views,goal_deadline}.py`, 마이그레이션 `users/0005`, `apps/stats/aggregation/goal_progress.py`, `apps/dashboard/views.py`, 템플릿·CSS·JS, locale 4파일.
- 검증: 전체 pytest 721 passed(기준선 692), prod deploy check exit 0, `msgfmt --check-format` 통과. 브라우저 375·820·992·1280px, 다크·라이트, ko·en. 두 검토자 Conforms.
- PR #89 (커밋 902c2d8 ~ 8cfd574).

### 2026-10-06 — 탈퇴 계정 purge를 GitHub Actions로 매일 실행 [ci]
- `.github/workflows/purge-deleted-accounts.yml`: 매일 03:47 KST `purge_deleted_accounts`. 실패하면 GitHub 알림. 사용자가 시크릿 5개를 등록했다.
- PR #86.

### 2026-10-06 — TimeBlock 태그 필수화 [fix]
- 마이그레이션 `dashboard/0007`이 태그 없는 기록 190건을 지우고 `tag`를 NOT NULL로 바꿨다(사용자가 CSV로 보관). 통계 창 픽스처에서 태그 없는 기록을 뺐다.
- 검증: 전체 pytest 692 passed.
- PR #85.

### 2026-10-06 — 통계 캐시 세대 키 운영 측정 [docs]
- 미스 TTFB 중앙값 969ms(쿼리 5개), 적중 485ms. 다른 날짜의 기록을 저장하면 적중이던 날짜가 미스로 바뀌는 것을 확인했다.
- PR #88.

### 2026-10-04 — Critical Remediation 미반영 커밋 선별 재적용 [fix] [security]
- 2026-08-15~16에 로컬 브랜치에만 있던 커밋 13개를 `main`과 대조해 필요한 것만 다시 적용했다.
- 그대로 옮김: 옮길 곳 없는 태그 삭제가 기록·메모를 함께 지움, 탈퇴 취소 뒤 재요청(`IntegrityError` 수정), `purge_deleted_accounts --check`.
- 재구현: 가입 트랜잭션(기본 태그 시드 실패 시 롤백), Google 가입자 기본 태그와 유예 중 Google 로그인의 탈퇴 취소(유예 뒤 로그인은 비활성 유지), 통계 캐시를 사용자별 세대 토큰으로 키잉(`:v3`), 기록·태그·목표·메모 변경을 커밋 뒤 시그널로 알림, 주간 활동 시간의 수면 제외를 카테고리 slug로 판정.
- 추가: 태그 삭제 API가 깨진 본문을 400으로 거절. Google 가입 이메일은 제공자가 준 주소로 저장하고 제공자가 인증한 주소만 인증 표시.
- 프런트: 기록 삭제 성공 뒤 "삭제 실패"를 띄우고 행을 되살리던 버그(`deleteSlot`의 미선언 변수, 2026-08-12부터) 수정.
- 검증: 전체 pytest 691 passed, prod deploy check exit 0. 삭제 흐름 브라우저 확인. Supabase RLS 경고 14개 테이블은 사용자가 SQL로 해소.
- PR #83.

### 2026-10-02 — 통계 쿼리 통합 2단계: 요청당 기록 1회 읽기 [perf]
- `get_stats_context`가 모든 집계가 쓸 창(기준일 주 시작 12주 전 ~ 주 끝·달 끝 중 늦은 날)을 한 번 읽고, 각 집계가 제 기간만 잘라 쓴다. 카테고리도 한 번만 읽는다. 결과 값과 캐시 키는 그대로.
- 로컬 쿼리 수 목표 0/6/12개 모두 5개(기록·카테고리·메모 각 1, 목표 2). 상한 18 → 5. 창이 기간을 덮지 못하면 상한을 넘겨 같은 테스트가 잡는다.
- 운영: 미스 TTFB 중앙값 2,291ms → 1,144ms(09-30 기준 −65%), db 569ms, 적중 446ms.
- 검증: 시나리오 WQ-01~14 + WQ-08b, 전체 pytest 671 passed.
- PR #80, 배포 PR #81.

### 2026-10-01 — 통계 쿼리 통합 1단계: 목표별 조회 제거 [perf]
- 목표 진행 바가 목표마다 기록을 따로 조회하던 N+1을 없애고 모든 목표 기간을 덮는 범위를 한 번 읽는다. 목표 0/6/12개 쿼리 18/25/31 → 18/20/20.
- 운영: 쿼리 29 → 20, 미스 TTFB 3,294ms → 2,291ms(−30%). 쿼리당 84.5ms는 그대로(Render 싱가포르 ↔ Supabase 도쿄 왕복 약 70ms).
- INP: `/stats/` 32ms 이하, `/dashboard/` 16~40ms.
- 검증: GQ-01~03(Red 6==2 → Green), 전체 pytest 620 passed.
- PR #77, #78, 배포 PR #79.

### 2026-09-30 — 통계 페이지 Server-Timing 헤더 [feat]
- `GET /stats/` 응답에 캐시 hit/miss, 생성 시간, DB 시간, 쿼리 수를 담은 `Server-Timing` 헤더. `prod.py`의 `STATS_SERVER_TIMING_ENABLED`(기본 꺼짐, 사용자가 켜 둠). SQL·키·사용자 정보는 넣지 않고, 계측 실패 시 헤더만 빠진다.
- 운영 측정: 처음 연 날짜 5개 모두 miss, 재조회 모두 hit. miss TTFB 중앙값 3,294ms 중 DB 2,363ms(72%, 쿼리 29개).
- 검증: 시나리오 11개 Green, 보안 검토 9개 기준 충족, 전체 pytest 617 passed.
- PR #76, 배포 PR #75.

### 2026-09-30 — 통계 전체 요청 성능 측정 도구 [test]
- `/stats/` 요청을 전체·렌더 전후·쿼리 수·SQL 시간·캐시 백엔드로 쪼개 재는 테스트 전용 도구(`apps/stats/conftest.py`). cold 5회·warm 5회.
- 로컬 SQLite cold 298ms(쿼리 21), warm 17ms(쿼리 3). 로컬 PostgreSQL cold 849ms. 운영 브라우저 TTFB 처음 2,817ms, 재조회 454ms, CLS 0. 모바일 에뮬레이션에서 폰트 2MB가 load 약 15초(미해결 C-6).
- PR #74.

## 2026-08

### 2026-08-31 — 서치 콘솔·GA4·sitemap [feat]
- 공개 페이지에 서치 콘솔 확인 태그, GA4, `sitemap.xml`. `robots.txt`는 홈만 색인 허용, sitemap 크롤 허용(09-02 수정).
- PR #71.

### 2026-08-31 — Lighthouse 최적화 [perf]
- 미사용 스크립트 제거와 `defer` 전환으로 렌더 차단 해소, 제거된 `STATICFILES_STORAGE`를 `STORAGES`로 이전, 언어 버튼 접근 이름에 코드 포함, 파비콘을 파스텔 파이 차트로 교체.
- PR #68.

### 2026-08-25 — 이메일 6자리 코드 인증 (가입·비밀번호 재설정) [feat] [security]
- 가입 즉시 로그인시키던 흐름과 링크 기반 재설정을 코드 인증으로 바꿨다. 모델 2개(`EmailVerification`, `EmailVerificationCode`), 기존 계정은 인증 완료로 backfill. 코드는 해시로만 저장, 수명 10분, 코드당 3회, 재발송 60초 쿨다운·1시간 5회. 데스크톱 설정은 끈다.
- `allauth.urls` 전체 include 때문에 `/accounts/password/reset/`에 링크 방식이 살아 있던 결함을 닫고, allauth는 소셜 경로만 include(`SOCIALACCOUNT_AUTO_SIGNUP = False`). 소셜 화면 3종을 시안대로 오버라이드.
- 프런트 이중 검토에서 결함 5건(소셜 화면의 실시간 아이디 검사 JS가 폼 id 불일치로 죽어 있음 등)을 고쳤다. 템플릿 주석이 화면에 새던 것을 막고 프런트 주석 금지를 규칙으로 남겼다.
- 검증: 전체 pytest 592 passed, 카탈로그 미번역·fuzzy 0건.
- PR #62, #66.

### 2026-08-25 — production 배포 트리에서 문서 제외 [ci]
- `deploy.yml`이 `lifeDiary/docs/`, `.claude/`, README, 거버넌스 파일을 운영 브랜치에서 뺀다.
- PR #63.

### 2026-08-18 — 분석 차트 카테고리 색·범례 고정 해소 [fix]
- 차트 선 팔레트가 파스텔 개편 이전 값이었고, 테마 감지가 존재하지 않는 `#themeToggle`을 보고 있었다. 범례 고정 원인까지 셋을 고쳤다.
- PR #61.

### 2026-08-17 — 목표 관리 페이지 통합 [feat]
- 껍데기 없이 그려지던 목표 화면을 목록·진행률·인라인 수정·추가·삭제·되돌리기 한 화면으로 모았다. 변경 뷰가 본문 조각을 직접 돌려준다(422는 오류 문구 포함). 중복 검증은 `UserGoalForm.clean()`. 진행률이 붉어지는 조건은 "페이스보다 뒤처짐"으로 통일.
- 브라우저에서 잡은 결함 3건: 전면 로딩 오버레이가 영영 안 걷힘(`base.html` 링크 핸들러, 별도 커밋), UA 포커스 링, 375px 줄바꿈. i18n fuzzy 오상속 1건 교정.
- 검증: 전체 pytest 543 passed. 1440/768/375/360px × 라이트·다크 × ko·en.
- PR #56.

### 2026-08-17 — 헤더 테마·언어 컨트롤 [feat]
- 마이페이지 안에만 있던 테마·언어 선택을 헤더로 옮겨 비로그인 사용자도 쓴다.
- PR #58.

### 2026-08-17 — 백로그 통합 [docs]
- 여러 실행 로그의 Deferred를 성격별(A 배포·운영, B 백엔드, C 프런트, D 테스트, E i18n, F 장기)로 모았다. 지금은 이 파일의 "미해결".
- PR #55.

### 2026-08-16~17 — P0 v2 UI 핸드오프 이식 6단계 [feat]
- Claude Design 명세 v2를 폰트·오버레이·clamp → `category_stats` 집계 → `stats.js` 전면 재작성(카테고리 5선, 테마 동기화, HTML 범례) → segmented 전환 + 목표 진행 바(페이스 마커) → 입력 패널·모바일 바텀시트(80dvh, 스와이프 닫기) → 인증·온보딩·설정·홈 순으로 이식했다.
- 분석 화면 가독성 3건(툴팁 글자색, 히트맵 축 설명, 범례)도 함께.
- 검증: 단계마다 브라우저 실측. 전체 pytest 543 passed.
- PR #54, #57.

### 2026-08-16 — JSON API의 django-ninja 이식과 OpenAPI/Swagger [refactor]
- 엔드포인트 5개(time-blocks 저장/삭제/undo, categories, tags CRUD)를 URL·응답 봉투를 보존한 채 ninja 라우터로 이식. `/api/docs`, `/api/openapi.json`. 전역 예외 핸들러로 401 `UNAUTHORIZED`, 400 `VALIDATION_ERROR`·`INVALID_JSON`, 404 `TAG_NOT_FOUND`. 문서에서 엔드포인트가 빠지면 실패하는 계약 테스트.
- 안내: `docs/architecture/2026-08-16_api-documentation-guide.md`.
- PR #53.

### 2026-08-14 — 그리드 태그 라벨 위치와 24:00 경계 [fix]
- 라벨이 "폭 3칸 이상인 첫 행"에 붙던 규칙을 없애고, 라벨이 옮겨간 인접 시간이 변이 응답에 빠지던 결함(`hours_to_refresh` ±1시간)을 고쳤다. 세로 시간축에 24:00 끝선.
- 검증: 전체 pytest 501 passed.
- PR #49.

### 2026-08-14 — CSRF 신뢰 도메인 등록 [fix]
- PR #47, 배포.

### 2026-08-13~14 — 월간 엑셀 내보내기, 호버·포커스·눌림 상태 복구 [feat]
- `openpyxl`로 월간 기록 워크북. 내보내기 버튼의 진행 상태 전환에서 스크린리더 미공지·포커스 유실을 고쳤다. 다크 primary 버튼 대비.
- PR #46.

### 2026-08-12 — 운영 도메인 `lifediary.kr` [ci]
- `ALLOWED_HOSTS` 등록만으로 동작 확인. `production` 브랜치에 직접 들어간 수정을 `main`이 따라잡게 했다.

### 2026-08-10~12 — 시안 정합 재작업 7단계 [feat]
- 시안 22화면을 전수 대조해 격차를 메웠다. 1~3 스킨 잔재·인증 화면·태그 모달·이름 10자. 4 **모든 태그를 개인 소유로**(`Tag.user` NOT NULL, `is_default` 폐지, 되돌릴 수 없는 마이그레이션). 5 달성률 분모를 지난 시간 기준으로, 룰 기반 피드백을 사실 관찰로 교체. 6 빈 상태와 온보딩 3단계. 7 태그 관리를 행 리스트로 재작성(행 드래그·인라인 편집은 미채택).
- 2026-08-10 전수 점검의 P0 네 건(기본 태그 교차 소유권, gettext 카탈로그, Shift+Arrow 오류, inline JS 경계)이 이 작업으로 닫혔다.
- 검증: 전체 pytest 466 passed(08-12).

### 2026-08-01~02 — P0 시안 리디자인 [feat]
- 내비게이션 홈·기록·분석·설정 4개와 모바일 탭바. 기록 그리드 24행 × 6열, 같은 태그 연속 칸 병합, 키보드 경로. 저장·삭제 뒤 부분 갱신과 60초 되돌리기. 분석 요약·일·주·월 4탭, 집계 4종 신설(`comparison`, `density`, `goal_progress`, `summary`). 색은 카테고리가 정한다.
- 결정: 주 기간은 달력 주(월~일). 프런트엔드 소스 문자열 검사 테스트 12건 제거. Git은 에이전트가 직접 실행.
- PR #40 (머지 08-11, 커밋 30개).

## 2026-07

### 2026-07-18 — 전수 검토와 조치 [fix] [security]
- ko 카탈로그 빈 `msgstr` 377건 항등 번역(테스트 28건 실패 해소), `SECURE_PROXY_SSL_HEADER`·CSRF 신뢰 오리진·CSP 미들웨어, dashboard–stats 의존 역전과 users 레이어링, 모바일 바텀시트 Escape 닫기·포커스 트랩. 검토 보고서: `docs/2026-07-18_comprehensive-project-review.md`.
- 07-31 `ALLOWED_HOSTS`에 `lifediary.kr`, `www`.

## 2026-05

- 05-30 운영 배포(#35~#38).
- 05-26 계정 탈퇴 15일 유예 삭제(요청 시 비활성, 유예 중 로그인은 취소, `purge_deleted_accounts`), 약관 저작권 조항, pytest gettext 부재 허용.
- 05-25 공개 정책 페이지 `/privacy/`·`/terms/`, 반복 실패 뒤 로그인 reCAPTCHA, pytest 시작 시 카탈로그 컴파일, 머지 설명 생성 스크립트, 태그 UI·재설정 링크 개선.
- 05-24 운영 콘솔 로깅, 공유 태그 카테고리 헤더 partial, 태그 색 추천 14색, 재설정 메일이 요청 호스트 사용.
- 05-23 모바일 시트 높이·뷰포트 유지, 태그 안내 이미지 로컬라이즈.
- 05-22 Google 로그인(`django-allauth`).
- 05-20 로그인·복구 보안 강화, Gmail SMTP 전환, 대시보드 퀵 입력 상태 안내, `robots.txt`, 푸터 연락처, 모바일 터치 드래그.
- 05-19 헤더 유틸리티 컨트롤과 시간 그리드 드래그, 인증 쿠키·로그인 보안 1단계.
- 05-18 푸터 저작권 LogBetter.
- 05-15 라이프 피드백 토글, 모바일 입력 바텀시트, 영어 태그 안내 이미지, 운영 메일 준비.
- 05-11 운영 메일 Resend API 전환(뒤에 Gmail SMTP로 돌아감), gh CLI 재시도.
- 05-09 아이디 찾기 SMTP 실패 처리.
- 05-07 데스크톱 앱 Phase 0(pywebview + waitress 런처, desktop 설정), 가입 실시간 검증·비밀번호 강도·표시 토글·Caps Lock 안내, 로그인 상태 유지, 가입 직후 환영 화면, 통계 모바일 섹션 일렬·목표 accordion, 테스트 비밀번호 리터럴 제거(GitGuardian).
- 05-05 README 갱신, 워크플로를 레포 루트로.
- 05-02 통계·태그 카테고리 한/영 전환 수정.
- 05-01 계정 복구(아이디·비밀번호 찾기)와 이메일 인프라.

## 2026-04

- 04-28~30 ko→en i18n 1~5단계(`LocalizableMessage`, JS 카탈로그), unittest → pytest 전환(111 passed), `.mo` 트래킹과 번역 수정.
- 04-26 통계 `UserGoal` 조회 3회 → 1회, 월간 데이터 lazy 캐시.
- 04-24 태그 범례 클릭·사이드바 카테고리 그룹, 날짜 변경 시 활성 탭 유지.
- 04-22~23 프런트 DRY(`apiCall`, 로딩 오버레이, 삭제 확인·폼 오류 partial), 저장·삭제 오버레이와 드래그 개선, 삭제 시 통계 캐시 무효화 누락 수정.
- 04-21 보안 3종(저장형 XSS, `django-axes` 브루트포스 방어, CDN SRI — `docs/security/`), 템플릿 정리(partial 추출, `ai_feedback` → `life_feedback`), 마이페이지 목표 AJAX 갱신, 주간 "가장 활발한 요일" 버그. 테스트 55 passed.
- 04-20 아키텍처 3~4단계: Port `Protocol` + Pydantic Command, Use Case 계층, 통계 페이지 캐싱, `StatsCalculator` 분해, Supabase 연결 최적화, `success_response` 평탄화.
- 04-18 다크모드(시스템 감지 + 토글), i18n 인프라 0단계, 피드백 개편, 목표 추가 중복 제출 방지.
- 04-16 그리드 2D 범위 선택.
- 04-15 인라인 JS 정적 파일 추출, 사이드바 UX, 태그 배경 대비 글자색 자동.
- 04-13 카테고리(대분류) 계층 추가.
- 04-11~12 CSS 디자인 토큰 통합, 홈 개편, 모바일 반응형, 로딩 모달 버그.
- 04-08~09 코드 리뷰 기반 수정(16/23 → 잔여 7개), Repository 1단계·Domain Service 2단계, `uv`, settings 분리.

## 2025-07 ~ 2025-09

- 07-21 Django 초기 세팅. 07-23~25 기록 슬롯·태그·통계·로그인(PR #3~#7), AI 피드백, Render 배포(gunicorn, PostgreSQL, whitenoise). 07-26 기본 태그와 태그 설명. 07-31 로딩 모달, 목표 달성률 표시 조정. 08-01 세션 타임아웃, 목표 시간 제한. 08-09 리뷰 수정(PR #11). 09-18 로딩 모달 오류·파비콘·설정.

---

## 진행 중인 계획 (문서로 유지)

| 문서 | 범위 | 상태 |
|---|---|---|
| `docs/plans/2026-05-07_desktop-auth-single-user-plan.md` | 데스크톱 단일 로컬 사용자 자동 로그인, 인증 화면 차단 | 설정·런처만 있고 로컬 사용자 부트스트랩·미들웨어는 미구현 |
| `docs/plans/2026-05-03_desktop-app-packaging-plan.md` | pywebview + waitress + PyInstaller로 macOS `.app`·Windows `.exe` | PyInstaller spec·데스크톱 README·릴리스 워크플로 없음. desktop 설정은 allauth URL 불일치로 `manage.py check` 실패(기존) |
| `docs/plans/2026-05-06_distribution-and-monetization-plan.md` | 공개 배포, 운영 가시성, 수익화 실험 | 로드맵. 단계마다 승인 필요 |
| `docs/plans/2026-05-28-ad-revenue-marketing-strategy.md` | 공개 콘텐츠 페이지와 보수적 광고로 월 약 3만 원 서버비 충당 | 계획 범위. 광고는 공개 페이지에만, 단계 승인 뒤 |

## 미해결

항목 번호는 2026-08-17 백로그 통합 때의 것을 이어 쓴다. 해소된 것은 지웠다.

### 운영·배포
- A-2 보안 잔여: 쿠키·보안 플래그 재점검, 로그인 실패 알림 (`docs/security/2026-04-21_xss-bruteforce-sri-remediation.md`).
- A-3 배포된 `Set-Cookie`·`SECURE_PROXY_SSL_HEADER` 실측.
- A-4 메일 발신: Gmail SMTP. 전용 발신 도메인·DNS·발송량 한도 확인 전.
- A-7 로그인 후 응답에 `Cache-Control: private, no-store` 명시(지금은 Cloudflare가 `DYNAMIC`으로 캐시하지 않음).
- A-9 DB 연결 재수립 비용(첫 요청 약 670ms, 1회 관찰). `CONN_MAX_AGE` 뒤 도쿄 풀러 재연결 가설.
- A-10 서버·DB 리전 일치(Render 싱가포르 ↔ Supabase 도쿄, 쿼리당 81~85ms). 사용자가 보류.
- 에러 추적·메트릭 미연동. 배포 콘솔 로그와 통계 `Server-Timing`뿐.
- 캐시 쓰기 실패 시 통계 요청 500. 운영 파일 캐시는 인스턴스 하나 전제.
- Google 가입이 제공자 미인증 주소도 받음(인증 표시만 한정). 관리자 화면 편집은 캐시 세대를 바꾸지 않음. purge 때 캐시 잔존.

### 백엔드
- B-1 마이페이지 목표 추가 POST 분기와 `mypage_goals_partial` 고아화 정리. `goals.js`가 `usergoal_form.html`을 계속 쓰는지 확인 뒤.
- B-2 `category_guide`의 `@login_required` 제거(공개 콘텐츠 단계, 보안 검토 동반).
- B-4 `Tag.color` 컬럼 드롭 여부(지금은 `save()`가 카테고리 색을 복사).
- B-5 온보딩 칩의 "추천" 상태에 필요한 백엔드 신호.
- B-7 측정 헬퍼(`apps/stats/conftest.py`) 일반화. B-9 `_QueryTimer`를 `apps/core`로. 둘 다 두 번째 사용처가 생길 때.
- B-8 `Server-Timing` 부착에 `status_code == 200` 명시 확인.
- B-10 기록 저장 API TTFB 약 1.2초(쿼리 수·DB 시간 미계측). 되돌리기도 비슷.
- 목표 (사용자, 태그, 기간) 유일성 DB 제약. `calculator=None` 두 경로 정리. `find_daily_counts` 운영 호출 없음. hit 경로 쿼리 3개.
- 데스크톱: 단일 로컬 사용자 인증, 패키징(위 계획 문서).

### 프런트엔드·정적 자산
- C-1 죽은 CSS(`.home-daygrid*`, `.navbar-utility-controls` 등) 삭제 — D-2와 함께.
- C-2 미참조 이미지 `tag_usage_guide*.png` 2.1MB 삭제 여부(사용자 확인 필요).
- C-3 FontAwesome 전역 제거(템플릿 7개, `showOverlay` 아이콘).
- C-4 44px 터치 타깃 전역 재확인(`.segmented__item` 약 28px, 시트 닫기 32px 등).
- C-5 `.chip__swatch`·`.category-picker__swatch` 라이트 대비(1.44~2.15), 공용 테두리 규칙.
- C-6 `PretendardVariable.woff2` 2.0MB 서브셋 파이프라인(Slow 4G에서 약 14초).
- C-7 확인 모달 없는 태그 삭제의 이중 제출 가드. C-8 sessionStorage 차단 시 온보딩 STEP3 안내.
- C-9 `renderRows`가 다시 그리는 행의 미래/현재 음영 오버레이를 지움(새로고침하면 복구).
- C-10 시안 1a 라이트 모드 work 라인 아래 영역(장식, 두 번 보류). C-11 `NEUTRAL_COLOR = "#8A9A91"`의 출처 확인.
- C-12 저장 응답 직후 139~351ms 긴 프레임. C-13 응답 대기 중 새로 고른 칸 선택이 `clearSelection()`으로 지워질 가능성.
- C-14 모바일 통계·대시보드 UX 잔여 항목과 통계 차트 지연 렌더(`AGENTS.md` 실행 순서 4항에서 옮김, 2026-10-08).
- `dashboard.js` `#undoSnackbar`: 숨김→표시 때 문구 전달 장치 없음, 다시 그리기 뒤 포커스 복원 없음.
- 목표 표: 되돌리기 한 단계(8초 안 연쇄 삭제의 첫 목표는 복원 불가). 자동 숨김으로 포커스가 추가 폼으로 갈 때 이유를 알리지 않음. 오류 문구를 칸마다 따로 두는 구조.
- 실기기 스크린리더(NVDA·VoiceOver)·실제 모바일 기기·Safari 클릭-비포커스 경로는 어느 작업에서도 확인하지 않았다(접근성 트리·에뮬레이션으로 대신).

### 테스트
- D-1 JS/CSS 소스 문자열 검사 테스트 삭제(Frontend Work Policy 위반 형태). D-2 `test_time_grid_prevents_text_selection`이 C-1의 죽은 CSS를 단언 — C-1과 한 트랙.
- D-3 `test_selected_slot_info_prompts_tag_selection` 중복 정의(뒤엣것이 덮음).
- D-4 로케일 파라미터화 확대, `factory_boy` 검토, 로케일 누수 가드.
- 설정 화면(`mypage`) POST 경로의 직접 테스트.

### i18n
- E-1 일본어 지원, 캐시 키 로케일 분리, Chart.js 로케일.
- E-2 JSON 응답의 로케일 처리를 ninja 기준으로 재규정.

### 장기
- F-1 API: rate limiting, 토큰 인증, 버저닝, PyInstaller ninja 정적 번들.
- F-2 데스크톱 배포: 코드 서명, 공증, 자동 업데이트, 운영 지표, 수익화 단계.
- F-3 계정 복구: 이메일 백필 정책.
- F-4 스테일 원격 브랜치 11개 정리.
