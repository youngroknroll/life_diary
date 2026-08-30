# Lighthouse 최적화 실행 로그 (2026-08-31)

계획: `docs/plans/2026-08-31_lighthouse-optimization-plan.md`
브랜치: `feat/lighthouse-optimization`

## 배경 측정 (www.lifediary.kr, 모바일)

Accessibility 100 / Best Practices 92 / SEO 63, LCP 740ms(무스로틀),
CLS 0.00, 렌더 차단 손실 추정 310ms.

## 변경 내역

### Track A — robots.txt 홈만 색인 허용

- `lifeDiary/urls.py`: `Disallow: /` 전체 차단을
  `Allow: /$` + `Allow: /static/` + `Disallow: /` 로 교체.
  사용자 결정(2026-08-31): 홈만 색인 허용. `/static/` 은 색인이 아니라
  구글이 홈을 렌더링 평가할 때 자산을 읽게 하는 크롤 허용이다.
- `apps/core/tests.py`: `test_robots_txt_disallows_all_crawlers` →
  `test_robots_txt_allows_only_home_indexing` 로 대체.
- Red: 본문 불일치로 실패 확인 → Green: 1 passed.

### Track B — prod 정적 파일 STORAGES 이전

- 원인: `STATICFILES_STORAGE` 는 Django 5.1에서 제거된 설정이라 5.2에서
  조용히 무시되고 있었다. 그 결과 prod 가 비해시 정적 경로를
  `max-age=60` 으로 서빙했고 whitenoise 압축·장기 캐시가 비활성이었다.
- `lifeDiary/settings/prod.py`: `STORAGES` 딕셔너리 추가
  (`default` FileSystemStorage + `staticfiles` whitenoise
  `CompressedManifestStaticFilesStorage`).
- `lifeDiary/settings/dev.py`: 죽은 `STATICFILES_STORAGE` 라인 제거.
  prod 스코프로 둔 이유: pytest-django 가 DEBUG=False 를 강제하므로 dev
  에 manifest 스토리지를 두면 collectstatic 없이는 `{% static %}` 해석이
  깨진다.
- `lifeDiary/test_prod_settings.py`:
  `test_prod_settings_serve_hashed_static_files_with_whitenoise` 추가.
  Red(AttributeError: no STORAGES) → Green.

### Track C — 프론트엔드 스크립트 정리

- `templates/base.html`:
  - 미사용 htmx 제거 — `hx-` 속성·`htmx.` API 참조 저장소 전체 0건,
    `htmx:configRequest` CSRF 리스너도 함께 제거(utils.js 가
    `getCookie('csrftoken')` 으로 자체 주입, utils.js:13,161).
  - 미사용 Alpine.js 제거 — `x-data` 등 저장소 전체 0건.
  - chart.js + chartjs-adapter-date-fns 를 head 동기 로드에서 제거.
  - `javascript-catalog`(jsi18n) 스크립트에 `defer` 추가. defer 는 문서
    순서 실행이라 utils.js defer 앞 배치로 순서 보존.
- `apps/stats/templates/stats/index.html`: chart.js + 어댑터를 기존 SRI
  그대로 `defer` 로 추가, `stats.js` defer 앞 배치. `new Chart` 사용처는
  stats.js 뿐.
- `templates/shared/_nav_prefs.html`: 언어 버튼 aria-label/title 을
  `{% trans '언어 선택' as lang_label %}` + `({{ LANGUAGE_CODE... }})` 로
  구성해 보이는 텍스트(KO/EN)를 접근 이름에 포함. 기존 msgid 재사용이라
  .po 변경 없음.

## 검증 증거 (전부 fresh 실행)

| 항목 | 명령/방법 | 결과 |
|---|---|---|
| Red-Green S1 | pytest -k robots | Red(본문 불일치) → 1 passed |
| Red-Green S2 | pytest -k whitenoise | Red(no STORAGES) → 7 passed(파일 전체) |
| 전체 회귀 | `conda run -n knou-life-diary pytest` | **593 passed** (414s) |
| collectstatic | `--settings=lifeDiary.settings.prod --noinput` | exit 0, staticfiles.json 생성, `style.59834671f0d9.css` + `.gz` 확인 (brotli 패키지 미설치로 `.br` 없음 — gzip 사전압축은 활성) |
| Django check | `manage.py check` | 이슈 0, exit 0 |
| prod deploy check | `--deploy --fail-level ERROR` | exit 0 (W009 SECRET_KEY 경고는 로컬 자리표시자, 기존과 동일) |
| 마이그레이션 드리프트 | `makemigrations --check --dry-run` | 변경 없음, exit 0 |
| 브라우저 | dev DB 사본으로 검증 서버(:8123) + Chrome DevTools | 아래 상세 |
| 로컬 Lighthouse(모바일, 홈) | chrome-devtools lighthouse_audit | **A11y 100 / BP 100 / SEO 100, 실패 감사 0건** |

