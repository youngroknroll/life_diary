# Distribution & Monetization Plan

**Date**: 2026-05-06
**Goal**: 데스크톱 앱 빌드 → 공개 배포 → 운영 인프라 → 수익화 실험 → 포트폴리오 정량화
**Strategic Intent**: 단순 "Django 사이트 만들었습니다"를 넘어 **production-grade 운영 경험**을 포트폴리오로 전환

---

## 0. Context & Why

### 문제 정의
현재 LifeDiary는 "개인 프로젝트 = 사이트 구축" 수준이며, 채용 시장에서 차별화가 약하다.

### 차별화 가설
채용 평가는 코드 자체보다 **"실무 문제를 풀어봤는가"** 에 가중치가 높다.

| 평가받는 것 | 평가받지 않는 것 |
|---|---|
| 실제 사용자 (5명이라도) | 기능 개수 |
| 배포 + 운영 경험 | 깔끔한 코드 |
| 모니터링/장애 대응 | 화려한 UI |
| 결제 파이프라인 경험 | 사용 라이브러리 목록 |
| 의사결정 문서화 | 코드 라인 수 |

### 수익화의 진짜 목적
> **돈이 아니라 "Stripe/라이선스/환불 처리 경험"이 목적**이다. 월 ₩10,000을 벌어도 이력서에 쓸 수 있다.

### 본 plan과 기존 plan의 관계
- `2026-05-03_desktop-app-packaging-plan.md` = **빌드까지** 다룸 (§7 Out of Scope에 배포/서명/업데이트 명시 제외)
- 본 plan = **빌드 이후의 배포·운영·수익화** 다룸 (이전 plan의 후속)

---

## 1. Phase Overview

각 Phase는 **독립 승인 게이트**로 분리. 다음 Phase 진입 전 사용자 명시 승인 필요.

| Phase | 목표 | 예상 기간 | 게이트 |
|---|---|---|---|
| **1. 빌드+공개 배포** | `.dmg`/`.exe` GitHub Releases 공개 | 1~2주 | 본인이 다운로드해 동작 확인 |
| **2. 운영 인프라** | Sentry, 다운로드 통계, 피드백 채널 | 1주 | 첫 외부 사용자 1명 확보 |
| **3. 수익화 실험** | Open Core (무료 본체 + 유료 동기화) | 2~3주 | 라이선스 검증 e2e 동작 |
| **4. 포트폴리오 정리** | 정량 지표 + ADR + 이력서 항목화 | 3~5일 | 이력서/README 완성 |

---

## 2. Phase 1 — 빌드 + 공개 배포

### 2.1 Decisions

| # | 항목 | 결정 |
|---|------|------|
| 1A | 저장소 가시성 | **Public 유지** (포트폴리오 가치 우선) |
| 1B | 배포 채널 | **GitHub Releases** (무료, 통계 API 제공) |
| 1C | 빌드 자동화 | **GitHub Actions** (macOS + Windows 러너) |
| 1D | 코드 서명 | **Phase 1에서 생략** (Gatekeeper 우회 안내로 대체) |
| 1E | 버전 관리 | **SemVer** (`v0.1.0`부터 시작) |

### 2.2 Why

- **Public 유지**: 채용 담당자가 PR/커밋 히스토리에서 보안 베이스라인, Light DDD 리팩토링, i18n 등 차별화 포인트 확인 가능. 비공개 시 이 가치 소실.
- **GitHub Releases**: 별도 호스팅 비용 0, 다운로드 카운터 자동, GitHub API로 통계 수집 가능.
- **GitHub Actions**: macOS/Windows 러너 무료 제공 (public repo). PyInstaller 크로스컴파일 불가 문제 해결.
- **서명 생략**: Apple Developer $99/년은 사용자 검증 후 투자. 초기엔 README에 "우클릭 > 열기" 안내로 충분.

### 2.3 Workflow

