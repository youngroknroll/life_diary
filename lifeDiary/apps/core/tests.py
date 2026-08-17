import pytest
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
        # 시안 5a 는 "하루 10분 단위 기록"을 히어로 kicker 로 쓴다.
        # 홈에서 10분 단위를 감추던 2026-04-11 결정을 뒤집은 것이다.
        assert "10분 단위" in body

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
