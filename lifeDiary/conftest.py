import ast
import pytest
import shutil
import struct
from pathlib import Path
from django.core import management
from django.core.management.base import CommandError


def _compile_test_messages():
    if shutil.which("msgfmt") is None:
        _compile_message_catalogs_without_msgfmt()
        return

    try:
        management.call_command(
            "compilemessages",
            ignore=[".venv/*", ".worktrees/*", "staticfiles/*"],
            locale=["en", "ko"],
            verbosity=0,
        )
    except CommandError as exc:
        if "Can't find msgfmt" not in str(exc):
            raise
        _compile_message_catalogs_without_msgfmt()


def _compile_message_catalogs_without_msgfmt():
    """Compile project translation catalogs with a small Python-only writer."""
    locale_root = Path("locale")
    for source_path in sorted(locale_root.glob("*/LC_MESSAGES/*.po")):
        target_path = source_path.with_suffix(".mo")
        _compile_po_file(source_path, target_path)


def _compile_po_file(source_path: Path, target_path: Path):
    entries = _parse_po_entries(source_path.read_text(encoding="utf-8"))
    entries.sort(key=lambda item: item[0].encode("utf-8"))

    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("wb") as handle:
        _write_mo_file(handle, entries)


def _parse_po_entries(content: str):
    entries = []
    entry = {"msgctxt": None, "msgid": None, "msgid_plural": None, "msgstrs": {}}
    current_field = None

    def flush_entry():
        nonlocal entry, current_field
        if entry["msgid"] is None:
            return

        msgid = entry["msgid"]
        if entry["msgctxt"] is not None:
            msgid = f"{entry['msgctxt']}\x04{msgid}"

        if entry["msgid_plural"] is not None:
            original = f"{msgid}\x00{entry['msgid_plural']}"
            max_index = max(entry["msgstrs"]) if entry["msgstrs"] else 0
            translated = "\x00".join(entry["msgstrs"].get(index, "") for index in range(max_index + 1))
        else:
            original = msgid
            translated = entry["msgstrs"].get(0, "")

        entries.append((original, translated))
        entry = {"msgctxt": None, "msgid": None, "msgid_plural": None, "msgstrs": {}}
        current_field = None

    def append_value(field_name, value, field_index=None):
        if field_name == "msgctxt":
            entry["msgctxt"] = (entry["msgctxt"] or "") + value
        elif field_name == "msgid":
            entry["msgid"] = (entry["msgid"] or "") + value
        elif field_name == "msgid_plural":
            entry["msgid_plural"] = (entry["msgid_plural"] or "") + value
        elif field_name == "msgstr":
            entry["msgstrs"][field_index] = entry["msgstrs"].get(field_index, "") + value

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line:
            flush_entry()
            continue

        if line.startswith("#"):
            continue

        if line.startswith("msgctxt "):
            current_field = ("msgctxt", None)
            append_value("msgctxt", _decode_po_string(line[8:].lstrip()))
            continue

        if line.startswith("msgid_plural "):
            current_field = ("msgid_plural", None)
            append_value("msgid_plural", _decode_po_string(line[13:].lstrip()))
            continue

        if line.startswith("msgid "):
            if entry["msgid"] is not None:
                flush_entry()
            current_field = ("msgid", None)
            append_value("msgid", _decode_po_string(line[6:].lstrip()))
            continue

        if line.startswith("msgstr["):
            close_bracket = line.index("]")
            index = int(line[7:close_bracket])
            current_field = ("msgstr", index)
            append_value("msgstr", _decode_po_string(line[close_bracket + 1 :].lstrip()), index)
            continue

        if line.startswith("msgstr "):
            current_field = ("msgstr", 0)
            append_value("msgstr", _decode_po_string(line[7:].lstrip()), 0)
            continue

        if line.startswith('"') and current_field is not None:
            field_name, field_index = current_field
            append_value(field_name, _decode_po_string(line), field_index)

    flush_entry()
    return entries


def _decode_po_string(token: str) -> str:
    return ast.literal_eval(token)


def _write_mo_file(handle, entries):
    # GNU MO format: header, original table, translated table, then string data.
    originals = [original.encode("utf-8") for original, _ in entries]
    translations = [translated.encode("utf-8") for _, translated in entries]
    count = len(entries)
    header_size = 7 * 4
    table_size = count * 8
    originals_offset = header_size
    translations_offset = originals_offset + table_size
    strings_offset = translations_offset + table_size

    original_table = []
    translation_table = []
    string_data = bytearray()
    current_offset = strings_offset

    for original_bytes, translation_bytes in zip(originals, translations):
        original_table.append((len(original_bytes), current_offset))
        string_data.extend(original_bytes + b"\0")
        current_offset += len(original_bytes) + 1

    for translation_bytes in translations:
        translation_table.append((len(translation_bytes), current_offset))
        string_data.extend(translation_bytes + b"\0")
        current_offset += len(translation_bytes) + 1

    handle.write(
        struct.pack(
            "<IIIIIII",
            0x950412DE,
            0,
            count,
            originals_offset,
            translations_offset,
            0,
            0,
        )
    )

    for length, offset in original_table:
        handle.write(struct.pack("<II", length, offset))

    for length, offset in translation_table:
        handle.write(struct.pack("<II", length, offset))

    handle.write(string_data)


def pytest_sessionstart(session):
    _compile_test_messages()


@pytest.fixture(autouse=True)
def _use_dummy_cache(settings):
    """테스트 구간 동안 파일 기반 캐시 대신 DummyCache 사용."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
    settings.AXES_ENABLED = False
    settings.AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
    ]


@pytest.fixture
def en_client(client):
    """영어 locale 강제 client."""
    client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
    return client


@pytest.fixture
def ko_client(client):
    """한국어 locale 강제 client."""
    client.defaults["HTTP_ACCEPT_LANGUAGE"] = "ko"
    return client


@pytest.fixture
def make_user(db, django_user_model):
    """user factory — 호출마다 새 user 생성."""
    counter = {"n": 0}

    def _make(username=None, password="pass-Long-9!", **kwargs):
        counter["n"] += 1
        return django_user_model.objects.create_user(
            username=username or f"u{counter['n']}",
            password=password,
            **kwargs,
        )

    return _make


@pytest.fixture
def auth_client(client, make_user):
    """기본 user로 로그인된 client."""
    user = make_user()
    client.force_login(user)
    client.user = user
    return client


@pytest.fixture
def auth_en_client(en_client, make_user):
    """영어 locale + 로그인."""
    user = make_user()
    en_client.force_login(user)
    en_client.user = user
    return en_client