```
[git tag v0.1.0 push]
   ↓
[GitHub Actions: matrix(macos-latest, windows-latest)]
   ├─ checkout
   ├─ setup-python
   ├─ pip install -r requirements-desktop.txt
   ├─ python manage.py collectstatic --settings=lifeDiary.settings.desktop
   ├─ pyinstaller desktop/lifediary.spec --clean
   ├─ (macOS) create-dmg → LifeDiary-mac-{version}.dmg
   └─ (Windows) zip dist/LifeDiary → LifeDiary-win-{version}.zip
   ↓
[gh release create v0.1.0 LifeDiary-mac.dmg LifeDiary-win.zip]
```

### 2.4 Files

```
.github/workflows/
└── desktop-release.yml          # NEW (matrix 빌드 + Release upload)

README.md                        # UPDATE (다운로드 섹션, 스크린샷, Gatekeeper 안내)
docs/SCREENSHOTS/                # NEW (홍보용 이미지)
```

### 2.5 README 다운로드 섹션 구조

```markdown
## 📥 Download

### macOS (10.15+)
[LifeDiary-mac-v0.1.0.dmg](릴리스 링크)

> 첫 실행 시 "확인되지 않은 개발자" 경고가 뜨면 우클릭 > 열기를 선택하세요.

### Windows (10/11)
[LifeDiary-win-v0.1.0.zip](릴리스 링크)

### 시스템 요구사항
- macOS: 10.15 Catalina 이상
- Windows: WebView2 런타임 (10/11 기본 탑재)
```

### 2.6 Verification

- [ ] `git tag v0.1.0 && git push --tags` → Actions가 양 OS 빌드 성공
- [ ] Releases 페이지에 두 파일 업로드 확인
- [ ] **본인 PC에서 직접 다운로드** → 더블클릭 → 실행
- [ ] 첫 실행 시 사용자 데이터 디렉토리에 DB 생성 확인

### 2.7 Out of Scope (Phase 1)

- 코드 서명 / notarization → Phase 3
- 자동 업데이트 → Phase 3
- 다운로드 통계 시각화 → Phase 2

---

## 3. Phase 2 — 운영 인프라

### 3.1 Decisions

| # | 항목 | 결정 |
|---|------|------|
| 2A | 에러 모니터링 | **Sentry** (무료 5k events/월) |
| 2B | 다운로드 통계 | **GitHub Releases API + 자체 대시보드** |
| 2C | 피드백 채널 | **GitHub Discussions** (별도 인프라 0) |
| 2D | 사용자 분석 | **로컬 telemetry opt-in** (개인정보 최소) |

### 3.2 Why

- **Sentry**: 일기 앱은 사용자가 직접 버그 리포트 안 함. 크래시/예외를 자동 수집해야 개선 가능.
- **GitHub Releases API**: 다운로드 수, OS별 분포 폴링 가능. 별도 분석 인프라 불필요.
- **GitHub Discussions**: 이슈 트래커와 분리된 사용자 대화 공간. 무료.
- **Telemetry opt-in**: GDPR/개인정보 위험 회피. 단, "기능 사용 빈도" 정도는 익명 수집해야 개선 우선순위 결정 가능.

### 3.3 Components

#### 3.3.1 Sentry 연동
- `sentry-sdk[django]` 추가
- `desktop.py`에서 `dsn` 설정 (환경변수 우선, 없으면 빌드 시 주입된 값)
- Django 미들웨어 자동 hook
- pywebview 크래시는 `launcher.py`에서 `try/except` + `sentry_sdk.capture_exception`

#### 3.3.2 다운로드 통계 대시보드
- `scripts/release-stats.py`: GitHub Releases API 폴링 → JSON 캐시
- 출력: `total_downloads`, `os_breakdown`, `version_breakdown`
- 주간 cron으로 README badge 자동 업데이트

#### 3.3.3 피드백 채널
- GitHub Discussions 카테고리: `💡 Ideas`, `🐛 Bug Reports`, `❓ Q&A`, `🙌 Show & Tell`
- README에 링크
- 첫 외부 사용자 확보를 위한 홍보 채널: 개인 SNS, 디스코드 커뮤니티, Show HN 후보

