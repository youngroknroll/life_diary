# 2026-04-28 테스트 unittest → pytest 일괄 전환 실행 로그

> 실행일: 2026-04-28
> 목표: pytest-django 러너 위에서 작성 스타일도 pytest-native로 통일. 다국어 확장(영어→일본어)을 대비해 fixture/parametrize 활용 기반 마련.

---

## 배경

- 러너는 이미 pytest(`pytest.ini` + `pytest-django 4.12`)지만, **테스트 코드는 unittest 스타일**(`TestCase` + `self.assert*` + `setUp/setUpTestData`)로 작성돼 있었다.
- `force_login` 14곳, `HTTP_ACCEPT_LANGUAGE = "en"` 8곳 보일러플레이트가 반복.
- 미국·일본 런칭 계획에 맞춰 다국어 테스트를 `parametrize`로 압축할 필요.

## 사용자 결정

- **범위**: 전체 일괄 (11파일, 100+ 테스트)
- **DB scope**: 클래스 단위 + `setUpTestData`를 fixture로 대체

## 결과 요약

| 항목 | 변환 전 | 변환 후 |
|------|--------|--------|
| 테스트 통과 수 | 111 | 111 |
| 11파일 LOC 합계 | 1,108 | 953 (−14%) |
| `force_login` 직접 호출 | 14곳 | conftest fixture 1개 |
| `HTTP_ACCEPT_LANGUAGE` 직접 설정 | 8곳 | `en_client`/`ko_client` |
| `User.objects.create_user(...)` 보일러 | 다수 | `make_user` factory |

---

## Phase A — 인프라 (conftest 확장 + 신규)

### 변경 파일
- `conftest.py` (확장)
- `apps/tags/conftest.py` (신규)
- `apps/dashboard/conftest.py` (신규)
- `apps/users/conftest.py` (신규)

### 루트 `conftest.py` 추가 fixture
- `en_client` / `ko_client`: `client.defaults["HTTP_ACCEPT_LANGUAGE"]` 강제 설정
- `make_user(username=None, password="pass-Long-9!")`: counter 기반 user factory
- `auth_client`: `make_user` + `force_login` 적용된 client (`client.user`로 user 접근)
- `auth_en_client`: 영어 locale + 로그인 결합

### 앱별 factory
- `apps/tags/conftest.py`: `category_factory`, `tag_factory` (count 기반 unique slug/name)
- `apps/dashboard/conftest.py`: `time_block_factory`
- `apps/users/conftest.py`: `goal_factory`

기존 autouse `_use_dummy_cache`, `AXES_ENABLED=False` 픽스처는 그대로 유지.

---

## Phase B — i18n 5파일 변환

| 파일 | 클래스 → 함수형 클래스 |
|------|----------------------|
| `apps/core/test_i18n_phase1.py` | 2 클래스, 5 테스트 |
| `apps/dashboard/test_i18n_phase2.py` | 1 클래스, 4 테스트 |
| `apps/tags/test_i18n_phase3.py` | 1 클래스, 4 테스트 |
| `apps/users/test_i18n_phase4.py` | 5 클래스, 8 테스트 |
| `apps/stats/test_i18n_phase5.py` | 2 클래스, 6 테스트 |

### 적용 패턴
- `setUpTestData(cls)` + `setUp(self).client.force_login(...)` 보일러 → `auth_en_client` fixture 1개
- `self.assertContains(resp, X)` → `assert X in resp.content.decode()`
- `self.assertNotContains(...)` → `assert X not in body`

### 발견 이슈 — locale leak
`TestFormatTimeDisplay.test_korean_default` 단독 실행은 통과하지만 전체 실행 시 실패:
- 다른 테스트가 `activate("en")` 후 `deactivate()` 누락 또는 `en_client` 사용으로 active locale이 영어로 누수.
- 한국어 기본값 가정이 깨짐 → `format_time_display(2, 30) == "2h 30m"` 결과.

**수정**: 명시적으로 `activate("ko")` … `deactivate()` 컨텍스트 추가하여 locale 독립성 확보.

