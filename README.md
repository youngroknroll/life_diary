# Life Diary - 일상생활 정돈 앱

방통대 소프트웨어 경진대회 출품작

배포사이트 : [라이프 다이어리](https://lifediary.onrender.com/)

## 프로젝트 개요

Life Diary는 일상생활을 10분 단위로 기록하고 분석할 수 있는 웹 애플리케이션입니다. 사용자는 시간 블록에 태그를 할당하여 하루를 체계적으로 관리하고, 통계를 통해 자신의 시간 사용 패턴을 파악할 수 있습니다.

##  주요 기능

### 시간 블록 관리
- **10분 단위 기록**: 하루 24시간을 144개의 10분 슬롯으로 분할
- **태그 기반 분류**: 업무, 운동, 식사 등 사용자 정의 태그로 활동 분류
- **메모 기능**: 각 시간 블록에 최대 500자까지 메모 작성 가능
- **직관적 UI**: 시간대별 색상 코딩으로 한눈에 파악 가능

###  태그 시스템
- **개인 태그**: 사용자별 맞춤 태그 생성 및 관리
- **기본 태그**: 모든 사용자가 공유하는 기본 태그 제공
- **색상 커스터마이징**: HEX 색상 코드로 태그별 색상 설정

### 통계 및 분석
- **시간 사용 통계**: 태그별 시간 사용량 분석
- **AI 피드백**: 시간 사용 패턴에 대한 인사이트 제공
- **목표 설정**: 일간/주간/월간 목표 시간 설정 및 추적

### 사용자 관리
- **회원가입/로그인**: Django 기본 인증 시스템
- **개인 메모**: 사용자별 노트 작성 및 관리
- **목표 관리**: 태그별 시간 목표 설정

##  기술 스택

### Backend
- **Django 5.2.4**: 웹 프레임워크
- **Python 3.x**: 프로그래밍 언어
- **SQLite**: 개발용 데이터베이스
- **PostgreSQL**: 프로덕션용 데이터베이스 (psycopg)

### Frontend
- **HTML/CSS/JavaScript**: 기본 웹 기술
- **Django Templates**: 서버사이드 렌더링
- **Bootstrap**: UI 프레임워크 (추정)

### 배포
- **Gunicorn**: WSGI 서버
- **WhiteNoise**: 정적 파일 서빙
- **python-dotenv**: 환경 변수 관리

##  프로젝트 구조

```
lifeDiary/
├── apps/                          # Django 앱들
│   ├── core/                      # 핵심 유틸리티
│   │   ├── static/core/           # 공통 정적 파일
│   │   │   ├── css/style.css      # 공통 스타일
│   │   │   ├── js/tag.js          # 태그 관련 JavaScript
│   │   │   └── js/utils.js        # 유틸리티 함수
│   │   └── utils.py               # 공통 유틸리티 함수
│   ├── dashboard/                 # 메인 대시보드
│   │   ├── models.py              # TimeBlock 모델
│   │   ├── views.py               # 대시보드 뷰
│   │   ├── urls.py                # URL 라우팅
│   │   ├── api_urls.py            # API 엔드포인트
│   │   └── templates/dashboard/   # 대시보드 템플릿
│   ├── stats/                     # 통계 및 분석
│   │   ├── views.py               # 통계 뷰
│   │   ├── logic.py               # 통계 계산 로직
│   │   ├── feedback.py            # AI 피드백 생성
│   │   └── templates/stats/       # 통계 템플릿
│   ├── tags/                      # 태그 관리
│   │   ├── models.py              # Tag 모델
│   │   ├── views.py               # 태그 뷰
│   │   ├── urls.py                # URL 라우팅
│   │   ├── api_urls.py            # API 엔드포인트
│   │   └── templates/tags/        # 태그 템플릿
│   └── users/                     # 사용자 관리
│       ├── models.py              # UserGoal, UserNote 모델
│       ├── views.py               # 사용자 뷰
│       ├── forms.py               # 폼 정의
│       └── templates/users/       # 사용자 템플릿
├── lifeDiary/                     # 프로젝트 설정
│   ├── settings/                  # 설정 파일들
│   │   ├── base.py                # 기본 설정
│   │   ├── dev.py                 # 개발 환경 설정
│   │   └── prod.py                # 프로덕션 환경 설정
│   ├── urls.py                    # 메인 URL 설정
│   └── wsgi.py                    # WSGI 설정
├── templates/                     # 전역 템플릿
│   ├── base.html                  # 기본 템플릿
│   └── index.html                 # 홈페이지
├── staticfiles/                   # 정적 파일들
├── manage.py                      # Django 관리 명령어
└── requirements.txt               # Python 의존성
```

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd knou/lifeDiary
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
# .env 파일 생성
echo "DJANGO_SECRET_KEY=your-secret-key-here" > .env
```

### 5. 데이터베이스 마이그레이션
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. 슈퍼유저 생성 (선택사항)
```bash
python manage.py createsuperuser
```

### 7. 개발 서버 실행
```bash
python manage.py runserver
```

브라우저에서 `http://localhost:8000`으로 접속하여 애플리케이션을 확인할 수 있습니다.

##  사용법

### 1. 회원가입 및 로그인
- `/accounts/signup/`에서 회원가입
- `/accounts/login/`에서 로그인

### 2. 태그 설정
- `/tags/`에서 개인 태그 생성 및 관리
- 태그별 색상 설정으로 시각적 구분

### 3. 시간 기록
- `/dashboard/`에서 메인 대시보드 접속
- 날짜 선택 후 시간 블록 클릭하여 태그 할당
- 메모 작성으로 상세 정보 기록

### 4. 통계 확인
- `/stats/`에서 시간 사용 통계 및 AI 피드백 확인
- 목표 대비 달성률 분석

### 5. 목표 설정
- `/accounts/mypage/`에서 태그별 시간 목표 설정
- 일간/주간/월간 단위로 목표 관리

##  API 엔드포인트

### 시간 블록 API
- `POST /api/timeblock/`: 시간 블록 생성/수정
- `DELETE /api/timeblock/`: 시간 블록 삭제

### 태그 API
- `GET /api/tags/`: 사용자 태그 목록 조회
- `POST /api/tags/`: 새 태그 생성
- `PUT /api/tags/<id>/`: 태그 수정
- `DELETE /api/tags/<id>/`: 태그 삭제

## 핵심 모델

### TimeBlock (시간 블록)
- 사용자별 10분 단위 시간 기록
- 태그와 메모 연결
- 날짜별 고유 제약 조건

### Tag (태그)
- 사용자별 개인 태그 및 공용 기본 태그
- HEX 색상 코드로 시각적 구분
- 이름 중복 방지 제약 조건

### UserGoal (사용자 목표)
- 태그별 시간 목표 설정
- 일간/주간/월간 단위 지원

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 방통대 소프트웨어 경진대회 출품작입니다.

## 👨‍💻 개발자

- 송영록

---