#### 3.3.4 Opt-in Telemetry
- 첫 실행 시 다이얼로그: "익명 사용 통계 수집에 동의하시겠습니까?"
- 동의 시: 사용 기능 카운트만 수집 (일기 글자 수, 사진 업로드 여부 X)
- 자체 백엔드 vs Plausible/PostHog → **PostHog Cloud 무료 플랜** (1M events/월) 권장

### 3.4 Files

```
requirements-desktop.txt         # UPDATE (sentry-sdk 추가)
lifeDiary/settings/desktop.py    # UPDATE (Sentry init)
desktop/launcher.py              # UPDATE (Sentry init, telemetry consent)
desktop/telemetry.py             # NEW (PostHog 클라이언트, opt-in 로직)
scripts/release-stats.py         # NEW (GitHub API → README badge)
.github/discussions-categories.md # NEW (가이드)
```

### 3.5 Verification

- [ ] 의도적으로 예외 발생 → Sentry 대시보드에 표시
- [ ] `scripts/release-stats.py` 실행 → 다운로드 수 출력
- [ ] Discussions에 첫 외부 사용자 등록 (가족/친구/동료라도)
- [ ] Telemetry opt-out 사용자는 PostHog로 데이터 안 감 (Red-Green 검증)

---

## 4. Phase 3 — 수익화 실험 (Open Core)

### 4.1 Decisions

| # | 항목 | 결정 |
|---|------|------|
| 3A | 수익 모델 | **Open Core**: 무료 본체 + 유료 동기화 |
| 3B | 유료 기능 | **클라우드 동기화** (다기기), **자동 백업** |
| 3C | 가격 | **₩3,000/월** 또는 **₩30,000/년** (Day One 1/10 수준) |
| 3D | 결제 처리 | **Lemon Squeezy** (Merchant of Record, VAT 자동) |
| 3E | 라이선스 검증 | **백엔드 API + 로컬 토큰 캐시** (오프라인 7일 허용) |
| 3F | 백엔드 호스팅 | **Railway** 또는 **Fly.io** 무료 티어 |
| 3G | 동기화 스토리지 | **사용자 자체 (S3 호환 키)** vs **자체 호스팅** → 결정 보류 |

### 4.2 Why

- **Open Core**: 본체 오픈소스 유지 = 포트폴리오 가치 보존. 유료 기능은 분리된 부가 가치.
- **클라우드 동기화 선택 이유**: 일기 앱 특성상 다기기 사용 니즈 명확. 백엔드 인프라 경험 증명.
- **Lemon Squeezy**: Stripe 직접 연동 시 한국 사업자등록 + VAT 신고 필요. LS는 MoR로 이 부담 0.
- **로컬 토큰 캐시**: 매 실행마다 서버 검증 시 오프라인 사용 불가. 7일 허용은 산업 표준.
- **백엔드 따로**: 데스크톱 앱은 로컬 SQLite, 동기화는 별도 서비스. **Django + DRF**로 구축 → 기존 스킬 재사용 + 백엔드 경험 증명.

### 4.3 Architecture

```
[Desktop App (Free)]
      │
      │ (Pro 유저만)
      ↓
[License Token]  ──검증──→  [Backend API (Django/DRF)]
      │                              │
      │                              ├─ Lemon Squeezy webhook 수신
      │                              ├─ License 발급/검증
      │                              └─ 동기화 데이터 저장
      ↓
[Sync Service]
      │
      ↓
[Encrypted Storage (S3 호환)]
```

### 4.4 Components

#### 4.4.1 Backend (`lifediary-cloud` 새 repo)
- Django + DRF
- 모델: `User`, `License`, `SyncDocument` (encrypted blob)
- 엔드포인트:
  - `POST /api/license/validate` (라이선스 키 검증)
  - `POST /api/sync/push` (암호화된 일기 데이터 업로드)
  - `GET /api/sync/pull` (다운로드)
  - `POST /api/webhooks/lemonsqueezy` (결제/취소/환불)

#### 4.4.2 Lemon Squeezy 연동
- 상품 등록: "LifeDiary Pro - Monthly" / "LifeDiary Pro - Yearly"
- Webhook URL → 백엔드 → DB에 라이선스 발급
- 사용자 이메일로 라이선스 키 자동 발송