---

## Phase C — 앱 본 테스트 5파일 변환

### `apps/core/tests.py` (HomePageTests, 2건)
- 한국어 카피 검증 — `ko_client` fixture로 locale 보장 (Phase B와 동일 leak 회피)

### `apps/dashboard/tests.py` (3 클래스 → 함수+fixture, 7건)
- `_extract_element` HTMLParser 헬퍼는 클래스 메서드에서 모듈 함수로 추출
- `dash_user_with_tags` composite fixture: ko_client + 로그인 + 카테고리 정렬용 태그 2개 생성
- `SimpleTestCase` (`build_time_headers`, `validate_slot_indexes`) → 평문 클래스

### `apps/stats/tests.py` (3 클래스, 11건)
- DB 무관 services 테스트 → `@pytest.mark.django_db` 미부여
- `_make_day` 헬퍼 모듈 함수로 추출

### `apps/users/tests.py` (3 클래스, 5건)
- `alice_bob_with_bob_tag` composite fixture로 IDOR 회귀 테스트의 두 user + 태그 setup 압축
- `override_settings(AXES_ENABLED=True, ...)` context manager 그대로 함수 본문에서 사용

### `apps/tags/tests.py` (9 클래스, 28건 — 가장 큼)
- `_render` 모듈 함수로 추출 (3 템플릿 태그 테스트 공유)
- `auth_client.user` 활용으로 별도 user 변수 불필요 (`Tag.objects.create(user=auth_client.user, ...)`)
- `from django.db.models import ProtectedError` import 위치 정리

### 변환 전후 (앱 테스트만)
| 파일 | 전 | 후 |
|------|----|----|
| core/tests.py | 29 | 25 |
| dashboard/tests.py | 142 | 135 |
| stats/tests.py | 105 | 85 |
| users/tests.py | 99 | 94 |
| tags/tests.py | 343 | 298 |

---

## Phase D — 검증

```bash
conda run -n knou-life-diary pytest --tb=short
# 111 passed in 45.02s
```

- 통과 수 동일 (111 → 111)
- 회귀 0건
- `pytest --collect-only`로 모든 테스트 정상 발견 확인

---

## 변경하지 않은 파일 (이미 pytest)

- `apps/core/test_messages.py`
- `apps/dashboard/test_use_cases.py`
- `apps/users/test_use_cases.py`
- `apps/users/test_goal_repository.py`
- `apps/stats/test_stats_perf.py`

---

## 변환 매핑 (참고)

| unittest | pytest |
|----------|--------|
| `class XTests(TestCase):` | `@pytest.mark.django_db\nclass TestX:` |
| `class YTests(SimpleTestCase):` | `class TestY:` (마커 없음) |
| `setUp(self).client.force_login(user)` | `auth_client` fixture |
| `setUp(self).client.defaults["HTTP_ACCEPT_LANGUAGE"]="en"` | `en_client`/`auth_en_client` |
| `self.assertEqual(a, b)` | `assert a == b` |
| `self.assertContains(resp, x)` | `assert x in resp.content.decode()` |
| `self.assertRaises(E)` | `with pytest.raises(E):` |
| `setUpTestData(cls)` | class fixture 또는 함수별 factory 호출 |

---

## 후속 과제 (옵션)

1. **parametrize 도입**: ko/en locale 토글 다국어 테스트 1건 시범 — Phase B 변환 결과 즉시 적용 가능.
2. **factory_boy 도입**: 현재 단순 fixture로 충분하지만, UserGoal+Tag+Category 조합 시드가 늘면 검토.
3. **locale leak 가드**: pytest fixture(autouse, function-scope)로 매 테스트 후 `deactivate()` 호출 — 현재는 케이스별 처리.

---

## 핵심 파일

- 인프라: `conftest.py`, `apps/{tags,dashboard,users}/conftest.py`
- 변환된 테스트 11개: `apps/{core,dashboard,stats,users,tags}/{tests,test_i18n_phase*}.py`
