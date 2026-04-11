# Frontend CSS 리팩토링 기록

**날짜:** 2026-04-11
**범위:** 디자인 토큰 통합 · 중복 inline CSS 제거 · 로딩 오버레이 재작성 · Bootstrap primary 오버라이드

---

## 배경

프로젝트의 CSS가 여러 위치에 분산되어 있었고 하드코딩된 색상·크기 값이 반복되고 있었다.

- `apps/core/static/core/css/style.css`는 Bootstrap 기본 파란색(`#0d6efd`) 팔레트를 사용
- `templates/index.html`은 `<style>` 태그로 녹색 브랜드 팔레트(`#2f7d4f` 등)를 inline 정의
- `login.html`과 `signup.html`의 `<style>` 블록이 거의 100% 동일
- `base.html`에 로딩 모달 관련 CSS 27줄이 inline
- `#6c757d`, `border-radius: 10px`, `padding: 12px 15px` 등이 여러 템플릿에 반복

사용자 요구: **index.html의 녹색 팔레트를 사이트 전체 기본 테마로 승격하고 흩어진 CSS를 한 곳으로 모으기.**

---

## 디자인 토큰

`apps/core/static/core/css/style.css`의 `:root`에 디자인 토큰을 정의하여 단일 출처(single source of truth)로 삼는다.

### Brand Palette

```css
--color-primary:        #2f7d4f;  /* 기본 녹색 */
--color-primary-hover:  #25663f;  /* hover 시 진한 녹색 */
--color-primary-soft:   #e8f4ec;  /* 아이콘 배경 */
--color-primary-border: #98c7aa;  /* secondary 버튼 테두리 */
```

### Text & Surface

```css
--color-text:         #16231b;
--color-text-muted:   #4c5b52;
--color-surface:      #ffffff;
--color-surface-soft: #f3f8f5;
--color-border:       #d8e3d8;
--color-border-soft:  #dfe7df;
--color-border-muted: #e1e8e1;
```

### Accent (하루 기록 블록 예시)

```css
--color-accent-work:   #4f9f68;  /* 일 */
--color-accent-rest:   #f0c24b;  /* 휴식 */
--color-accent-move:   #6cb6c9;  /* 이동 */
--color-accent-care:   #e48f73;  /* 돌봄 */
--color-accent-muted:  #dbe8df;  /* 비어있는 블록 */
```

### Note 박스 (노란 강조)

```css
--color-note-bg:     #fff7df;
--color-note-border: #efd98c;
--color-note-text:   #5d4a15;
```

### Radius · Typography

```css
--radius-sm: 6px;
--radius-md: 8px;
--radius-lg: 15px;
--font-body: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
```

### Bootstrap 호환 alias

기존 코드가 `--primary-color` 같은 예전 변수명을 참조하므로 이관 충격 완화를 위해 alias를 둔다.

```css
--primary-color: var(--color-primary);
--success-color: #198754;
--warning-color: #ffc107;
--danger-color:  #dc3545;
--info-color:    #0dcaf0;
--light-color:   var(--color-surface-soft);
--dark-color:    var(--color-text);

/* Bootstrap 5 CSS 변수 오버라이드 (text-primary 등 자동 적용) */
--bs-primary:     #2f7d4f;
--bs-primary-rgb: 47, 125, 79;
```

---

## 공통 컴포넌트 클래스

### `.auth-card` — login/signup 통합

login.html과 signup.html의 30줄 이상 inline `<style>`이 거의 동일했다. `.auth-card` 공통 클래스로 묶어 두 파일의 `<style>` 블록을 완전히 제거했다.

```css
.auth-card {
    margin-top: 3rem;
    border: none;
    border-radius: var(--radius-lg);
}

.auth-card .card-header {
    border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
}

.auth-card .form-control {
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border);
    padding: 12px 15px;
}

.auth-card .form-control:focus {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 0.2rem rgba(47, 125, 79, 0.2);
}

.auth-card .btn-primary {
    border-radius: var(--radius-md);
    padding: 12px;
    font-weight: bold;
}
```

템플릿 사용:

```html
<div class="card auth-card shadow">
    <!-- ... -->
</div>
```

### `.btn-outline-primary` 강제 오버라이드

Bootstrap 5.3의 `.btn-outline-primary`는 scoped 변수(`--bs-btn-color: #0d6efd;`)에 **하드코딩된 hex 값**을 사용한다. `--bs-primary`를 `:root`에서 오버라이드해도 outline 버튼에는 적용되지 않는다.

해결: `.btn-outline-primary`에 `color`·`background-color`·`border-color`를 직접 `!important`로 지정.

