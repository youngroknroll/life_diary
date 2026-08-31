# Search Console 등록 지원 + GA4 도입 실행 로그 (2026-08-31)

계획: `docs/plans/2026-08-31_search-console-ga4-plan.md`

## 프로세스 예외

사용자가 2026-08-31 "비즈니스 로직이 아니니 TDD로 진행할 필요는 없어"로
Backend TDD Cycle(Red-Green)을 명시 웨이버했다. 구현 후 계약 보호용
테스트를 작성하는 방식으로 대체했다.

## 변경 내용

- `lifeDiary/settings/dev.py`: `GA_MEASUREMENT_ID`,
  `GOOGLE_SITE_VERIFICATION` 환경변수 설정 추가 (기본 빈 문자열).
- `lifeDiary/settings/desktop.py`: 두 값을 빈 문자열로 강제 (로컬 단일
  사용자 앱 비추적).
- `lifeDiary/settings/prod.py`: CSP에 GA4 출처 추가 — `script-src`
  `https://www.googletagmanager.com`, `connect-src`/`img-src`에
  `https://*.google-analytics.com https://*.analytics.google.com
  https://*.googletagmanager.com` (구글 공식 CSP 가이드 기준 최소 집합).
- `lifeDiary/views.py`: `_public_page_context()` 헬퍼로 홈·개인정보·약관
  3개 공개 뷰에만 두 값을 컨텍스트로 전달.
- `templates/base.html`: 컨텍스트 값이 있을 때만 서치 콘솔 확인 메타
  태그와 GA4 gtag 스니펫(async) 렌더링. 값 미전달 페이지(로그인 후
  전체·인증 워크플로)에는 절대 렌더링되지 않음.
- `lifeDiary/urls.py`: `sitemap.xml` 추가 (robots 정책에 맞춰 요청 호스트
  기반 홈 URL 1개만), robots.txt에 `Sitemap:` 줄 추가.
- `templates/legal/privacy.html`: "6. 웹 분석 도구" 섹션 신설, 쿠키
  섹션에 GA 쿠키 문구 반영, 기존 6·7절 → 7·8절 번호 조정, 최종 업데이트
  날짜 2026-08-31.
- `locale/ko`, `locale/en`: 신규·변경 문자열 9건 번역. makemessages가
  물려준 fuzzy 오역 3건(ko)·3건(en) 제거 후 정정, `msgfmt --check-format`
  통과. ko 헤더의 기존 fuzzy는 기존 상태 유지.
- 테스트: `apps/core/tests.py`에 sitemap·GA 조건부 렌더·대시보드 비추적
  계약 4건 추가, robots 테스트에 Sitemap 줄 반영, privacy 테스트에 분석
  고지 assertion 추가. `lifeDiary/test_prod_settings.py` CSP 계약에 GA
  출처 4건 추가.

## 검증 증거 (2026-08-31 실행)

- `conda run -n knou-life-diary pytest apps/core/tests.py
  lifeDiary/test_prod_settings.py --tb=short` → 18 passed.
- `conda run -n knou-life-diary pytest` → 597 passed (7:12).
- `conda run -n knou-life-diary python manage.py check` → 0 이슈.
- `conda run -n knou-life-diary python manage.py check
  --settings=lifeDiary.settings.prod --deploy --fail-level ERROR` →
  exit 0. W009 경고 1건은 로컬 셸의 SECRET_KEY에 대한 기존 경고로 이번
  변경과 무관 (실제 키는 Render 환경변수).
- `msgfmt --check-format` ko/en 모두 통과.
- 브라우저(HTTP + Chrome DevTools, env 설정 켠 runserver):
  - `/robots.txt`에 `Sitemap: http://<host>/sitemap.xml` 줄 확인.
  - `/sitemap.xml`이 홈 URL 1개만 담은 XML 반환.
  - 홈 `<head>`에 확인 메타 태그·gtag 스니펫 렌더, gtag.js 네트워크 200,
    콘솔 메시지 0건.
  - `/accounts/login/` 응답에 gtag·확인 태그 0건, `/terms/`에는 gtag 렌더.
  - `/privacy/` ko·en 모두 "웹 분석 도구"/"Web Analytics" 섹션 렌더.

## Frontend Review Evidence (깊이: Light)

- Web Experience Designer 판정: **Conforms** — 신설 섹션이 기존 카드
  패턴(h2.h5 + p/ul)을 그대로 따르고, head 태그 2종은 비가시 요소로
  레이아웃·시각 위계 영향 없음. 근거: privacy ko/en HTTP 렌더 확인.
- Browser Interaction Reviewer 판정: **Conforms** — gtag는 `async`
  로드로 렌더 차단 없음(직전 Lighthouse 작업 회귀 없음), 콘솔 에러 0건,
  로그인·비공개 화면 비추적 확인. 근거: DevTools 네트워크·콘솔 검사,
  `test_dashboard_never_renders_analytics_even_when_configured`.
- Quality Verification Lead 결정: 완료 — 계획의 Test List 7개 시나리오가
  모두 자동 테스트 또는 브라우저 증거로 커버되고 전체 회귀 그린.

## 미검증 항목

- 실배포 환경에서의 CSP 하 GA 동작 (환경변수 설정·배포 후 확인 필요).
- 서치 콘솔 소유권 확인 성공 여부 (사용자 등록 절차 이후 확인 가능).

## Deferred

- 쿠키 동의 배너 검토, AdSense 신청, 공개 콘텐츠 페이지 확장 시
  sitemap/robots 재검토 — 계획 문서의 Deferred Work 절 참고.
