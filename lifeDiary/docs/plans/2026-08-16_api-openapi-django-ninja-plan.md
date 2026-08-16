# django-ninja 도입: JSON API 이식 + OpenAPI/Swagger 문서화 계획

- 날짜: 2026-08-16
- 브랜치: `feat/api-openapi-ninja` (base: `main` c4a7e90)
- 상태: 사용자 승인 완료 (계약 변경 4건 포함)

## 목적

JSON API 5개 엔드포인트에 OpenAPI 3 스키마와 Swagger UI를 제공해
프론트엔드 협업 기반을 만든다. 스택은 사용자가 django-ninja로 확정했다
(DRF, 수기 OpenAPI 스펙 대비 선택). pydantic>=2.7은 이미 의존성에 있고
dashboard 커맨드 검증이 이미 pydantic이므로 궁합이 좋다.

## 승인 범위

- `apps/dashboard/api_urls.py`, `apps/tags/api_urls.py`의 5개 엔드포인트를
  django-ninja 라우터로 이식하고 URL 경로를 그대로 보존한다.
- Swagger UI `/api/docs`, 스키마 `/api/openapi.json`을 전 환경에서 제공한다.
- 아래 "의도적 계약 변경" 4건 외 모든 요청/응답 계약을 그대로 보존한다.

### 명시적 제외

- users 앱의 signup check/goals 엔드포인트 (JSON API 아님 또는 페이지 결합)
- rate limiting, 토큰 인증, API 버저닝 정책
- 프론트엔드 JS/템플릿/CSS 편집 (URL 보존으로 무변경)
- PyInstaller desktop 번들에 ninja 정적 파일 포함 검증 (desktop 트랙에서)

## 현재 계약 요약 (탐색 근거)

- 응답 봉투: 성공 `{"success": true, "message", ...데이터 평탄 병합}`,
  에러 `{"success": false, "message", "error": 코드}` (`apps/core/utils.py:83-124`)
- 프론트 12개 호출부가 `/api/...` 경로를 하드코딩 (`apps/core/static/core/js/utils.js`
  `apiCall()` 경유, `X-CSRFToken` 헤더 + 세션 쿠키). JS는 에러 시 HTTP 상태와
  `message`만 읽는다. `success`/`error` 코드는 소비처 없음.
- 웹 계층 테스트 약 28개가 경로를 하드코딩해 회귀망 역할.
  `apps/tags/test_category_i18n.py:33,40`만 `reverse("tags_api:category_list")` 사용.
- `PUT/DELETE /api/tags/<id>/`는 웹 테스트 공백.

## 의도적 계약 변경 (사용자 승인 완료)

1. 미인증 API 호출: 302 HTML 리다이렉트 → **401 JSON**. 현재 302는 fetch가
   로그인 HTML을 따라가 JSON 파싱 오류가 나는 사실상 결함.
   `test_undo_requires_login`의 `(302, 403)` 단언을 401로 갱신.
2. 잘못된 JSON 메시지 통일: dashboard "올바른 JSON 형식이 아닙니다." /
   tags "잘못된 형식의 요청입니다." → 전역 파서 핸들러 1개로 통일
   (dashboard 문구 채택, EN "Invalid JSON format."). tags i18n 테스트 갱신.
3. 미소유/없는 태그 PUT/DELETE: 500 → **404 `TAG_NOT_FOUND`**.
   `get_for_owner_or_404`의 Http404가 bare except로 새는 현재 동작은 결함.
4. ninja ValidationError를 기존 봉투로 매핑: `{"success": false, "message":
   첫 에러 msg, "error": "VALIDATION_ERROR"}`, status **400 유지**
   (ninja 기본 422/`detail` 형태 금지 — JS·기존 테스트 보호).

## 설계

### 구조 (기존 흐름 유지: api 오퍼레이션 → use_cases → repositories → models)

- `lifeDiary/api.py`: `NinjaAPI(auth=django_auth, title="LifeDiary API",
  version="1.0.0")` 단일 인스턴스, 전역 예외 핸들러(봉투 변환), 라우터 등록.
- `apps/dashboard/api.py`, `apps/tags/api.py`: `Router`와 오퍼레이션.
  기존 뷰의 use case 싱글턴과 `_mutation_payload` 등 헬퍼를 재사용.
- `apps/dashboard/schemas.py`, `apps/tags/schemas.py`: 요청/응답 ninja Schema.
  응답 스키마는 현재 평탄 봉투를 그대로 필드로 명세.
- `lifeDiary/urls.py`: include 2줄 → `path("api/", api.urls)`.
  `apps/*/api_urls.py` 삭제, 뷰의 API 함수 제거(페이지 뷰 유지).
