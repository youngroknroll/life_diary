import pytest
from pathlib import Path

@pytest.mark.django_db
def test_login_page_has_enhance_and_no_test_creds(client):
    r = client.get('/accounts/login/')
    assert r.status_code == 200
    h = r.content.decode()
    assert 'auth-enhance.js' in h, 'auth-enhance.js script tag missing'
    assert 'TestID' not in h
    assert 'TestPWD' not in h
    assert 'tttt1234' not in h
    assert 'type="password"' in h
    assert 'auth-card' in h

@pytest.mark.django_db
def test_signup_page_has_enhance(client):
    r = client.get('/accounts/signup/')
    assert r.status_code == 200
    h = r.content.decode()
    assert 'auth-enhance.js' in h
    assert 'password-strength.js' in h
    assert h.count('type="password"') >= 2
    assert 'name="password1"' in h


@pytest.mark.django_db
def test_login_page_does_not_load_strength_meter(client):
    """Strength meter는 signup 전용. login에서는 로드되지 않아야 한다."""
    r = client.get('/accounts/login/')
    assert r.status_code == 200
    assert 'password-strength.js' not in r.content.decode()


@pytest.mark.django_db
def test_login_page_has_google_continue_link(client):
    r = client.get("/accounts/login/")

    assert r.status_code == 200
    h = r.content.decode()
    assert "Google로 계속하기" in h
    assert "/accounts/google/login/" in h


@pytest.mark.django_db
def test_login_page_google_button_has_blue_hover_style(client):
    r = client.get("/accounts/login/")

    assert r.status_code == 200
    h = r.content.decode()
    css = Path("apps/core/static/core/css/style.css").read_text()
    assert "auth-google-login" in h
    assert ".auth-google-login:hover" in css
    assert "background-color: #2563eb" in css
