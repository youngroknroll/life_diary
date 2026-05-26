import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


def _copyright_year_range():
    current_year = timezone.localtime(timezone.now()).year
    if current_year == 2025:
        return "2025"
    return f"2025-{current_year}"


@pytest.mark.django_db
class TestHomePage:
    def test_home_page_presents_simple_daily_recording_for_anonymous_user(self, ko_client):
        response = ko_client.get(reverse("home"))
        body = response.content.decode()
        assert '<html lang="ko">' in body
        assert "하루를 단순하게 기록하세요" in body
        assert "로그인하고 기록 시작" in body
        assert "활동을 고르고, 오늘의 흐름을 남기고, 돌아봅니다." in body
        assert "소비시간의 분류" in body
        assert 'data-bs-target="#homePreviewImageModal"' in body
        assert 'id="homePreviewImageModal"' in body
        assert "10분 단위" not in body

    def test_home_page_renders_korean_footer_copyright(self, ko_client):
        response = ko_client.get(reverse("home"))
        body = response.content.decode()
        years = _copyright_year_range()
        assert f"라이프 다이어리 &copy; {years} LogBetter. All rights reserved." in body
        assert "songyeongrok" not in body

    def test_home_page_renders_legal_footer_links(self, ko_client):
        response = ko_client.get(reverse("home"))
        body = response.content.decode()

        assert f'href="{reverse("privacy")}"' in body
        assert f'href="{reverse("terms")}"' in body
        assert "개인정보처리방침" in body
        assert "이용약관" in body

    def test_home_page_renders_header_utility_controls(self, ko_client):
        response = ko_client.get(reverse("home"))
        body = response.content.decode()

        assert 'class="navbar-utility-controls"' in body
        utility_start = body.index('class="navbar-utility-controls"')
        utility_end = body.index('<button class="navbar-toggler"', utility_start)
        utility_section = body[utility_start:utility_end]

        assert 'class="navbar-language-form"' in utility_section
        assert "navbar-language-select" in utility_section
        assert 'id="themeToggle"' in utility_section
        assert 'class="theme-toggle__label"' in utility_section
        assert "다크" in utility_section
        assert "fas fa-moon" not in utility_section
        assert "fas fa-sun" not in utility_section

    def test_home_page_uses_korean_tag_usage_guide_for_non_english_language(self, ko_client):
        ko_client.cookies[settings.LANGUAGE_COOKIE_NAME] = "ko"
        response = ko_client.get(reverse("home"))
        body = response.content.decode()

        assert "/static/core/img/tag_usage_guide.png" in body
        assert "/static/core/img/tag_usage_guide_en.png" not in body

    def test_home_page_uses_english_tag_usage_guide_for_english_language(self, en_client):
        en_client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = en_client.get(reverse("home"))
        body = response.content.decode()

        assert "/static/core/img/tag_usage_guide_en.png" in body
        assert "/static/core/img/tag_usage_guide.png" not in body

    def test_home_page_invites_authenticated_user_to_record_today(self, ko_client, make_user):
        user = make_user(username="daily-user")
        ko_client.force_login(user)
        response = ko_client.get(reverse("home"))
        body = response.content.decode()
        assert "daily-user님" in body
        assert "오늘 기록하기" in body
        assert "로그인하고 기록 시작" not in body

    def test_robots_txt_disallows_all_crawlers(self, ko_client):
        response = ko_client.get("/robots.txt")

        assert response.status_code == 200
        assert response["Content-Type"] == "text/plain"
        assert response.content.decode() == "User-agent: *\nDisallow: /\n"

    def test_privacy_policy_page_renders_current_service_scope(self, ko_client):
        response = ko_client.get(reverse("privacy"))
        body = response.content.decode()

        assert response.status_code == 200
        assert "개인정보처리방침" in body
        assert "사용자명, 이메일 주소, 비밀번호 해시" in body
        assert "시간 블록, 일기/메모, 태그, 목표" in body
        assert "로그인 상태 유지, CSRF 보호, 언어 설정" in body
        assert "logbetter.info@gmail.com" in body

    def test_terms_page_renders_current_service_scope(self, ko_client):
        response = ko_client.get(reverse("terms"))
        body = response.content.decode()

        assert response.status_code == 200
        assert "이용약관" in body
        assert "계정 책임" in body
        assert "사용자 기록과 콘텐츠" in body
        assert "지식재산권" in body
        assert "화면, 로고, UI, 코드, 문구, 디자인, 서비스 구조" in body
        assert "사용자 입력 데이터의 권리는 사용자에게" in body
        assert "서비스 보안, 인증, rate limit, reCAPTCHA 확인" in body
        assert "logbetter.info@gmail.com" in body
