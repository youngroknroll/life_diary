import pytest

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
    assert h.count('type="password"') >= 2
