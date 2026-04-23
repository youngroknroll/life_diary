/**
 * =================================================================================
 * 공통 유틸리티 JavaScript
 * - 여러 페이지에서 공통으로 사용되는 헬퍼 함수들을 포함합니다.
 * =================================================================================
 */

/**
 * Django의 CSRF 토큰을 쿠키에서 가져오는 함수.
 * @param {string} name - 가져올 쿠키의 이름 (기본값: 'csrftoken').
 * @returns {string|null} - CSRF 토큰 값 또는 null.
 */
function getCookie(name = 'csrftoken') {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * 전역 알림 시스템
 * @param {string} message - 표시할 메시지
 * @param {string} type - 알림 타입 ('success', 'warning', 'error', 'info')
 * @param {number} duration - 자동 제거 시간 (밀리초, 기본 3000)
 */
function showNotification(message, type = 'info', duration = 3000) {
    // 기존 알림 제거
    const existingNotification = document.querySelector('.core-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show core-notification`;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // 자동 제거
    setTimeout(() => {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

/**
 * 전역 로딩 오버레이를 커스텀 메시지로 표시.
 * base.html의 #loadingOverlay DOM을 재사용한다.
 * @param {string} message - 표시할 안내 문구
 * @param {string} [icon='fa-clock'] - Font Awesome 아이콘 클래스
 */
function showOverlay(message, icon = 'fa-clock') {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) return;
    if (message) {
        const text = overlay.querySelector('.loading-text');
        if (text) {
            // 아이콘은 innerHTML, message는 textNode로 분리해 XSS 소지 제거
            text.innerHTML = `<i class="fas ${icon} me-2"></i>`;
            text.appendChild(document.createTextNode(message));
        }
    }
    overlay.classList.add('is-visible');
    overlay.setAttribute('aria-hidden', 'false');
}

/**
 * 전역 로딩 오버레이를 숨김.
 */
function hideOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) return;
    overlay.classList.remove('is-visible');
    overlay.setAttribute('aria-hidden', 'true');
}

/**
 * 삭제 확인 다이얼로그 공통 헬퍼.
 * 향후 네이티브 confirm을 커스텀 모달로 교체할 때 단일 진입점이 된다.
 * @param {string} message - 커스텀 확인 메시지 (기본: '정말 삭제하시겠습니까?')
 * @returns {boolean} - 사용자 확인 여부
 */
function confirmDelete(message = '정말 삭제하시겠습니까?') {
    return confirm(message);
}

/**
 * 버튼을 로딩 상태로 전환하고 원래 내용을 반환하는 헬퍼.
 * @param {HTMLElement} btn - 대상 버튼 엘리먼트
 * @param {string} text - 로딩 중 표시 텍스트 (기본: '처리 중...')
 * @returns {string} - 복구용 원래 innerHTML
 */
function setButtonLoading(btn, text = '처리 중...') {
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>${text}`;
    return original;
}

/**
 * 버튼을 로딩 상태에서 원래 상태로 복구하는 헬퍼.
 * @param {HTMLElement} btn - 대상 버튼 엘리먼트
 * @param {string} originalHTML - setButtonLoading이 반환한 원래 innerHTML
 */
function resetButtonLoading(btn, originalHTML) {
    btn.disabled = false;
    btn.innerHTML = originalHTML;
}

/**
 * API 호출을 위한 공통 fetch 래퍼.
 *
 * @param {string} url - API 엔드포인트 URL
 * @param {object} options
 * @param {string} [options.method='GET'] - HTTP 메서드
 * @param {object} [options.data] - JSON 직렬화해서 보낼 데이터
 * @param {*} [options.body] - 원본 body (FormData 등). 지정 시 data는 무시되고 Content-Type도 자동 지정 안 함
 * @param {object} [options.headers] - 추가 헤더
 * @param {boolean} [options.showLoading=true] - 버튼 로딩 표시 여부
 * @param {HTMLElement} [options.loadingElement] - 로딩 버튼 엘리먼트
 * @param {'json'|'text'|'none'} [options.responseType='json'] - 응답 파싱 방식
 *        - 'json' (기본): `.json()`
 *        - 'text': `.text()` (HTML partial 등)
 *        - 'none': 본문 파싱 없이 {ok, status} 반환. 204에는 자동 적용됨.
 * @returns {Promise<*>} - 응답 결과
 * @throws {Error} - 실패 시 err.status(HTTP), err.data(파싱된 응답) 부착
 */
async function apiCall(url, options = {}) {
    const {
        method = 'GET',
        data = null,
        body = null,
        headers = {},
        showLoading = true,
        loadingElement = null,
        responseType = 'json',
    } = options;

    const defaultHeaders = {
        'X-CSRFToken': getCookie('csrftoken'),
        ...headers,
    };
    // JSON 직렬화 모드에서만 Content-Type 자동 지정 (FormData면 브라우저가 boundary 포함해 설정)
    if (body === null && data !== null) {
        defaultHeaders['Content-Type'] = 'application/json';
    }

    let originalContent = null;
    if (showLoading && loadingElement) {
        originalContent = setButtonLoading(loadingElement);
    }

    try {
        const fetchOptions = {
            method,
            headers: defaultHeaders,
            credentials: 'same-origin',
        };

        if (body !== null) {
            fetchOptions.body = body;
        } else if (data !== null && method !== 'GET' && method !== 'HEAD') {
            fetchOptions.body = JSON.stringify(data);
        }

        const response = await fetch(url, fetchOptions);

        // 본문 없는 응답 (204 또는 none)
        if (response.status === 204 || responseType === 'none') {
            if (!response.ok) {
                const err = new Error(`HTTP ${response.status}`);
                err.status = response.status;
                throw err;
            }
            // responseType별 중립 값 반환 (text는 '', json은 null, none은 상태 객체)
            if (responseType === 'text') return '';
            if (responseType === 'json') return null;
            return { ok: true, status: response.status };
        }

        const result = responseType === 'text'
            ? await response.text()
            : await response.json();

        if (!response.ok) {
            const message = (responseType === 'json' && result && result.message) || `HTTP ${response.status}`;
            const err = new Error(message);
            err.status = response.status;
            err.data = result;
            throw err;
        }

        return result;

    } finally {
        if (showLoading && loadingElement && originalContent !== null) {
            resetButtonLoading(loadingElement, originalContent);
        }
    }
}

/**
 * 배경색의 밝기를 기반으로 대비되는 텍스트 색상을 반환하는 함수.
 * W3C 상대 휘도 공식을 사용합니다.
 * @param {string} hexColor - '#RRGGBB' 형식의 HEX 색상
 * @returns {string} - 밝은 배경이면 '#212529'(어두운 글씨), 어두운 배경이면 '#ffffff'(흰 글씨)
 */
function getContrastTextColor(hexColor) {
    const hex = hexColor.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    // YIQ 공식: 밝기 임계값 128
    const yiq = (r * 299 + g * 587 + b * 114) / 1000;
    return yiq >= 128 ? '#212529' : '#ffffff';
}

/**
 * 오늘 날짜로 이동하는 공통 함수
 * date 파라미터를 제거하여 서버가 오늘 날짜로 처리하도록 함
 */
function goToToday() {
    const url = new URL(window.location);
    url.searchParams.delete('date');
    window.location.href = url.toString();
} 