#### 4.4.3 데스크톱 앱 변경
- `desktop/license.py`: 라이선스 입력/검증/캐시
- `desktop/sync.py`: 백엔드 push/pull (E2E 암호화)
- 설정 UI: "Pro 업그레이드" 버튼 → Lemon Squeezy 결제 페이지로 이동
- 무료 사용자: 동기화 메뉴 회색 처리 + Pro 업그레이드 안내

#### 4.4.4 E2E 암호화
- 사용자 비밀번호 기반 키 derivation (PBKDF2)
- 일기 데이터는 클라이언트에서 암호화 후 업로드
- **백엔드는 평문 못 봄** = 신뢰 모델 = 마케팅 포인트

### 4.5 Files

```
lifediary-cloud/                 # NEW REPO (private)
├── apps/license/
├── apps/sync/
├── apps/webhooks/
└── ...

(this repo)
desktop/license.py               # NEW
desktop/sync.py                  # NEW
desktop/crypto.py                # NEW (E2E 암호화)
```

### 4.6 Pricing Page

```markdown
## LifeDiary Free
- 무제한 일기 작성 (로컬 저장)
- 모든 기본 기능
- ₩0

## LifeDiary Pro
- Free의 모든 기능 +
- ☁️ 클라우드 동기화 (E2E 암호화)
- 📱 다기기 사용 (3대까지)
- 💾 자동 백업
- ₩3,000/월 또는 ₩30,000/년 (2개월 절약)
```

### 4.7 Verification (Red-Green)

- [ ] **Green**: Pro 사용자가 기기 A에서 작성 → 기기 B에서 동기화 확인
- [ ] **Red**: 라이선스 만료/취소 시 동기화 차단 확인
- [ ] **Red**: 무료 사용자가 sync API 직접 호출 → 401 응답
- [ ] **Red**: 백엔드 DB에서 일기 내용 평문 조회 불가 (E2E 검증)
- [ ] Lemon Squeezy 테스트 환불 → webhook → 라이선스 무효화

### 4.8 Risks

| 리스크 | 대응 |
|---|---|
| 결제 0건 가능성 | 목표는 수익 X, **결제 파이프라인 경험**이 목적. 본인 카드로 자가 구매도 검증 가치 있음 |
| 백엔드 인프라 비용 | Railway/Fly.io 무료 티어 + Lemon Squeezy 호스팅 페이지 활용 |
| 한국 사업자등록 | 부업 소득 ₩6.6M/년 미만은 신고만. LS가 글로벌 결제이므로 해외 소득 처리 |
| E2E 암호화 키 분실 | 사용자에게 "복구 불가" 명시, 키 파일 다운로드 백업 권장 |

---

## 5. Phase 4 — 포트폴리오 정량화

### 5.1 산출물

#### 5.1.1 README 강화
- 다운로드 수 (자동 업데이트 badge)
- 스크린샷 + 데모 GIF
- 아키텍처 다이어그램 (데스크톱 앱 + 백엔드)
- 기술 스택 요약

#### 5.1.2 Architecture Decision Records
`docs/adr/` 디렉토리에 주요 의사결정 문서화:
- `0001-light-ddd-adoption.md` (이미 있음)
- `0002-desktop-packaging-strategy.md`
- `0003-open-core-monetization.md`
- `0004-e2e-encryption-design.md`

#### 5.1.3 Postmortem / Incident Reports
`docs/postmortems/`:
- Sentry로 잡은 실제 버그 → 원인 분석 → 수정 → 재발 방지
- 1~2건이라도 작성하면 채용 시 강력한 자료

#### 5.1.4 이력서 항목 (예시)
```
• LifeDiary - 데스크톱 일기 앱 (Django + PyInstaller)
  - GitHub Public, 누적 다운로드 N건
  - PyInstaller 데스크톱 패키징, GitHub Actions 멀티 OS 빌드
  - Sentry 기반 모니터링, 실제 크래시 N건 수정
  - Open Core 수익화 (Lemon Squeezy + Django/DRF 백엔드)
  - E2E 암호화 클라우드 동기화 설계 및 구현
  - 유료 사용자 N명 (₩X 수익)
```