브라우저 상세 (dev DB 는 사본만 사용, 원본 무변경):

- 홈/로그인/대시보드/stats 콘솔 에러 0건. `window.htmx`·`Alpine`·
  `Chart`(stats 외) 모두 undefined, gettext 정상.
- stats 실데이터 날짜(2026-08-02): 4개 차트 전부 인스턴스화, Chart.js
  3.9.1 defer+SRI 로드. 빈 주간에서 chart-empty 오버레이 정상.
- 테마 드롭다운 → 다크 전환 → 차트 생존, 콘솔 무에러.
- 언어 전환(폼 POST) → ko "언어 선택 (KO)", en "Language (EN)" — 두
  로케일 모두 보이는 텍스트가 접근 이름에 포함.
- jsi18n defer 경합 결정적 재현: gettext/showOverlay 를 undefined 로
  만들고 로그인 제출 → TypeError 는 찍히나 로그인·리다이렉트 정상.
  최악 결과는 오버레이 미표시(코스메틱)이며, 같은 등급 경합이 변경
  전에도 defer utils.js 의 showOverlay 에 존재 — 신규 실패 클래스 아님.

검증하지 않은 것:

- 프로덕션 Lighthouse 점수는 배포 후에만 확정된다. 특히 Best Practices
  의 CSP 소스맵 콘솔 에러는 prod CSP 헤더에서만 재현되므로 로컬 100점이
  prod 100점을 보장하지 않는다(보류 항목).
- Render 빌드의 collectstatic 이 prod 설정으로 실행되는지는 저장소에서
  확인 불가(아래 배포 체크리스트).

## 프론트엔드 이중 리뷰 판정

- WED 사후 판정: **Conforms** — 정적 마크업·속성·구조가 사전 사양과
  일치함을 소스 재확인, 이탈 없음.
- BIR 사후 판정: **Deviates 없음** — 필수 기준(A1, A4, B6, C9, C10,
  R1-R3, 경합 리스크의 구조적 정합성) 전부 소스 재확인으로 Conforms.
  런타임 전용 항목(콘솔 무에러, 차트 실렌더, Lighthouse 수치, 경합 재현
  로그)은 리뷰어가 브라우저 도구 없이 독립 재현하지 못해 Unverified 로
  표기.
- QVL 완료 판정: **완료** — BIR 이 Unverified 로 표기한 런타임 항목은
  전부 이 세션에서 조율자가 Chrome DevTools 로 직접 실행해 fresh 출력
  으로 확인한 것들이며(위 검증 표), 에이전트 자기보고가 아니라 도구
  실행 증거다. BIR 은 그 보고가 소스 구조·표준 이벤트 의미론과 모순
  없음을 정합성 수준에서 확인했다. 잔여 리스크(로그인 오버레이 경합,
  코스메틱 한정)는 아래 Deferred 에 기록.

## 배포 체크리스트 (필수)

1. Render 빌드 커맨드의 `collectstatic` 이 prod 설정으로 실행되는지
   확인: 환경변수 `DJANGO_SETTINGS_MODULE=lifeDiary.settings.prod` 또는
   `--settings` 플래그. **manifest 없이 기동하면 `{% static %}` 해석에서
   Missing staticfiles manifest entry 500 이 난다.**
2. 배포 직후 홈 1회 로드 + 정적 URL 이 해시 경로(`style.<hash>.css`)로
   나오는지 확인.
3. 문제 시 롤백: STORAGES 커밋 revert 후 재배포.

## Deferred Refactoring Note

- Topic: CSP 소스맵 콘솔 에러(BP 92), `script-src` 의 미사용
  `https://unpkg.com` 허용 출처 정리, desktop.py 의 죽은
  `STATICFILES_STORAGE`, jsi18n 응답 캐시 헤더, 비공개 페이지 noindex,
  `login.html` 의 gettext 호출 가드(BIR 권고 — jsi18n 미로드 경합 시
  콘솔 TypeError 제거용 방어 패턴).
- Why not now: CSP 완화는 보안 베이스라인 후퇴, 벤더 셀프호스팅은 별도
  결정 필요. desktop 은 패키징 검증 수단 부재. jsi18n 은 defer 로 임계
  경로에서 이미 제거됨.
- Trigger: 벤더 셀프호스팅 결정 / 다음 데스크톱 패키징 작업 / 반복 방문
  TTFB 재문제화 / 외부 링크로 비공개 URL 노출 관측.
- Expected change location: `lifeDiary/settings/prod.py`(CSP),
  `lifeDiary/settings/desktop.py`, `lifeDiary/urls.py`.
- Related tests: `lifeDiary/test_prod_settings.py` 의 CSP 계약 테스트.
