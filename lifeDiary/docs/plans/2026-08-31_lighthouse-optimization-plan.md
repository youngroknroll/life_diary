# Lighthouse 최적화 계획 (2026-08-31)

## 배경

www.lifediary.kr 모바일 Lighthouse 점검 결과: Accessibility 100, Best
Practices 92, SEO 63, LCP 740ms(무스로틀), CLS 0. 렌더 차단 리소스로
FCP/LCP 약 310ms 손실 추정.

근본 원인 4건:

1. `robots.txt`가 `Disallow: /` 전체 차단 → SEO 63 (`is-crawlable` 실패).
2. `STATICFILES_STORAGE`는 Django 5.1에서 제거된 설정이라 5.2에서 무시됨
   → manifest 해시·whitenoise 압축·장기 캐시 전부 비활성. `style.css`가
   비해시 경로 + `max-age=60`으로 서빙 중.
3. `base.html`이 미사용 htmx(hx- 속성 0건)·Alpine.js(x-data 0건)를 전
   페이지에 로드하고, stats 전용 chart.js+어댑터를 head에서 동기 로드.
   `/jsi18n/`(~328ms)도 동기 로드.
4. 언어 선택 버튼의 보이는 텍스트(KO/EN)가 접근 가능한 이름에 미포함
   (axe `label-content-name-mismatch`).

## 승인된 범위 (사용자 승인 2026-08-31)

- robots.txt: **홈(`/`)만 색인 허용**, 나머지 경로 차단. 렌더링 평가를
  위해 `/static/` 크롤 허용 포함(색인 대상 아님, 자산 크롤용).
- prod 정적 파일 스토리지를 `STORAGES` 딕셔너리로 이전.
- base.html 스크립트 정리(htmx·Alpine 제거, chart.js 이동, jsi18n defer).
- 언어 버튼 접근성 수정.

## 명시적 제외 (Deferred)

- CSP 소스맵 콘솔 에러(BP 92): connect-src 완화는 보안 베이스라인 후퇴.
  트리거: 벤더 셀프호스팅 결정 시 함께 해소.
- `desktop.py`의 죽은 `STATICFILES_STORAGE`: 데스크톱 패키징 검증 수단이
  현재 없음. 트리거: 다음 데스크톱 패키징 작업.
- `/jsi18n/` 응답 캐시 헤더: defer 전환으로 임계 경로에서 제거되므로
  이번 범위에서 불필요. 트리거: 반복 방문 TTFB가 다시 문제될 때.
- 비공개 페이지 meta noindex: robots 차단으로 크롤 자체가 막힘. 트리거:
  외부 링크로 인한 URL 노출이 관측될 때.

## Activated Roles

- Backend TDD Coach: robots.txt·STORAGES 계약 테스트 시퀀스.
- Backend & Integration Engineer: urls.py, settings, 테스트 구현.
- Deployment & Operations Reviewer: collectstatic 설정 모듈 리스크,
  롤아웃 체크리스트.
- Web Experience Designer + Browser Interaction Reviewer: 프론트엔드
  이중 리뷰 게이트(사전 산출물 + 사후 판정).
- Frontend Implementation Engineer: 템플릿 수정.
- Quality Verification Lead: 증거 매트릭스와 완료 판정.

## Not Activated

- Product Scope Owner: 색인 정책은 사용자가 직접 결정함(질문-응답).
- Domain Architecture Reviewer: 도메인 경계·의존 방향 변화 없음.
- Security & Resilience Reviewer: CSP·쿠키·인증 변경 없음(소스맵 건은
  보류로 명시). 단, 구현 중 CSP 관련 변경이 생기면 즉시 활성화.
- AI Automation Architect: AI 범위 아님.

## 파일과 구현 단계

### Track A — robots.txt (backend, web 계약)

- `apps/core/tests.py`: 기존
  `test_robots_txt_disallows_all_crawlers`를
  `test_robots_txt_allows_only_home_indexing`으로 대체(Red).
- `lifeDiary/urls.py:36-42`: 응답 본문을 아래로 교체(Green).

```text
User-agent: *
Allow: /$
Allow: /static/
Disallow: /
```

RFC 9309 최장 일치 규칙으로 `/`(정확히 루트)와 `/static/*`만 허용된다.

### Track B — STORAGES (deployment/configuration)

- `lifeDiary/test_prod_settings.py`: 기존 monkeypatch+reload 패턴으로
  `STORAGES["staticfiles"]`가 whitenoise
  `CompressedManifestStaticFilesStorage`인지 계약 테스트 추가(Red).
- `lifeDiary/settings/prod.py`: `STORAGES` 딕셔너리 정의(Green).
  `default`(FileSystemStorage)와 `staticfiles`를 모두 명시(STORAGES는
  기본값과 병합되지 않고 전체 대체됨).
- `lifeDiary/settings/dev.py:202`: 죽은 `STATICFILES_STORAGE` 라인 제거.
  dev·pytest는 오늘과 동일한 기본 스토리지 유지(pytest-django가
  DEBUG=False를 강제하므로 dev에 manifest를 넣으면 템플릿 렌더 테스트가
  manifest 부재로 깨진다 — prod 스코프가 안전).