```css
.btn.btn-outline-primary,
.btn-outline-primary {
    color: #2f7d4f !important;
    border-color: #2f7d4f !important;
    background-color: transparent !important;
}

.btn.btn-outline-primary:hover,
.btn.btn-outline-primary:focus,
.btn.btn-outline-primary:active,
.btn-outline-primary:hover,
.btn-outline-primary:focus,
.btn-outline-primary:active {
    color: #ffffff !important;
    background-color: #2f7d4f !important;
    border-color: #2f7d4f !important;
}
```

> **왜 `!important`가 필요한가?** 일반적으로 `!important`는 피해야 하지만, 여기선 써드파티 라이브러리(Bootstrap)의 기본값을 브랜드 색으로 덮어쓰기 위한 의도적 선택이다. 변수 체인(`--bs-btn-color: var(--color-primary)`)은 특정성 문제와 변수 해석 타이밍 문제로 실패 사례가 있었다.

---

## 로딩 오버레이 재작성 (핵심 변경)

### 문제

dashboard와 stats 페이지에서 **휠 스크롤이 고정**되는 버그 발생.

### 원인

이전 구현은 Bootstrap Modal을 로딩 표시용으로 사용했다.

```js
// Before: Bootstrap Modal 기반
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
loadingModal.show();   // body에 modal-open 추가 → overflow: hidden
// ...
window.addEventListener('load', () => loadingModal.hide());
```

Bootstrap Modal은 열릴 때 `<body>`에 `modal-open` 클래스를 붙여 `overflow: hidden`을 강제한다. dashboard/stats는 Chart.js 초기화로 인해 `window.load` 타이밍이 복잡해서, Bootstrap의 **fade-in 트랜지션이 끝나기 전에 `hide()`가 호출되는 race condition**이 발생. 이 경우 Bootstrap이 `modal-open` 클래스를 body에서 제거하지 못해 스크롤이 영구적으로 잠긴다.

### 해결

Bootstrap Modal을 완전히 버리고 **순수 `<div>` 오버레이**로 재작성. body를 건드리지 않으므로 스크롤 락이 발생할 여지 자체가 없다.

**HTML (`base.html`):**

```html
<div id="loadingOverlay" class="loading-overlay" aria-hidden="true">
    <div class="loading-overlay-content">
        <div class="loading-spinner mx-auto"></div>
        <div class="loading-text mt-3">
            <i class="fas fa-clock me-2"></i>
            페이지를 불러오는 중입니다...
        </div>
    </div>
</div>
```

**CSS (`style.css`):**

```css
.loading-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(5px);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 2000;
}

.loading-overlay.is-visible {
    display: flex;
}

.loading-overlay-content {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 2.5rem 3rem;
    text-align: center;
    box-shadow: 0 16px 34px rgba(43, 73, 53, 0.2);
}
```

**JavaScript (`base.html`):**

```js
const loadingOverlay = document.getElementById('loadingOverlay');
let isNavigating = false;

function showLoadingOverlay() {
    if (loadingOverlay) loadingOverlay.classList.add('is-visible');
}

function hideLoadingOverlay() {
    if (loadingOverlay) loadingOverlay.classList.remove('is-visible');
    isNavigating = false;
}

// 홈 제외 페이지는 로드 중 오버레이 표시
const isHomePage = window.location.pathname === '/' || window.location.pathname === '';
if (!isHomePage) showLoadingOverlay();

// 모든 리소스 로드 완료 시 숨김
window.addEventListener('load', hideLoadingOverlay);

// bfcache(뒤로/앞으로) 복원 시 숨김
window.addEventListener('pageshow', e => {
    if (e.persisted) hideLoadingOverlay();
});

// 페이지 이동 링크 클릭 시 오버레이 표시
document.addEventListener('click', e => {
    const link = e.target.closest('a');
    if (link && link.href && !link.href.startsWith('javascript:') && !link.href.startsWith('#') && !link.target && !isNavigating) {
        if (!link.href.includes('admin') && !link.href.includes('logout') && !link.href.endsWith('#')) {
            isNavigating = true;
            showLoadingOverlay();
        }
    }
});

// Dropdown 토글은 페이지 이동이 아니므로 오버레이 숨김
document.addEventListener('click', e => {
    if (e.target.matches('[data-bs-toggle="dropdown"]') || e.target.closest('[data-bs-toggle="dropdown"]')) {
        hideLoadingOverlay();
    }
});
```

### 이전 버그들

현재 구현에 도달하기까지 두 번 수정했다.

