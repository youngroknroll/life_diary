# API 문서(OpenAPI/Swagger) 안내

- 날짜: 2026-08-16
- 관련 계획: `docs/plans/2026-08-16_api-openapi-django-ninja-plan.md`

## 보는 곳

- Swagger UI: `/api/docs` (runserver 기준 http://127.0.0.1:8000/api/docs)
- OpenAPI 3 스키마(JSON): `/api/openapi.json`

문서 페이지는 전 환경에서 공개다. 데이터 엔드포인트 자체는 전부 세션
인증(`django_auth`) 뒤에 있으므로 스키마 공개가 데이터 접근을 열지 않는다.
Swagger 정적 자산은 `INSTALLED_APPS`의 `ninja` 등록으로 CDN 없이
staticfiles(whitenoise)로 서빙된다.

## 구조

```text
lifeDiary/api.py            # NinjaAPI 인스턴스, 전역 예외 핸들러, 라우터 조립
apps/dashboard/api.py       # time-blocks 저장/삭제/undo 오퍼레이션
apps/dashboard/schemas.py   # 대시보드 요청·응답 Schema
apps/tags/api.py            # 카테고리 조회, 태그 CRUD 오퍼레이션
apps/tags/schemas.py        # 태그 요청·응답 Schema
apps/core/schemas.py        # 공통 봉투(MessageEnvelope, ErrorEnvelope)
```

오퍼레이션은 HTTP 계층만 담당하고 검증·비즈니스 규칙은 기존
`use_cases`/`commands`가 그대로 갖는다
(`api → use_cases → repositories/domain_services → models`).

## 응답 계약

- 성공: `{"success": true, "message": "...", ...필드 평탄 병합}`
- 오류: `{"success": false, "message": "...", "error": "코드"}`
- 프론트 `apiCall()`(apps/core/static/core/js/utils.js)은 HTTP 상태와
  `message`만 소비한다. 오류 응답에서 이 둘은 반드시 유지한다.

전역 예외 핸들러(`lifeDiary/api.py`)가 봉투를 보장한다:

| 상황 | 상태 | error 코드 |
|---|---|---|
| 미인증 | 401 | `UNAUTHORIZED` |
| 요청 스키마 검증 실패 | 400 | `VALIDATION_ERROR` (첫 오류 메시지) |
| 본문 JSON 파싱 실패 | 400 | `INVALID_JSON` |

## 새 엔드포인트 추가 절차

1. 소유 앱의 `schemas.py`에 요청/응답 `Schema`를 정의한다. 응답 스키마에
   없는 키는 직렬화에서 탈락하므로 클라이언트가 읽는 필드를 빠짐없이 적는다.
2. 소유 앱의 `api.py` 라우터에 오퍼레이션을 추가하고 `summary`,
   `description`, 상태코드별 `response`를 채운다. 이것이 곧 문서다.
3. 검증·규칙은 use case/command에 두고 오퍼레이션은 예외→봉투 매핑만 한다.
4. 새 사용자 노출 문자열은 `locale/ko`(항등)·`locale/en` 카탈로그에 추가하고
   `msgfmt --check-format`으로 확인한다.
5. 웹 계층 테스트는 경로 리터럴(`/api/...`)로 요청해 URL 계약을 고정한다.

## 프론트엔드 협업 메모

- 스키마 파일 하나로 계약을 공유한다: `/api/openapi.json`을 그대로 전달하면
  Swagger UI, Postman, openapi-typescript 등에서 바로 쓸 수 있다.
- URL 경로는 프론트 JS 12곳에 리터럴로 박혀 있으므로 경로 변경은 곧
  프론트 파손이다. 경로를 바꾸려면 프론트 트랙과 함께 움직인다.
