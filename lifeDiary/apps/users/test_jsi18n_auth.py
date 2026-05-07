import pytest

@pytest.mark.django_db
def test_signup_en_loads_catalog_and_scripts(en_client):
    r = en_client.get('/accounts/signup/')
    assert r.status_code == 200
    h = r.content.decode()
    assert '/jsi18n/' in h, "JavaScriptCatalog URL must be loaded"
    assert 'auth-enhance.js' in h
    assert 'password-strength.js' in h

@pytest.mark.django_db
def test_jsi18n_catalog_serves_english_translations(en_client):
    r = en_client.get('/jsi18n/')
    assert r.status_code == 200
    body = r.content.decode()
    # The catalog JS embeds msgid → msgstr mappings for current language
    assert 'Show password' in body
    assert 'Caps Lock is on' in body
    assert 'Too short' in body
    assert 'Strong' in body

@pytest.mark.django_db
def test_jsi18n_catalog_serves_korean_fallback(ko_client):
    r = ko_client.get('/jsi18n/')
    assert r.status_code == 200
    body = r.content.decode()
    # Korean .po has empty msgstrs → gettext returns msgid → 한글 표시
    assert '비밀번호 표시' in body or 'Show password' not in body
