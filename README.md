# Life Diary

Life Diary는 하루를 10분 단위로 기록하고, 그 기록을 태그와 통계로 다시 읽어보는 Django 기반 생활 로그 서비스입니다.  
입력 부담은 낮추고, 회고는 구조적으로 하자는 방향으로 만든 프로젝트입니다.

배포사이트 : [라이프 다이어리](https://lifediary.onrender.com/)
## 무엇을 할 수 있나

- 하루를 144개의 10분 슬롯으로 나눠 기록
- 태그와 카테고리로 활동 분류
- 태그별 일간, 주간, 월간 목표 시간 관리
- 메모와 함께 개인 운영 기록 보관
- 일간, 주간, 월간 통계와 규칙 기반 라이프 피드백 제공

## 핵심 흐름

1. 사용자가 대시보드에서 시간 구간을 선택합니다.
2. 선택한 슬롯에 태그와 메모를 저장합니다.
3. 저장된 기록은 목표, 통계, 피드백 화면으로 연결됩니다.
4. 사용자는 자신의 생활 패턴을 다시 확인하고 조정합니다.

조금 더 자세한 비즈니스 로직과 아키텍처 설명은 아래 문서를 보면 됩니다.

- [비즈니스 로직 및 아키텍처 플로우 가이드](lifeDiary/docs/architecture/2026-04-21_business-logic-and-architecture-guide.md)
- [백엔드 플로우 및 개선 메모](lifeDiary/docs/refactoring/2026-04-21_backend-flow-and-improvements.md)
- [아키텍처/비용 최적화 계획](lifeDiary/docs/plans/2026-04-21_architecture-and-cost-plan.md)

## 기술 스택

- Python 3.13
- Django 5.2
- SQLite(dev) / PostgreSQL(prod)
- WhiteNoise
- Gunicorn
- Pydantic
- Pytest / Django test runner

## 프로젝트 구조

```text
lifeDiary/
├─ apps/
│  ├─ dashboard/   # 시간 기록 조회/저장/삭제
│  ├─ tags/        # 태그, 카테고리 관리
│  ├─ users/       # 인증, 목표, 메모, 마이페이지
│  ├─ stats/       # 집계, 피드백, 캐시
│  └─ core/        # 공통 유틸리티와 정적 자산
├─ docs/           # 설계, 리팩터링, 구조 문서
├─ lifeDiary/      # Django 프로젝트 설정
├─ templates/      # 공용 템플릿
├─ manage.py
└─ Procfile
```

현재 구조는 Django 모놀리스를 유지하면서도 앱 단위 책임 분리와 `views / use_cases / repositories / domain_services / models` 흐름을 점진적으로 정리하는 방향으로 운영하고 있습니다.

## 로컬 실행

### 1. 가상환경 생성 및 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

루트에 `.env` 파일을 두고 최소한 아래 값을 넣습니다.

```env
DJANGO_SECRET_KEY=your-secret-key
```

프로덕션 설정을 사용할 경우 PostgreSQL 연결 정보도 필요합니다.

```env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=6543
```

### 3. 마이그레이션 및 실행

```bash
python manage.py migrate
python manage.py runserver
```

기본 개발 설정은 `lifeDiary.settings.dev`를 사용합니다.

## 테스트

두 방식 모두 사용 가능합니다.

```bash
pytest
```

```bash
python manage.py test
```

## 배포 메모

- 개발 환경은 SQLite를 사용합니다.
- 프로덕션 환경은 `lifeDiary.settings.prod` 기준 PostgreSQL을 사용합니다.
- `Procfile` 기준 실행 명령은 아래와 같습니다.

```bash
gunicorn lifeDiary.wsgi --workers=2 --threads=4 --worker-class=gthread --bind 0.0.0.0:$PORT
```

## 이 프로젝트를 한 문장으로 설명하면

Life Diary는 생활 기록을 많이 쓰지 않고도 남길 수 있게 하고, 그 기록을 다시 목표와 통계, 피드백으로 돌려주는 구조화된 회고 서비스입니다.
