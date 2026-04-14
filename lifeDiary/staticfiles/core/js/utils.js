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
 * API 호출을 위한 공통 fetch 래퍼
 * @param {string} url - API 엔드포인트 URL
 * @param {object} options - fetch 옵션
 * @param {object} options.method - HTTP 메서드
 * @param {object} options.data - 전송할 데이터
 * @param {object} options.headers - 추가 헤더
 * @returns {Promise<object>} - API 응답 결과
 */
async function apiCall(url, options = {}) {
    const {
        method = 'GET',
        data = null,
        headers = {},
        showLoading = true,
        loadingElement = null
    } = options;

    // 기본 헤더 설정
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        ...headers
    };

    // 로딩 상태 처리
    let originalContent = null;
    if (showLoading && loadingElement) {
        originalContent = loadingElement.innerHTML;
        loadingElement.disabled = true;
        loadingElement.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>처리 중...';
    }

    try {
        const fetchOptions = {
            method,
            headers: defaultHeaders,
        };

        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE')) {
            fetchOptions.body = JSON.stringify(data);
        }

        const response = await fetch(url, fetchOptions);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || `HTTP ${response.status}`);
        }

        return result;

    } catch (error) {
        throw error;
    } finally {
        // 로딩 상태 해제
        if (showLoading && loadingElement && originalContent !== null) {
            loadingElement.disabled = false;
            loadingElement.innerHTML = originalContent;
        }
    }
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