### Track C — 프론트엔드 (dual review gate, High depth)

- `templates/base.html`:
  - htmx `<script>`와 `htmx:configRequest` 리스너 제거(미사용).
  - Alpine.js `<script>` 제거(미사용).
  - chart.js + chartjs-adapter-date-fns `<script>` 2개를 head에서 제거.
  - `javascript-catalog` 스크립트에 `defer` 추가(문서 순서상 utils.js
    defer보다 앞이라 실행 순서 보존).
- `apps/stats/templates/stats/index.html` extra_js: chart.js + 어댑터를
  기존 SRI 해시 그대로 `defer`로 추가, `stats.js` defer 앞에 배치.
- `templates/shared/_nav_prefs.html:34-36`: 언어 버튼 aria-label에
  보이는 코드(`KO`/`EN`)를 포함.

안전 근거(사전 조사 완료): 모든 앱 JS는 defer로 로드되고, 인라인
스크립트의 gettext/유틸 호출은 전부 이벤트 핸들러 내부라 defer 전환과
충돌하지 않음. `new Chart`는 `apps/stats/static/stats/js/stats.js`에만
존재.

## Domain Boundary / Dependency Direction

앱 경계·의존 방향 변화 없음. 설정과 표현 계층만 수정.

## Coupling / Cohesion

base.html의 라이브러리 로드가 실사용 위치(stats)로 이동해 응집 상승,
전역 결합 감소. 신규 결합 없음.

## Pythonic Code Design

프레임워크 네이티브 `STORAGES` 설정 사용. 커스텀 스토리지·추상화 없음.

## Test List

| Scenario | 내용 | Boundary | 테스트 |
|---|---|---|---|
| S1 | robots.txt가 홈만 색인 허용하고 나머지를 차단한다 | web | `test_robots_txt_allows_only_home_indexing` |
| S2 | prod가 whitenoise manifest 스토리지로 해시 정적 파일을 서빙한다 | contract | `test_prod_settings_serve_hashed_static_files_with_whitenoise` |

프론트엔드는 프론트엔드 작업 정책에 따라 자동 테스트 없이 브라우저
증거로 검증한다.

## 검증 명령과 기대 증거

1. Red: 신규/수정 테스트가 기대 사유로 실패.
2. Green: `conda run -n knou-life-diary pytest apps/core/tests.py lifeDiary/test_prod_settings.py --tb=short` 통과.
3. `conda run -n knou-life-diary python manage.py collectstatic --noinput --settings=lifeDiary.settings.prod` exit 0 + `staticfiles/staticfiles.json` 생성 + style.css 해시본·`.br`/`.gz` 존재.
4. 전체 회귀: `conda run -n knou-life-diary pytest`.
5. `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`.
6. 브라우저: 로컬 runserver로 홈·로그인·대시보드·stats 렌더, 드롭다운
   동작, stats 차트 렌더, 콘솔 무에러 확인. 언어 버튼 접근 이름 확인.

## 롤아웃 리스크 (Deployment & Operations)

- **manifest 부재 기동 리스크**: Render 빌드의 collectstatic이 prod
  설정으로 실행되지 않으면 manifest가 없어 정적 URL 해석 시 500.
  배포 전 Render 빌드 커맨드/환경변수(`DJANGO_SETTINGS_MODULE`)를
  확인하고, 배포 직후 홈 1회 로드로 확인한다. 롤백은 커밋 revert.
- robots.txt 변경은 크롤러 반영에 시간이 걸리며 즉시 롤백 가능.

## Frontend Review Evidence

- 리뷰 깊이: High — base.html 스크립트 로딩은 전 페이지 공통 패턴.
- WED 사전 사양: 산출 완료 — 페이지별 무영향 기준, 언어 버튼 라벨 형식
  (`{% trans '언어 선택' as lang_label %}` + 코드 결합), 판정 체크리스트
  7항목.
- BIR 사전 기준: 산출 완료 — R1(jsi18n defer 전제) ~ R3(SRI 동일 유지)
  필수 준수, 수용 기준 A1-A5/B6-B8/C9-C11, jsi18n 경합 Medium 리스크
  검증 요구. 저장소 전수 패턴 검색으로 htmx/Alpine/Chart/gettext 사용처
  확정.
- 브라우저 증거: 실행 로그
  (`docs/refactoring/2026-08-31_lighthouse-optimization.md`) 검증 표와
  브라우저 상세 절 — 콘솔 무에러, 4개 차트 인스턴스화, 테마·언어 전환,
  두 로케일 접근 이름, jsi18n 경합 결정적 재현(코스메틱 한정 확인),
  로컬 모바일 Lighthouse A11y 100 / BP 100 / SEO 100.
- WED 사후 판정: **Conforms** — 정적 마크업·속성·구조가 사전 사양과
  일치함을 소스 재확인, 이탈 없음.
- BIR 사후 판정: 실행 로그 참조.
- QVL 완료 판정: 실행 로그 참조.
