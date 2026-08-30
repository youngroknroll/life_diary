# 2026-08-31 파비콘 교체 — 파스텔 파이 차트 아이콘

## 배경

링크 공유 시 사이트 아이콘이 뜨게 해 달라는 사용자 요청. OG 대표 이미지는
사용자 결정으로 생략하고, 사용자가 제공한 파이 차트 이미지에서 도형만
추출해 파비콘으로 쓴다. 기존 파비콘은 🕐 이모지 인라인 데이터 URI 라서
루트 `favicon.ico` 를 직접 요청하는 크롤러·구형 브라우저에는 잡히지
않았다.

## 산출물

원본 래스터를 자르는 대신, 원본에서 조각 각도와 색을 측정해 도형을
벡터로 재생성했다(모든 크기에서 선명, 배경 투명).

측정값 — 중심 (1290,798), 반지름 370px, 경계각(반시계, 0°=동쪽)
110 / 155.4 / 222.5 / 311.9 / 349.6, 조각 간 간격 2.5°:

| 조각 | 색 |
|---|---|
| 초록 | `#e6efdc` |
| 파랑 | `#e1e9f5` |
| 주황 | `#f3cbb1` |
| 보라 | `#d3c4e5` |
| 노랑 | `#fdefd0` |

## 변경 파일

- `apps/core/static/core/img/favicon.svg` (479B) — 기본 아이콘
- `apps/core/static/core/img/favicon-32.png` (2.2KB) — PNG 폴백
- `apps/core/static/core/img/apple-touch-icon.png` (9.3KB, 180px 흰 배경)
- `templates/base.html` — 이모지 데이터 URI 를 위 3개 `<link>` 로 교체,
  `{% load static %}` 를 파비콘 블록 위로 이동
- `lifeDiary/urls.py` — `/favicon.ico` → 비해시 정적 경로 302. manifest
  조회 없이 import 시점에 안전하도록 `settings.STATIC_URL` 문자열 결합.

## 검증 (2026-08-31, 로컬)

- `manage.py check` — 0 이슈
- runserver + curl: 홈 HTML 에 3개 링크 태그 출력, `/favicon.ico` 302 →
  `/static/core/img/favicon-32.png`, svg/png 3종 모두 200
- prod 설정 collectstatic — exit 0, `staticfiles.json` 에 3개 항목 해시
  등록(`favicon.077d7558df3f.svg` 등)
- 생성 이미지 렌더링을 원본과 육안 대조(조각 배치·색 일치)

## 후속 참고

- 카카오톡 등은 미리보기를 캐시하므로 배포 후 카카오 공유 디버거에서
  캐시 초기화가 필요할 수 있다.
- 파스텔 톤이라 어두운 테마 탭에서는 대비가 낮다. 필요해지면 색 농도를
  올린 다크 전용 변형을 검토한다(현재는 원본 충실 재현이 사용자 요청).