- 요청 검증: ninja 입력 스키마는 현재 `.get()` 기본값과 동일하게 관대하게
  두고, 오퍼레이션 안에서 기존 pydantic 커맨드/use case 검증을 그대로 태워
  메시지·상태코드를 보존한다.

### Domain Boundary And Dependency Direction

- 라우터는 앱 소유(`apps/dashboard/api.py`, `apps/tags/api.py`),
  `lifeDiary/api.py`는 조립만 담당. 의존 방향은 기존과 동일하게
  api(HTTP 계층) → use_cases → repositories/domain_services → models.
- 비즈니스 규칙은 이동하지 않는다. HTTP 계층 교체일 뿐 use case,
  repository, 커맨드, 시그널은 무변경.

### Coupling And Cohesion Review

- 결합도: 뷰 함수 5개 + url conf 2개가 라우터 2개 + 조립 1개로 대체.
  앱 간 결합 증가 없음 (`lifeDiary/api.py`가 두 라우터를 아는 것은 기존
  `lifeDiary/urls.py`가 두 api_urls를 아는 것과 동형).
- 응집도: 스키마는 소유 앱에 배치. 봉투 스키마 공통분(success/message/error)은
  `apps/core`에 두지 않고 각 앱 스키마가 상속할 최소 base만 core에 둘지
  구현 중 판단 — 중복 2회까지는 앱별 유지(추상화 조기 도입 금지).

### Pythonic Code Design

- 프레임워크 네이티브 확장점 사용: ninja `Router`, `Schema`,
  `@api.exception_handler`. 메타프로그래밍·전역 상태 추가 없음.
- 오퍼레이션 함수는 기존 뷰와 같은 예외→응답 매핑을 유지하되,
  공통 매핑은 전역 핸들러로 올려 중복 제거.

### 보안

- `django_auth` 세션 인증 + 쿠키 기반이라 ninja가 CSRF 보호를 자동
  활성화. 프론트는 이미 `X-CSRFToken` 헤더 전송 — 무변경.
- 소유권 검사(`get_for_owner_or_404`, `find_by_id_accessible`)는 use case
  계층 그대로 유지.
- `/api/docs` 공개는 스키마 노출일 뿐 데이터 엔드포인트는 전부 인증 뒤.
- 보안 베이스라인(axes, reCAPTCHA, 쿠키, 스로틀링) 비접촉.

### 의존성/설정

- `requirements.txt`에 `django-ninja` 핀 추가 후
  `conda run -n knou-life-diary pip install -r requirements.txt`.
- `"ninja"`를 INSTALLED_APPS에 추가: `lifeDiary/settings/dev.py`와
  독립 정의인 `lifeDiary/settings/desktop.py` 양쪽. Swagger 자산을
  CDN 없이 staticfiles(whitenoise)로 서빙 (prod CSP·오프라인 desktop 대응).

## Activated Roles

- Product Scope Owner: 계약 변경 4건 범위 확정 (사용자 승인으로 완료)
- Domain Architecture Reviewer: HTTP 계층 교체의 경계·의존 방향 (본 문서 설계 절)
- Backend TDD Coach: Test List 순서와 Red-Green 판정
- Backend & Integration Engineer: 구현 전담
- Security & Resilience Reviewer: 401 전환·CSRF 유지·문서 공개 확인
- Deployment & Operations Reviewer: 의존성·정적 파일·prod/desktop 설정 확인

Not Activated: Web Experience Designer·Browser Interaction Reviewer·Frontend
Implementation Engineer (프론트 파일 무변경 — 브라우저 회귀 확인은 QA 증거로
수행하되 프론트 구현 게이트 아님), AI Automation Architect (해당 없음).

## Test List

기존 웹 테스트 ~28개는 경로 하드코딩이라 이식 후 그대로 회귀망이 된다.
아래는 신규/갱신분만. Status는 작업 로그에서 갱신한다.

