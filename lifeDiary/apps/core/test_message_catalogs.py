"""메시지 카탈로그 계약.

makemessages 의 fuzzy 매칭은 새 문자열에 비슷하게 생긴 다른 문자열의 번역을
붙인다. compilemessages 는 fuzzy 항목을 통째로 건너뛰므로 화면에는 원문이
그대로 나오고, 눈으로 보기 전까지 아무도 모른다. 여기서 잡는다.
"""

import re

import pytest
from django.conf import settings


HANGUL = re.compile(r"[가-힣]")
ENTRY = re.compile(r'^msgid "(.*)"\n^msgstr "(.*)"', re.M)

CATALOGS = [
    (locale, name)
    for locale in ("ko", "en")
    for name in ("django", "djangojs")
]


def read_entries(locale, name):
    path = settings.BASE_DIR / f"locale/{locale}/LC_MESSAGES/{name}.po"
    if not path.exists():
        return []
    return [
        (msgid, msgstr)
        for msgid, msgstr in ENTRY.findall(path.read_text())
        if msgid
    ]


@pytest.mark.parametrize("locale,name", CATALOGS)
def test_translated_entries_are_not_left_fuzzy(locale, name):
    """번역을 채운 항목에 fuzzy 가 남으면 compilemessages 가 건너뛴다."""
    path = settings.BASE_DIR / f"locale/{locale}/LC_MESSAGES/{name}.po"
    if not path.exists():
        pytest.skip(f"{path} 없음")

    blocks = path.read_text().split("\n\n")
    stale = [
        block.splitlines()[0]
        for block in blocks
        if "#, fuzzy" in block and 'msgstr ""' not in block
    ]

    assert not stale, f"fuzzy 플래그가 남은 항목: {stale}"


@pytest.mark.parametrize("name", ["django", "djangojs"])
def test_korean_catalog_keeps_source_strings_intact(name):
    """원문이 한국어면 ko 번역은 원문 그대로여야 한다.

    다르면 fuzzy 매칭이 엉뚱한 문자열을 물려준 것이다 — 기록이 기록률로,
    설정이 수정으로 바뀐 적이 있다.
    """
    drifted = [
        (msgid, msgstr)
        for msgid, msgstr in read_entries("ko", name)
        if HANGUL.search(msgid) and msgstr and msgstr != msgid
    ]

    assert not drifted, f"ko 번역이 원문과 다름: {drifted}"


@pytest.mark.parametrize("locale,name", CATALOGS)
def test_format_placeholders_survive_translation(locale, name):
    """번역이 %(name)s 를 잃으면 렌더 시점에 터진다."""
    mismatched = [
        (msgid, msgstr)
        for msgid, msgstr in read_entries(locale, name)
        if msgstr
        and set(re.findall(r"%\((\w+)\)", msgid)) != set(re.findall(r"%\((\w+)\)", msgstr))
    ]

    assert not mismatched, f"서식 인자 불일치: {mismatched}"
