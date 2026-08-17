# django-ninja 이식 + OpenAPI/Swagger 문서화 실행 로그

- 날짜: 2026-08-16
- 브랜치: `feat/api-openapi-ninja` (base: main c4a7e90)
- 계획: `docs/plans/2026-08-16_api-openapi-django-ninja-plan.md`
- 안내: `docs/architecture/2026-08-16_api-documentation-guide.md`

## 무엇을 했나

JSON API 5개 엔드포인트를 URL과 응답 봉투를 그대로 보존한 채
django-ninja 라우터로 이식하고, `/api/docs`(Swagger UI)와
`/api/openapi.json`(OAS 3.1)을 추가했다. 승인된 계약 변경 4건만 반영했다.

## 변경 파일

- 신설: `lifeDiary/api.py`(NinjaAPI 조립 + 전역 예외 핸들러),
  `apps/dashboard/api.py`·`schemas.py`, `apps/tags/api.py`·`schemas.py`,
  `apps/core/schemas.py`(공통 봉투), `lifeDiary/test_api_docs.py`,
  `apps/tags/test_tag_update_delete_api.py`
- 수정: `lifeDiary/urls.py`(ninja 마운트), `requirements.txt`
  (`django-ninja==1.6.2`), `lifeDiary/settings/dev.py`·`desktop.py`
  (INSTALLED_APPS `ninja` — Swagger 자산 로컬 서빙),
  `locale/{ko,en}/LC_MESSAGES/django.po`(신규 3문자열),
  `apps/dashboard/test_undo.py`(401), `apps/tags/test_i18n_phase3.py`
  (INVALID_JSON 문구 통일), `apps/tags/test_category_i18n.py`(경로 리터럴)
- 삭제: `apps/dashboard/api_urls.py`, `apps/tags/api_urls.py`,
  두 views.py의 API 함수·헬퍼

## 계약 변경 (계획 승인분)

1. 미인증 API 호출 302 리다이렉트 → 401 JSON 봉투
2. 깨진 JSON 메시지를 "올바른 JSON 형식이 아닙니다."로 통일
3. 미소유·없는 태그 PUT/DELETE 500 → 404 `TAG_NOT_FOUND`
4. 요청 스키마 검증 실패 → 400 `VALIDATION_ERROR` 봉투(첫 오류 메시지)

## Test List 결과

| Scenario ID | Test | Status | 증거 |
|---|---|---|---|
| TAG-PUT-01 | test_updating_own_tag_name_returns_updated_tag | Green | 이식 전 특성화 Green → 이식 후 Green |
| TAG-PUT-02 | test_updating_foreign_tag_is_refused_as_not_found | Green | Red 검증: `except Http404` 제거 시 500으로 실패 확인 후 복원 |
| TAG-DEL-01 | test_deleting_own_tag_confirms_deletion | Green | 특성화, 이식 전후 Green |
| TAG-DEL-02 | test_deleting_missing_tag_is_refused_as_not_found | Green | TAG-PUT-02와 동일한 Red-Green 사이클 |
| TAG-DEL-03 | test_deleting_tag_moves_blocks_to_requested_tag | Green | 특성화, 이식 전후 Green |
| API-AUTH-01 | test_undo_requires_login (401로 갱신) | Green | 이식 직후 (302,403) 단언이 401로 실패 → 갱신 후 Green |
| API-JSON-01 | test_create_tag_invalid_json (기대값 갱신) | Green | 이식 직후 구 문구 단언 실패 → 통일 문구로 Green |
| API-DOCS-01 | test_openapi_schema_lists_all_five_endpoints | Green | 구현 후 작성 — 사전 Red 미수행(스키마 자동 생성 특성상 생략) |
| API-VAL-01 | 기존 회귀(pydantic 커맨드 검증 경로 유지) | Green | test_undo.py 16건 포함 전체 회귀 |

## 검증 증거 (전부 이 세션에서 신규 실행)

- 전체 회귀: `conda run -n knou-life-diary pytest` → **506 passed** (296.9s)
- `manage.py check` → issues 0
- prod deploy check(`--fail-level ERROR`) → 통과 (W009 SECRET_KEY 경고 1건,
  로컬에 prod 시크릿 env가 없어 나는 기존 경고)
- `makemigrations --check --dry-run` → No changes detected
- `msgfmt --check-format` ko/en → 통과
- 브라우저(chrome-devtools, runserver, 일회용 계정 — 검증 후 삭제로 롤백):
  - 대시보드: 지금 시각 채우기 + 태그 선택 + 저장 → 201, 스낵바
    "1개의 슬롯이 저장되었습니다." + 되돌리기 버튼, 그리드·통계 즉시 갱신
  - 페이지 컨텍스트 apiCall: tag_id 누락 404, 저장 201, undo 200
    ("되돌렸습니다.", 통계 원복), 삭제 200 — 실제 세션·CSRF 경유
  - 태그 관리: 생성 201 → 수정 200(목록에 새 이름) → 삭제 200
    (confirm 다이얼로그 포함), 네트워크 로그로 전 요청 상태 확인
  - `/api/docs`: OAS 3.1, 8개 오퍼레이션, 스키마 목록 렌더 확인(스크린샷),
    Try-it-out으로 GET /api/categories/ 실행 → 200 실응답 표시
  - 콘솔: 오류 없음 (레이블 누락 a11y 이슈 1건 — 기존 폼 이슈)

## 검증하지 않은 것

- 데스크톱 설정 체크: `manage.py check --settings=desktop`은 **이 브랜치
  이전부터 실패** (ROOT_URLCONF가 allauth.urls를 include하는데 desktop
  INSTALLED_APPS에 allauth 없음 — 클린 트리에서 재현 확인). 범위 밖 기존
  결함으로 보고만 한다.
- 스크린리더 실통과, PyInstaller 번들에서의 Swagger 정적 자산.

## Deferred Refactoring Note

- Topic: rate limiting·토큰 인증·API 버저닝, PyInstaller ninja 정적 번들
  검증, 프론트 JS의 에러 코드(`error`) 활용, desktop settings의
  allauth URLConf 불일치 수정
- Why not now: 승인 범위는 이식 + 문서화. desktop 결함은 이 트랙 이전부터
  존재하는 별도 사안
- Trigger: 외부 API 소비자 등장, desktop 패키징 트랙 재개
- Expected location: `lifeDiary/api.py`, `lifeDiary/settings/desktop.py`,
  desktop 패키징 spec
- Related tests: `lifeDiary/test_api_docs.py`, `apps/*` 웹 계층 테스트