| Scenario ID | Business behavior | Given / When / Then | Boundary | Test name | Status |
|---|---|---|---|---|---|
| TAG-PUT-01 | 자기 태그 이름을 고치면 수정된 태그가 돌아온다 | 로그인 사용자와 소유 태그 / PUT 이름 변경 / 200 + tag.name 갱신 | web | test_updating_own_tag_name_returns_updated_tag | Pending |
| TAG-PUT-02 | 남의 태그는 고칠 수 없다 | 타인 소유 태그 / PUT / 404 TAG_NOT_FOUND (계약 변경 3) | web | test_updating_foreign_tag_is_refused_as_not_found | Pending |
| TAG-DEL-01 | 자기 태그를 지우면 삭제 확인 메시지가 온다 | 소유 태그 / DELETE / 200 + message 2키 봉투 | web | test_deleting_own_tag_confirms_deletion | Pending |
| TAG-DEL-02 | 없는 태그 삭제는 거절된다 | 존재하지 않는 tag_id / DELETE / 404 TAG_NOT_FOUND (계약 변경 3) | web | test_deleting_missing_tag_is_refused_as_not_found | Pending |
| TAG-DEL-03 | 삭제 시 다른 태그로 기록을 옮길 수 있다 | 블록 있는 태그와 이동 대상 / DELETE move_to_id / 200 + 블록 이동 | web | test_deleting_tag_moves_blocks_to_requested_tag | Pending |
| API-AUTH-01 | 로그인 없이 API를 부르면 401 JSON을 받는다 | 비로그인 / POST time-blocks / 401 + success false (계약 변경 1) | web | test_unauthenticated_api_call_returns_401_json | Pending |
| API-JSON-01 | 깨진 JSON은 통일된 메시지로 거절된다 | 로그인 / 깨진 body POST tags / 400 INVALID_JSON 통일 문구 (계약 변경 2) | web | 기존 test_create_tag_invalid_json 기대값 갱신 | Pending |
| API-DOCS-01 | 문서 페이지와 스키마가 서빙된다 | - / GET /api/docs, /api/openapi.json / 200 + 5개 경로 포함 | web | test_openapi_schema_lists_all_five_endpoints | Pending |
| API-VAL-01 | 검증 실패는 기존 봉투와 400으로 온다 | 로그인 / slot_indexes 빈 배열 POST / 400 VALIDATION_ERROR 봉투 (계약 변경 4) | web | 기존 회귀 + 필요 시 보강 | Pending |

특성화 테스트(TAG-PUT-01, TAG-DEL-01, TAG-DEL-03)는 이식 전 현재 코드에서
Green을 확인해 보호망으로 삼는다(신규 동작이 아니므로 Red 불요). 계약 변경
분(TAG-PUT-02, TAG-DEL-02, API-AUTH-01, API-DOCS-01)은 Red-Green을 지킨다.

## 구현 순서 (작은 커밋 단위)

1. 본 계획 문서 커밋
2. 보호 테스트 선행: tags PUT/DELETE 특성화 테스트 (현재 코드 Green 확인)
3. 의존성 + 스켈레톤: django-ninja 설치, `lifeDiary/api.py` 빈 NinjaAPI,
   기존 include 앞에 마운트 공존, `manage.py check` 통과
4. tags 라우터 이식 (categories GET → tags GET/POST → tags PUT/DELETE,
   500→404 Red-Green 포함)
5. dashboard 라우터 이식 (time-blocks POST/DELETE → undo POST, 401 갱신)
6. 전역 핸들러 + i18n (.po ko/en 갱신, ko msgstr 필수,
   `msgfmt --check-format` 검증)
7. 구 코드 제거: api_urls 2파일 삭제, 뷰 API 함수 제거,
   `reverse("tags_api:...")` 테스트 2건 경로 리터럴로 갱신
8. 문서 품질 패스: summary/description/예시, `docs/`에 API 문서 안내
9. 작업 로그 `docs/refactoring/` + `docs/project-status.md` 갱신, PR

## Verification

- 타깃: `conda run -n knou-life-diary pytest apps/tags apps/dashboard --tb=short`
- 전체 회귀: `conda run -n knou-life-diary pytest`
- `conda run -n knou-life-diary python manage.py check`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`
- `conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.desktop`
- `conda run -n knou-life-diary python manage.py makemigrations --check --dry-run`
- 브라우저: runserver 후 대시보드 슬롯 저장/삭제/undo, 태그 생성/수정/삭제
  클릭스루, `/api/docs` 렌더 + Try-it-out 1건, 콘솔 무오류

## Deferred Refactoring Note

- Topic: rate limiting·토큰 인증·API 버저닝, PyInstaller ninja 정적 번들 검증,
  프론트 JS의 에러 코드 활용, 봉투 base 스키마의 core 승격
- Why not now: 현재 승인 범위는 이식 + 문서화이며 소비자는 자체 프론트뿐
- Trigger: 외부 클라이언트 등장, desktop 패키징 트랙 재개, 봉투 중복 3회째
- Expected location: `lifeDiary/api.py`, `apps/core/schemas.py`(신설 시),
  desktop 패키징 spec
- Related tests: `apps/*/test_*` 웹 계층, `lifeDiary/test_prod_settings.py`