1. **`checkIfStillLoading()` 제거 (이전 커밋)** — CDN cross-origin CSS의 `cssRules` 접근 시 CORS 오류가 원인이 되어, `window.load` 이후에도 오버레이가 사라지지 않는 문제. 이 함수는 `window.load`가 이미 보장하는 체크를 중복 수행하다가 오작동했다.
2. **`pageshow` 이벤트 추가 (이전 커밋)** — 뒤로가기 시 bfcache에서 복원된 페이지는 `window.load`가 재실행되지 않아 오버레이가 유지되는 문제. `e.persisted === true`일 때 강제 숨김 처리.

---

## 파일별 변경 요약

| 파일 | 변경 |
|---|---|
| `apps/core/static/core/css/style.css` | 94줄 → 200+ 줄. 디자인 토큰, `.auth-card`, `.btn-outline-primary` 오버라이드, `.loading-overlay` 추가 |
| `templates/base.html` | 로딩 모달 inline `<style>` 제거, Bootstrap Modal → `loading-overlay` div로 교체, JS를 plain show/hide로 재작성 |
| `templates/index.html` | 하드코딩 hex 값 약 30개를 `var(--color-*)`로 치환 |
| `apps/users/templates/users/login.html` | inline `<style>` 30줄 삭제, `.auth-card` 클래스 적용 |
| `apps/users/templates/users/signup.html` | 동일 |
| `apps/users/templates/users/mypage.html` | 불필요한 form-control 오버라이드 제거 (Bootstrap 기본값 사용) |
| `apps/users/templates/users/usergoal_form.html` | 동일 |
| `apps/dashboard/templates/dashboard/index.html` | "목표 추가" 버튼: `btn-outline-secondary text-danger` → `btn-outline-primary fw-bold` |
| `apps/stats/templates/stats/index.html` | "목표 확인" 버튼: 동일 |
| `apps/tags/templates/tags/_tag_modal.html` | 기본 태그 색상 `#007bff` → `#2f7d4f` |

---

## 운영 주의사항 (중요)

### 1. WhiteNoise + ManifestStaticFilesStorage

`lifeDiary/settings/dev.py`에 다음 설정이 있다:

```python
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

이 설정은 **DEBUG 모드에서도** `STATIC_ROOT`(`staticfiles/`)의 수집된 파일을 서빙한다. 따라서 **소스 CSS/JS를 수정한 뒤 반드시 `collectstatic`을 실행해야** 변경사항이 반영된다.

```bash
uv run python manage.py collectstatic --noinput
```

이 작업을 누락해서 "CSS가 적용되지 않는" 버그를 한 번 겪었다. 증상은:

- `var(--color-primary)` 등 토큰이 존재하지 않아 텍스트가 브라우저 기본 검정으로 표시
- 패널 배경·테두리가 빈 값으로 해석되어 사라진 것처럼 보임

### 2. 브라우저 캐시

`staticfiles/`의 파일 경로가 변경되지 않으므로 브라우저는 공격적으로 캐싱한다. CSS 변경 후에는 **⌘+Shift+R (하드 리프레시)** 로 확인하거나 개발자 도구의 "Disable cache" 옵션을 사용한다.

### 3. CSS 변수 오버라이드 시 Bootstrap 동작 이해

Bootstrap 5.3의 버튼 클래스는 scoped 변수를 사용하는데, 이 변수들의 기본값은 **`var(--bs-primary)` 참조가 아니라 하드코딩된 hex**이다.

```css
/* Bootstrap 원본 */
.btn-outline-primary {
    --bs-btn-color: #0d6efd;  /* 하드코딩 */
    /* ... */
}
```

따라서 `:root`에서 `--bs-primary`만 덮어쓰면 **유틸리티 클래스(`text-primary` 등)만 반영되고 버튼은 파란색으로 남는다.** 버튼별 scoped 변수를 직접 덮어쓰거나, 아니면 `color`/`background-color`를 `!important`로 직접 지정해야 한다.

### 4. Bootstrap Modal을 로딩 인디케이터로 쓰지 말 것

Bootstrap Modal은 열릴 때 body에 `modal-open` 클래스를 추가하여 스크롤을 잠근다. 사용자가 닫는 일반 모달에는 문제가 없지만, **자동으로 열고 닫는 로딩 인디케이터**로 쓰면 fade 트랜지션과 `hide()` 호출이 경합해 body 스크롤이 영구적으로 잠길 수 있다. 로딩·토스트·간단한 오버레이는 plain div로 구현하는 것이 안전하다.

---

## 검증

- Django `manage.py check` → 0 issues
- 기존 비즈니스 로직 테스트 12개 전부 통과
- 홈/대시보드/통계/마이페이지/태그 5개 페이지 모두 200 OK
- 홈의 `var(--color-primary)` 참조 6회 확인
- login에 `.auth-card` 클래스 적용 확인
- dashboard의 144개 `time-slot` 렌더링 확인
- `Traceback`/`TemplateSyntaxError` 0건
