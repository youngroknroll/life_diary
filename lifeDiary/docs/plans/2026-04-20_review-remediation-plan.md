# 2026-04-20 코드리뷰 대응 플랜

> 기반: 외부 코드리뷰 5건 (API 응답 계약, 테스트 수집, HTML 마크업, 레이어 일관성, 정적 자산 중복)
> 목표: 실행·통합 레벨 회귀 제거 + 레이어 기준 통일
> 실행 순서는 영향도·수정 비용·회귀 위험 기준.

---

## 검증 결과 요약

| # | 지적 | 증거 | 심각도 |
|---|------|------|--------|
| 1 | API 응답 계약 불일치 | `success_response`는 `data` 래핑, 프론트(JS)·`apps/tags/tests.py:270`는 최상위 `tags`/`categories` 기대. `manage.py test`에서 3건 실패 | **CRITICAL** |
| 2 | 테스트 수집 누락 | pytest 9건만, Django runner 36건. `pytest.ini` 없음 → CI에서 3건 실패 감지 불가 | **CRITICAL** |
| 3 | HTML 마크업 버그 | `apps/dashboard/templates/dashboard/index.html:158` 닫는 `>` 누락 | HIGH |
| 4 | 레이어링 비일관 | `apps/users/views.py`의 goal/note CRUD가 뷰에서 직접 폼 저장·모델 조작·리다이렉트 | HIGH |
| 5 | 정적 자산 중복 | `staticfiles/` 134개가 git 추적, `.gitignore` 미등록 | MEDIUM |

---

## Phase A — API 응답 계약 통일 (CRITICAL)

### 진단

- `success_response(message, data=None)`가 `{"success": True, "message": ..., "data": {...}}`로 감싼다.
- 반면 프론트·테스트 모두 **플랫 구조**(`result.tags`, `data["tags"]`)를 기대한다.
- 대시보드 프론트는 `result.message`만 사용 → 플랫 전환 시에도 무해.
- **CSRF 토큰·카운트 키 등 상위 키와 충돌 없는지 선검증 필요.**

### 결정

`success_response`의 반환 구조를 **플랫(spread)** 으로 변경. 기존 케이스별 대응보다 설계 일관성이 높다.

변경 전:
```python
if data:
    response_data["data"] = data
```
변경 후:
```python
if data:
    response_data.update(data)
```

### 변경 파일

- `apps/core/utils.py` — `success_response` 수정
- (영향 확인) `apps/tags/views.py`, `apps/dashboard/views.py` 호출부는 그대로.

### 검증

1. `.venv/bin/python manage.py test apps.tags` — 3건 failing → pass 확인
2. `.venv/bin/python manage.py test` 전체 — 0 failures
3. dashboard 페이지 수동 재확인(필요 시): 저장/삭제 토스트 메시지 정상 표시

---

## Phase B — pytest 통합 설정 (CRITICAL)

### 진단

- 저장소 루트에 pytest 설정 파일 없음 → `apps/*/tests.py` 36건이 pytest 대상에서 제외됨.
- `conftest.py`는 `settings.configure()` 수동 호출 — `pytest-django`가 아닌 Django-only 모드로 돌고 있다.

### 결정

`pytest-django` 방식으로 통일. `conftest.py`는 `DummyCache`만 강제하고 설정 로딩은 Django에 위임.

### 변경 파일

1. `pytest.ini` (신규):
   ```ini
   [pytest]
   DJANGO_SETTINGS_MODULE = lifeDiary.settings.dev
   python_files = tests.py test_*.py *_tests.py
   addopts = --reuse-db
   ```
2. `requirements.txt` — `pytest-django` 추가 확인 (이미 있으면 skip)
3. `conftest.py` — `settings.configure(...)` 블록 제거, 캐시 override 만 남기거나 단순화
4. `lifeDiary/settings/dev.py` — 테스트 전용 캐시가 필요하면 `pytest` 경로에서 override되도록 정리

### 검증

- `.venv/bin/pytest --collect-only -q` → **36+ 건** 수집 확인
- `.venv/bin/pytest -q` → Phase A 수정 후 전체 pass

---

## Phase C — HTML 마크업 수정 (HIGH)

### 진단

