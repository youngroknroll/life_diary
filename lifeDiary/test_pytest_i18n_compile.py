import conftest

from conftest import _compile_test_messages

LOCALE_DIR = conftest.BASE_DIR / "locale" if hasattr(conftest, "BASE_DIR") else None


def _catalog_pairs():
    import pathlib

    base = pathlib.Path(__file__).resolve().parent / "locale"
    for language in ("en", "ko"):
        messages = base / language / "LC_MESSAGES"
        for domain in ("django", "djangojs"):
            yield messages / f"{domain}.po", messages / f"{domain}.mo"


def test_compile_test_messages_leaves_every_catalog_compiled_and_current():
    _compile_test_messages()

    for po_path, mo_path in _catalog_pairs():
        assert mo_path.exists(), mo_path
        assert mo_path.stat().st_mtime >= po_path.stat().st_mtime, mo_path


def test_compile_test_messages_uses_python_fallback_when_msgfmt_is_missing(monkeypatch):
    calls = []

    def fake_python_fallback():
        calls.append("fallback")

    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr(
        conftest,
        "_compile_message_catalogs_without_msgfmt",
        fake_python_fallback,
        raising=False,
    )

    _compile_test_messages()

    assert calls == ["fallback"]
