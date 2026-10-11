"""PretendardVariable.woff2 를 서비스가 쓰는 문자만 남겨 다시 만든다.

원본(한글 음절 11,172자, 2.0MB)은 Pretendard 배포본에서 받고, 이 스크립트가
KS X 1001 한글 2,350자 + 라틴·구두점·기호 블록만 남긴다. 2,350자 밖의 드문
음절은 시스템 글꼴로 폴백한다. 가변 wght 축과 OpenType 레이아웃은 유지한다.

실행: python scripts/subset_pretendard.py <원본.woff2> <출력.woff2>
fonttools 와 brotli 가 필요하다(개발 도구이며 requirements 에는 넣지 않는다).
"""

import sys

from fontTools import subset
from fontTools.ttLib import TTFont

UNICODE_RANGES = [
    (0x0020, 0x024F),  # 기본 라틴, 라틴-1 보충, 라틴 확장 A·B
    (0x02C6, 0x02DC),  # 수식 문자(ˆ ˜ 등)
    (0x0300, 0x036F),  # 결합 분음 부호
    (0x0370, 0x03FF),  # 그리스 문자(μ, Ω 등 단위·수식)
    (0x2000, 0x206F),  # 일반 구두점(… – — ‘ ’ “ ” • ‰)
    (0x2070, 0x209F),  # 위·아래 첨자
    (0x20A0, 0x20CF),  # 통화 기호(₩ € ₹)
    (0x2100, 0x214F),  # 문자형 기호(℃ ™ № ℓ)
    (0x2150, 0x218F),  # 로마 숫자
    (0x2190, 0x21FF),  # 화살표
    (0x2200, 0x22FF),  # 수학 연산자(≤ ≥ ≠ ∞)
    (0x2300, 0x23FF),  # 기술 기호(⌘ ⏰ ⌫)
    (0x2460, 0x24FF),  # 원문자·괄호 숫자
    (0x25A0, 0x25FF),  # 도형(■ □ ● ○ ◆ ▶)
    (0x2600, 0x26FF),  # 기타 기호(★ ☆ ☑ ⚠)
    (0x2700, 0x27BF),  # 딩벳(✓ ✔ ✕ ✗)
    (0x1100, 0x11FF),  # 한글 자모(옛한글 조합용)
    (0x3000, 0x303F),  # CJK 구두점(、。「」『』〈〉 전각 공백)
    (0x3130, 0x318F),  # 한글 호환 자모(ㄱ ㅏ ㆍ)
    (0xFF00, 0xFFEF),  # 전각 영숫자·구두점, 반각 가나
]


def ksx1001_hangul_syllables():
    """KS X 1001 완성형 한글 2,350자.

    cp949 는 11,172자를 모두 인코딩하지만 KS X 1001 영역(선두 바이트 B0~C8)에
    놓이는 것은 2,350자뿐이다. 나머지는 확장 영역(81~A0, A1~C6 의 하위 바이트)이다.
    """
    syllables = []
    for codepoint in range(0xAC00, 0xD7A4):
        lead, trail = chr(codepoint).encode("cp949")
        if 0xB0 <= lead <= 0xC8 and 0xA1 <= trail <= 0xFE:
            syllables.append(codepoint)
    assert len(syllables) == 2350, len(syllables)
    return syllables


def build_unicodes():
    unicodes = set(ksx1001_hangul_syllables())
    for start, end in UNICODE_RANGES:
        unicodes.update(range(start, end + 1))
    return sorted(unicodes)


def main(source, target):
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True
    options.recalc_average_width = True
    options.drop_tables += ["DSIG"]

    font = TTFont(source)
    before = len(font.getBestCmap())
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=build_unicodes())
    subsetter.subset(font)
    font.flavor = "woff2"
    font.save(target)

    result = TTFont(target)
    cmap = result.getBestCmap()
    hangul = sum(1 for c in cmap if 0xAC00 <= c <= 0xD7A3)
    axes = [(a.axisTag, a.minValue, a.maxValue) for a in result["fvar"].axes]
    print(f"codepoints {before} -> {len(cmap)} (hangul {hangul}), axes {axes}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