### 5.2 Verification

- [ ] README가 외부인이 처음 봤을 때 5분 안에 프로젝트 가치 파악 가능
- [ ] ADR 4건 이상 작성
- [ ] Postmortem 1건 이상
- [ ] 이력서에 정량 지표 (다운로드 N, 사용자 N, 수익 ₩X) 기재

---

## 6. Implementation Order

각 Phase 완료 후 **명시적 사용자 승인** → 다음 Phase 진입.

```
[Phase 0: prerequisite]
  └─ desktop-app-packaging-plan §6 1~6 완료 (빌드 동작)
        ↓
[Phase 1: 공개 배포]
  ├─ 1.1 GitHub Actions workflow 작성
  ├─ 1.2 README 다운로드 섹션 추가
  ├─ 1.3 v0.1.0 태그 → 첫 Release
  └─ 1.4 본인 PC 다운로드 검증
        ↓ [승인 게이트 1]
[Phase 2: 운영]
  ├─ 2.1 Sentry 연동
  ├─ 2.2 release-stats 스크립트
  ├─ 2.3 GitHub Discussions 활성화
  ├─ 2.4 Telemetry opt-in
  └─ 2.5 첫 외부 사용자 1명 확보
        ↓ [승인 게이트 2]
[Phase 3: 수익화]
  ├─ 3.1 lifediary-cloud 백엔드 신규 repo
  ├─ 3.2 Lemon Squeezy 상품 등록 + webhook
  ├─ 3.3 라이선스 검증 모듈
  ├─ 3.4 E2E 암호화 동기화
  ├─ 3.5 Pro 업그레이드 UI
  └─ 3.6 본인 카드 자가 구매 e2e 검증
        ↓ [승인 게이트 3]
[Phase 4: 정량화]
  ├─ 4.1 README 강화
  ├─ 4.2 ADR 작성
  ├─ 4.3 Postmortem
  └─ 4.4 이력서 항목화
```

---

## 7. Out of Scope

- App Store / Microsoft Store 출시 (심사 + 수수료 부담)
- 모바일 앱 (iOS/Android)
- 팀 협업 기능 (단일 사용자 일기 앱 컨셉 유지)
- AI 기능 (요약, 감정 분석) — 별도 plan 후보
- 한국 사업자등록 (Lemon Squeezy MoR로 우회)

---

## 8. Strategic Risks

| 리스크 | 영향 | 대응 |
|---|---|---|
| Phase 3에서 사용자 0명 → 수익 검증 불가 | 高 | 본인 카드 자가 구매로 결제 파이프라인 e2e 증명. 수익 X여도 "결제 시스템 구축 경험"은 남음 |
| 시간 투자 대비 채용 ROI 불확실 | 中 | 각 Phase가 독립 가치. Phase 1~2만 완료해도 "배포 + 운영" 경험 확보 |
| Open Core가 부담스러우면 무료만 가능 | 低 | Phase 3 스킵 → Phase 4 직행 가능 (정량 지표는 다운로드 수만 사용) |
| 백엔드 인프라 운영 비용 | 低 | 무료 티어로 출발, 사용자 증가 시 검토 |

---

## 9. Approval Required

- [ ] **Plan 전체 방향 승인** (포트폴리오 → 수익화 → 정량화 전략)
- [ ] **Phase 1 진입 승인** (GitHub Actions + Releases 공개 배포)
- [ ] (Phase 1 완료 후) **Phase 2 진입 승인**
- [ ] (Phase 2 완료 후) **Phase 3 진입 승인**
- [ ] (Phase 3 완료 후) **Phase 4 진입 승인**

---

## 10. Linked Plans

- `2026-05-03_desktop-app-packaging-plan.md` — 본 plan의 prerequisite (빌드)
- `2026-04-21_architecture-and-cost-plan.md` — 백엔드 인프라 결정 시 참조
- `2026-05-01_account-recovery-plan.md` — Phase 3 라이선스 시스템과 연관 (계정 복구 ↔ 라이선스 복구 패턴 공유)