`apps/dashboard/templates/dashboard/index.html:158`
```html
<div class="col-lg-4" id="quickInputSidebar" data-tags-url="{% url 'tags:index' %}"
```
닫는 `>` 누락.

### 변경

- 라인 끝에 `>` 추가
- 파일 내 유사 패턴(다줄 속성) 스캔

### 검증

- HTML 렌더 확인: `grep -nE '<(div|span|section)[^>]*$' apps/*/templates/**/*.html`에서 이 줄이 사라지는지 확인
- 대시보드 페이지 DOM 구조 수동 점검 (선택)

---

## Phase D — users CRUD Use Case 도입 (HIGH)

### 진단

`apps/users/views.py`에서 `usergoal_create/update/delete`, `usernote_create/update`가:
- `form.save(commit=False)` → `goal.user = request.user` → `goal.save()` 를 뷰가 직접 수행
- 리다이렉트 경로(`redirect("users:mypage")`)도 뷰에 산재
- dashboard/tags/stats는 Use Case 계층을 지나는데 users만 예외

### 결정 범위

**최소 침습 원칙**: 뷰는 "폼 검증 + Use Case 호출 + 리다이렉트"만 책임지고, 엔티티 소유권 할당·저장은 Use Case로 이동.

새 Use Case:
- `CreateGoalUseCase.execute(user, form_data) -> Goal`
- `UpdateGoalUseCase.execute(user, goal_id, form_data) -> Goal`
- `DeleteGoalUseCase.execute(user, goal_id) -> None`
- `CreateNoteUseCase.execute(user, form_data) -> Note`
- `UpdateNoteUseCase.execute(user, note_id, form_data) -> Note`

(`usergoal_delete`는 `@require_http_methods(["GET","POST"])` 유지 + Use Case 호출만 교체.)

### 변경 파일

- `apps/users/use_cases.py` — Use Case 5종 추가
- `apps/users/views.py` — 폼 저장·모델 조작 로직 제거, Use Case 위임

**폼 자체(`UserGoalForm`, `UserNoteForm`)는 그대로 유지** — ModelForm이 DB-boundary validator 역할 수행.

### 검증

- `.venv/bin/pytest -q apps/users` — 기존 테스트 유지
- 기능 스모크 테스트(로컬):
  - 목표 추가/수정/삭제
  - 노트 추가/수정
  - 리다이렉트 경로 불변 확인

---

## Phase E — 정적 자산 정리 (MEDIUM)

### 진단

- `staticfiles/` 134개 파일이 git에 추적됨. `collectstatic` 산출물.
- 소스 파일(`apps/*/static/...`)과 공존 → 수정 경로 혼동.

### 결정

- `.gitignore`에 `/staticfiles/` 추가
- `git rm -r --cached staticfiles/` 로 추적 해제 (워크트리에는 남김, 배포 시 재생성)

### 변경 파일

- `.gitignore` — `/staticfiles/` 라인 추가
- Git index에서 `staticfiles/` 제거 (커밋 필요)

### 검증

- `git status` → `staticfiles/` 변경 없음
- `git ls-files staticfiles/` → 빈 결과
- `.venv/bin/python manage.py collectstatic --noinput --dry-run` → 정상 수집 계획 표시

### 주의

- Render 배포 단계에서 `collectstatic`이 build hook/release phase에 포함돼 있는지 확인
  (`Procfile` 혹은 `render.yaml` 재검토)

---

## 실행 순서

1. **Phase A** → `manage.py test` 0 failures로 만드는 것이 최상위 우선
2. **Phase B** → pytest도 36+건을 돌리게 만들어 이후 변경의 회귀 감지 가능하게
3. **Phase C** → 1줄 수정, 리스크 없음
4. **Phase D** → 설계 작업. A·B 완료 후 회귀 감지선 위에서 진행
5. **Phase E** → 커밋 분리, 단독 수행

---

## 롤백 전략

각 Phase 단위 커밋 → 문제 발생 시 `git revert <phase-commit>` 로 개별 롤백.

## 성공 지표

- `.venv/bin/python manage.py test` → **0 failures**
- `.venv/bin/pytest -q` → **36+ passed**
- 대시보드·태그 페이지 실사용 회귀 없음
- `staticfiles/` git 미추적, 배포 파이프라인 정상
- users 앱이 dashboard/tags/stats와 동일한 레이어 규약 준수
