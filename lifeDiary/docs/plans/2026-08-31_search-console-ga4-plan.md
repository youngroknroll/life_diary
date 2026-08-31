# Search Console 등록 지원 + GA4 도입 계획 (2026-08-31)

## 배경

`docs/plans/2026-05-28-ad-revenue-marketing-strategy.md` Phase 2("Add Search
Console", "Submit sitemap if available, or add one if missing")와 8절("Any
analytics tool is documented in the privacy policy")에 해당하는 작업을
사용자가 2026-08-31 직접 승인했다. AdSense 신청과 광고 슬롯은 이번 범위가
아니다.

사용자 결정 사항:

- 서치 콘솔 소유권 확인: HTML 메타 태그 방식 (URL 접두어 속성)
- GA4 측정 ID: 아직 미발급 → 환경변수 기반으로 준비
- GA 적용 범위: 공개 페이지만 (홈, 개인정보처리방침, 이용약관)
- 부수 작업: sitemap.xml 추가, 개인정보처리방침 갱신 모두 포함

## 승인 범위

1. `GOOGLE_SITE_VERIFICATION`, `GA_MEASUREMENT_ID` 환경변수 기반 설정 추가.
   미설정 시 아무것도 렌더링하지 않는다. 데스크톱 설정은 두 값을 빈
   문자열로 강제한다.
2. 공개 페이지 3곳(홈 `index.html`, `legal/privacy.html`,
   `legal/terms.html`)에만 서치 콘솔 확인 메타 태그와 GA4 gtag 스니펫을
   조건부 렌더링. 로그인 후 페이지(대시보드·통계·태그·계정)에는 값이
   설정돼 있어도 절대 렌더링하지 않는다.
3. `sitemap.xml` 엔드포인트 추가. robots.txt가 홈만 색인 허용하므로
   sitemap도 홈 URL 하나만 담는다(요청 호스트 기반 절대 URL).
   robots.txt에 `Sitemap:` 줄을 추가한다.
4. prod CSP에 GA4 출처 추가(구글 공식 가이드 기준):
   - `script-src` += `https://www.googletagmanager.com`
   - `connect-src` += `https://*.google-analytics.com
     https://*.analytics.google.com https://*.googletagmanager.com`
   - `img-src` += `https://*.google-analytics.com
     https://*.googletagmanager.com`
5. 개인정보처리방침에 GA 사용 고지 섹션 추가 (ko 원문 + en 번역).
6. 계획·작업 로그·`docs/project-status.md` 문서화.

## 명시적 제외

- AdSense 신청, 광고 슬롯, 광고 파셜 (마케팅 플랜 Phase 2 후반~3)
- GTM(태그 매니저) 도입 — gtag.js 직접 삽입만
- 쿠키 동의 배너 — 별도 승인 대상으로 보류
- CSP nonce 엄격화 — 기존 보류 상태 유지
- 로그인 후 페이지 추적 — 사용자가 공개 페이지만으로 결정
- 서치 콘솔·GA 콘솔에서의 실제 등록 절차는 사용자가 수행

## Activated Roles / Not Activated

Activated:

- Deployment & Operations Reviewer — 환경변수·CSP·배포 영향 (본 계획의
  운영 체크리스트로 산출)
- Security & Resilience Reviewer — CSP 완화 폭 최소화, 개인 데이터 페이지
  비추적 계약 (본 계획의 보안 검토로 산출)
- Backend TDD Coach + Backend & Integration Engineer — sitemap·조건부
  렌더링·설정 계약의 Red-Green
- Frontend Implementation Engineer — base.html·privacy.html 편집
- Web Experience Designer / Browser Interaction Reviewer — 프론트 이중
  리뷰 게이트, 깊이 `Light` (비가시 태그 + 방침 텍스트 섹션 추가라 시각
  구조 변화 없음)
- Quality Verification Lead — 증거 매트릭스와 완료 판정

Not Activated:

- Product Scope Owner — 범위를 사용자가 질의응답으로 직접 확정
- Domain Architecture Reviewer — 앱 경계·의존 방향 변화 없음
- AI Automation Architect — AI 범위 아님

## Domain Boundary And Dependency Direction

- 공개 페이지 뷰는 `lifeDiary/views.py` 소유. 설정값을 읽어 컨텍스트에
  넣는 책임도 그 뷰에 둔다(새 앱·프로세서·미들웨어 도입 없음).
- sitemap·robots는 `lifeDiary/urls.py`의 기존 공개 인프라 경로 패턴을
  따른다.
- 앱 간 의존 변화 없음. `apps/*`는 이번 작업에서 수정하지 않는다
  (`apps/core/tests.py` 테스트 제외).

## Coupling And Cohesion Review

1. 결합도: 새 외부 의존은 GA 스크립트 출처뿐이며 환경변수 미설정 시 완전
   비활성. 증가분은 승인 범위 그 자체다.
2. 응집도: 공개 페이지 노출 규칙이 `lifeDiary/views.py` 한 곳에 모인다.
   통과.

## Pythonic Code Design

- `django.contrib.sitemaps`는 sites 프레임워크 의존이 생기므로 홈 URL
  하나에는 과설계다. robots.txt와 같은 소형 뷰로 XML을 직접 반환한다.
- 뷰는 `settings`에서 읽은 값을 명시적 컨텍스트 키
  (`ga_measurement_id`, `google_site_verification`)로 전달한다. 템플릿
  전역 주입(context processor)은 공개/비공개 구분을 흐리므로 쓰지 않는다.

## 구현 파일과 단계

1. `lifeDiary/settings/dev.py` — `GA_MEASUREMENT_ID`,
   `GOOGLE_SITE_VERIFICATION` = `os.getenv(..., "")`
2. `lifeDiary/settings/desktop.py` — 두 값을 `""`로 강제
3. `lifeDiary/settings/prod.py` — CSP 출처 추가 (계약 테스트 선행)
4. `lifeDiary/views.py` — 공개 페이지 컨텍스트 헬퍼 + 3개 뷰 적용
5. `templates/base.html` — `<head>`에 조건부 메타 태그·gtag 스니펫
6. `lifeDiary/urls.py` — `sitemap.xml` 경로 추가, robots.txt에
   `Sitemap:` 줄 추가
7. `templates/legal/privacy.html` — GA 고지 섹션 (trans 태그)
8. `locale/ko`, `locale/en` — 신규 문자열 번역 (ko msgstr 채움,
   `msgfmt --check-format` 검증)
9. `apps/core/tests.py`, `lifeDiary/test_prod_settings.py` — 아래 Test
   List
10. 작업 로그 `docs/refactoring/2026-08-31_search-console-ga4.md` +
    `docs/project-status.md` 갱신

## 프로세스 예외 (2026-08-31 승인)

사용자가 "비즈니스 로직이 아니니 TDD로 진행할 필요는 없어"로 Backend TDD
Cycle을 명시 웨이버했다. Test List의 시나리오는 구현 후 계약 보호
테스트로 작성한다. 실행 결과는
`docs/refactoring/2026-08-31_search-console-ga4.md` 참고.

## Test List

| Scenario ID | Business behavior | Given | When | Then | Boundary | Boundary rationale | Test name | Status |
|---|---|---|---|---|---|---|---|---|
| SEO-SITEMAP-1 | 검색엔진이 sitemap에서 홈 주소를 얻는다 | 서비스 기동 | `/sitemap.xml` GET | 200, XML, 요청 호스트 기반 홈 URL 1개만 | web | URL 라우팅·호스트 반영은 HTTP 경계에서만 관찰 가능 | `test_sitemap_lists_only_home_url` | Pending |
| SEO-ROBOTS-1 | 크롤러가 robots.txt에서 sitemap 위치를 얻는다 | 기존 홈 전용 색인 정책 | `/robots.txt` GET | 기존 정책 유지 + `Sitemap:` 줄 | web | 기존 `test_robots_txt_allows_only_home_indexing` 갱신 | (기존 테스트 수정) | Pending |
| GA-PUBLIC-1 | 측정 ID가 설정되면 공개 홈에서 GA가 로드된다 | `GA_MEASUREMENT_ID` 설정 | 홈 GET | 응답에 gtag 스크립트·측정 ID 포함 | web | 설정 조건부 렌더링은 응답에서만 관찰 가능 | `test_home_renders_analytics_when_measurement_id_configured` | Pending |
| GA-PUBLIC-2 | 측정 ID가 없으면 어떤 추적도 없다 | 설정 빈 문자열(기본) | 홈 GET | gtag 부재 | web | 동일 | `test_home_omits_analytics_without_measurement_id` | Pending |
| GA-PRIVATE-1 | 로그인 후 기록 화면은 측정 ID가 있어도 추적되지 않는다 | 설정 존재 + 로그인 사용자 | 대시보드 GET | gtag 부재 | web | 개인 데이터 페이지 비추적은 제품 계약 | `test_dashboard_never_renders_analytics_even_when_configured` | Pending |
| SC-META-1 | 확인 토큰이 설정되면 홈에 소유권 메타 태그가 실린다 | `GOOGLE_SITE_VERIFICATION` 설정 | 홈 GET | 메타 태그 포함(미설정 시 부재) | web | parametrize로 설정/미설정 케이스 | `test_home_renders_site_verification_meta_only_when_configured` | Pending |
| CSP-GA-1 | prod CSP가 GA 출처를 허용한다 | prod 설정 로드 | CSP 문자열 검사 | GA 4개 출처 포함 | contract | 기존 CSP 계약 테스트 확장 | (기존 테스트 수정) | Pending |

마크업 문자열 검사 주의: GA-*·SC-META-1은 표현이 아니라 "설정에 따른
포함/비포함"이라는 백엔드 계약을 검증하며, 마케팅 플랜 Phase 3의 "private
app pages do not render ad slots" 테스트 전례와 같은 성격이다.

## Frontend Review Evidence

- 깊이: `Light` — 비가시 head 태그 2종 + 방침 문서에 텍스트 섹션 1개.
  레이아웃·인터랙션·반응형 영향 없음.
- Web Experience Designer 사전 사양: 방침 페이지의 기존 섹션 구조
  (제목 + 목록)를 그대로 따르는 GA 고지 섹션 1개를 기존 "제3자 제공"류
  섹션 인근에 추가. 시각 요소 신규 도입 없음.
- Browser Interaction Reviewer 사전 기준: gtag는 `async`로 로드해 렌더
  차단 없음(직전 Lighthouse 작업 회귀 금지). 콘솔에 CSP 위반 에러 0건.
  키보드·포커스 영향 없음.
- 계획된 브라우저 증거: runserver + 측정 ID 임시 환경변수로 홈·방침
  페이지 렌더 확인, 콘솔 에러 0건 확인, 대시보드에서 gtag 부재 확인.
- 사후 판정 2건과 QVL 결정은 구현 후 작업 로그에 기록.

## 운영 체크리스트 (배포)

1. Render 환경변수 `GA_MEASUREMENT_ID`, `GOOGLE_SITE_VERIFICATION` 등록
   (코드 배포와 독립, 미설정이어도 동작 저하 없음).
2. 배포 후 `curl -s https://<host>/robots.txt`, `/sitemap.xml` 확인.
3. 서치 콘솔 "확인" 클릭은 메타 태그가 배포된 뒤에만 성공.
4. 롤백: 환경변수 제거만으로 추적·메타 태그가 즉시 사라진다.

## 보안 검토 요지

- CSP 완화는 구글 공식 가이드가 명시한 최소 출처 4건으로 한정. `frame-src`
  등 다른 지시자는 건드리지 않는다.
- 확인 토큰·측정 ID는 비밀은 아니나 환경변수로 관리해 저장소에 남기지
  않는다.
- 로그인 후 페이지 비추적은 GA-PRIVATE-1 테스트로 계약화한다.

## 검증 명령

- `conda run -n knou-life-diary pytest apps/core/tests.py lifeDiary/test_prod_settings.py --tb=short`
- `conda run -n knou-life-diary pytest`
- `conda run -n knou-life-diary python manage.py check`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`
- `msgfmt --check-format` (ko/en po)
- 브라우저: runserver로 홈·방침·대시보드 렌더 및 콘솔 확인

## 사용자 수행 절차 (코드 머지·배포 후)

1. GA4: analytics.google.com → 속성 생성 → 웹 스트림(서비스 대표 호스트)
   → 측정 ID(G-…) 발급 → Render에 `GA_MEASUREMENT_ID` 설정.
2. 서치 콘솔: URL 접두어 속성으로 대표 호스트 등록 → HTML 태그 방식 선택
   → `content="..."` 토큰을 Render `GOOGLE_SITE_VERIFICATION`에 설정 →
   재배포 → "확인" 클릭.
3. 서치 콘솔에 `https://<host>/sitemap.xml` 제출.

## Deferred Work

- 쿠키 동의 배너 필요성 검토 (GA 트래픽이 실제로 쌓이기 시작할 때)
- AdSense 신청 (마케팅 플랜 Phase 2 잔여)
- 공개 콘텐츠(가이드) 페이지가 생기면 sitemap·robots 정책 재검토
