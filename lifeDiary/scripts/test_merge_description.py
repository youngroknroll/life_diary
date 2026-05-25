from scripts.merge_description import (
    extract_bullets,
    extract_doc_paths,
    render_description,
)


def test_extract_bullets_keeps_korean_body_items_only():
    message = """add: 로그인 reCAPTCHA 검증 추가

- 로컬 개발환경에서 axes 계정 잠금을 비활성화
- 배포환경에서 로그인 실패 5회 이후 reCAPTCHA 확인을 요구하도록 추가
- reCAPTCHA 통과와 올바른 비밀번호 입력 시 정상 로그인되도록 수정
- 집중 테스트를 추가하고 프로젝트 상태/리팩터링 문서 갱신

Verification:
- pytest apps/users/tests.py
"""

    assert extract_bullets(message) == [
        "로컬 개발환경에서 axes 계정 잠금을 비활성화",
        "배포환경에서 로그인 실패 5회 이후 reCAPTCHA 확인을 요구하도록 추가",
        "reCAPTCHA 통과와 올바른 비밀번호 입력 시 정상 로그인되도록 수정",
        "집중 테스트를 추가하고 프로젝트 상태/리팩터링 문서 갱신",
    ]


def test_extract_doc_paths_finds_plan_and_refactoring_paths():
    changed_files = [
        "apps/users/views.py",
        "docs/plans/2026-05-25-login-recaptcha-after-failures.md",
        "docs/refactoring/2026-05-25_login-recaptcha-after-failures.md",
    ]

    assert extract_doc_paths(changed_files) == [
        "docs/plans/2026-05-25-login-recaptcha-after-failures.md",
        "docs/refactoring/2026-05-25_login-recaptcha-after-failures.md",
    ]


def test_render_description_uses_short_sections():
    description = render_description(
        bullets=[
            "로컬 개발환경에서 axes 계정 잠금을 비활성화",
            "배포환경에서 로그인 실패 5회 이후 reCAPTCHA 확인을 요구하도록 추가",
        ],
        verification=[
            "pytest apps/users/tests.py lifeDiary/test_prod_settings.py --tb=short",
            "python manage.py check",
        ],
        docs=[
            "docs/plans/2026-05-25-login-recaptcha-after-failures.md",
            "docs/refactoring/2026-05-25_login-recaptcha-after-failures.md",
        ],
    )

    assert description == """## 변경 요약

- 로컬 개발환경에서 axes 계정 잠금을 비활성화
- 배포환경에서 로그인 실패 5회 이후 reCAPTCHA 확인을 요구하도록 추가

## 검증

- pytest apps/users/tests.py lifeDiary/test_prod_settings.py --tb=short
- python manage.py check

## 문서

- docs/plans/2026-05-25-login-recaptcha-after-failures.md
- docs/refactoring/2026-05-25_login-recaptcha-after-failures.md"""
