/**
 * =================================================================================
 * 대시보드 JavaScript
 * - 타임블록 슬롯 선택, 드래그, 저장/삭제 등 대시보드 인터랙션 로직
 * - core/utils.js의 apiCall, showNotification, getContrastTextColor 사용
 * - core/tag.js의 openTagFormModal 사용
 * =================================================================================
 */

// ── 유틸리티 ──

function slotIndexToTime(slotIndex) {
    const totalMinutes = slotIndex * 10;
    const hour = Math.floor(totalMinutes / 60);
    const minute = totalMinutes % 60;
    return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
}

// ── 상태 변수 ──

let selectedSlots = new Set();
let selectedTag = null;
let isDragging = false;
let startSlot = null;
let isAdditiveDrag = false;
let dragBaseSelection = new Set();

const SLOTS_PER_HOUR = 6;
const TOTAL_SLOTS = 144;

function isMobileDashboardLayout() {
    return window.matchMedia('(max-width: 767.98px)').matches;
}

function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function slotToRowCol(slotIndex) {
    return {
        row: Math.floor(slotIndex / SLOTS_PER_HOUR),
        col: slotIndex % SLOTS_PER_HOUR,
    };
}

function rowColToSlot(row, col) {
    return row * SLOTS_PER_HOUR + col;
}

function blockForSlot(slotIndex) {
    const hour = Math.floor(slotIndex / SLOTS_PER_HOUR);
    const row = document.querySelector(`.day-row[data-hour="${hour}"]`);
    if (!row) return null;

    return Array.from(row.querySelectorAll('.slot-block')).find(block => {
        const start = parseInt(block.dataset.start, 10);
        const span = parseInt(block.dataset.span, 10);
        return slotIndex >= start && slotIndex < start + span;
    }) || null;
}

function isSlotFilled(slotIndex) {
    const block = blockForSlot(slotIndex);
    return !!(block && block.dataset.tagId);
}

function slotTagInfo(slotIndex) {
    const block = blockForSlot(slotIndex);
    if (!block || !block.dataset.tagId) return null;

    const [tagName, memo = ''] = (block.getAttribute('title') || '').split(' · ');
    return { tagName, memo };
}

/** 블록 하나가 여러 칸을 덮으므로 요소가 아니라 x 위치로 칸을 정한다. */
function slotFromPoint(clientX, clientY) {
    const element = document.elementFromPoint(clientX, clientY);
    const row = element && element.closest('.day-row[data-hour]');
    if (!row) return null;

    const cells = row.querySelector('.day-row__cells');
    if (!cells) return null;

    const rect = cells.getBoundingClientRect();
    if (rect.width <= 0) return null;

    const ratio = (clientX - rect.left) / rect.width;
    const col = Math.min(SLOTS_PER_HOUR - 1, Math.max(0, Math.floor(ratio * SLOTS_PER_HOUR)));
    const hour = parseInt(row.dataset.hour, 10);
    if (Number.isNaN(hour)) return null;

    return rowColToSlot(hour, col);
}

// ── 초기화 ──

document.addEventListener('DOMContentLoaded', function() {
    // 카테고리 데이터 전역 공유 (tag.js 모달에서 사용)
    apiCall('/api/categories/').then(data => {
        window._categories = data.categories;
    }).catch(err => console.error('카테고리 로드 오류:', err));

    initializeDashboard();
    initializeGridDrag();
    initializeGridKeyboard();
    initializeFillNow();
    initializeTagSelectDelegation('tagLegend');
    initializeTagSelectDelegation('tagContainer');

    // 태그 업데이트 이벤트 수신 (동적 변경 시에만 API 호출)
    document.addEventListener('tags-updated', function() {
        loadAvailableTags();
    });
});

function initializeTagSelectDelegation(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.addEventListener('click', function(event) {
        const el = event.target.closest('[data-tag-id]');
        if (!el || !container.contains(el)) return;
        const id = parseInt(el.dataset.tagId, 10);
        const color = el.dataset.tagColor;
        const name = el.dataset.tagName;
        if (!Number.isFinite(id) || !color || !name) return;
        selectTag(id, color, name);
    });
}

function initializeDashboard() {
    const dateSelector = document.getElementById('dateSelector');
    if (dateSelector) {
        dateSelector.addEventListener('change', function(event) {
            const url = new URL(window.location);
            url.searchParams.set('date', event.target.value);
            window.location.href = url.toString();
        });
    }

    // 온보딩처럼 이 그리드를 빌려 쓰는 화면에는 태그 만들기 버튼이 없다.
    const createTagBtn = document.getElementById('createNewTagBtn');
    if (createTagBtn) {
        createTagBtn.addEventListener('click', function() {
            window.openTagFormModal();
        });
    }

    document.querySelectorAll('[data-dashboard-sheet-close]').forEach((el) => {
        el.addEventListener('click', closeQuickInputSheet);
    });

    initQuickInputSheetSwipeToClose();
    syncQuickInputSheetForLayout();
    window.addEventListener('resize', syncQuickInputSheetForLayout);
}

// 핸들을 아래로 스와이프하면 닫는다(목업 4a). 핸들에서 시작한 제스처만
// 반응한다 — 태그 목록 스크롤과 겹치면 안 된다.
function initQuickInputSheetSwipeToClose() {
    const handle = document.querySelector('[data-dashboard-sheet-handle]');
    const sheet = document.getElementById('quickInputSheet');
    if (!handle || !sheet) return;

    const CLOSE_THRESHOLD_PX = 60;
    let startY = null;
    let dragY = 0;

    handle.addEventListener('touchstart', function (event) {
        if (!sheet.classList.contains('is-open')) return;
        startY = event.touches[0].clientY;
        dragY = 0;
        sheet.style.transition = 'none';
    }, { passive: true });

    handle.addEventListener('touchmove', function (event) {
        if (startY === null) return;
        dragY = Math.max(0, event.touches[0].clientY - startY);
        sheet.style.transform = `translateY(${dragY}px)`;
    }, { passive: true });

    handle.addEventListener('touchend', function () {
        if (startY === null) return;
        sheet.style.transition = '';
        sheet.style.transform = '';
        const shouldClose = dragY > CLOSE_THRESHOLD_PX;
        startY = null;
        if (shouldClose) closeQuickInputSheet();
    });
}

function syncQuickInputSheetForLayout() {
    const sheet = document.getElementById('quickInputSheet');
    const backdrop = document.getElementById('quickInputSheetBackdrop');
    if (!sheet || !backdrop) return;

    if (isMobileDashboardLayout()) {
        if (!sheet.classList.contains('is-open')) {
            sheet.setAttribute('role', 'dialog');
            sheet.setAttribute('aria-modal', 'true');
            sheet.setAttribute('aria-hidden', 'true');
            backdrop.setAttribute('aria-hidden', 'true');
        }
        return;
    }

    // 데스크톱 전환 강제 닫힘 경로에서도 keydown 리스너를 반드시 해제한다.
    document.removeEventListener('keydown', handleQuickInputSheetKeydown);
    sheet.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    sheet.removeAttribute('role');
    sheet.removeAttribute('aria-modal');
    sheet.setAttribute('aria-hidden', 'false');
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('dashboard-sheet-open');
}

function getQuickInputSheetFocusableElements(sheet) {
    // 매 호출 시 재계산: saveBtn 활성/비활성, 도움말 collapse 펼침 등
    // 열림 상태에서 변하는 요소를 즉시 반영해야 한다.
    return Array.from(
        sheet.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
    ).filter((el) => !el.disabled && el.getClientRects().length > 0);
}

function handleQuickInputSheetKeydown(event) {
    const sheet = document.getElementById('quickInputSheet');
    if (!sheet || !sheet.classList.contains('is-open') || !isMobileDashboardLayout()) return;

    if (event.key === 'Escape') {
        // IME 조합 중 Escape는 후보창 닫기 용도이므로 시트를 닫지 않는다.
        if (event.isComposing) return;
        // 시트 위에 열린 Bootstrap 모달(새 태그, 카테고리 설명)은
        // Bootstrap이 자체적으로 Escape를 처리하므로 시트는 유지한다.
        if (document.querySelector('.modal.show')) return;
        event.preventDefault();
        closeQuickInputSheet();
        return;
    }

    if (event.key !== 'Tab') return;
    const focusable = getQuickInputSheetFocusableElements(sheet);
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement;

    if (!sheet.contains(active)) {
        event.preventDefault();
        first.focus({ preventScroll: true });
        return;
    }
    if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus({ preventScroll: true });
    } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus({ preventScroll: true });
    }
}

function openQuickInputSheet() {
    if (!isMobileDashboardLayout() || selectedSlots.size === 0) return;
    const sheet = document.getElementById('quickInputSheet');
    const backdrop = document.getElementById('quickInputSheetBackdrop');
    if (!sheet || !backdrop) return;

    const wasOpen = sheet.classList.contains('is-open');
    sheet.classList.add('is-open');
    backdrop.classList.add('is-open');
    sheet.setAttribute('role', 'dialog');
    sheet.setAttribute('aria-modal', 'true');
    sheet.setAttribute('aria-hidden', 'false');
    backdrop.setAttribute('aria-hidden', 'false');
    document.body.classList.add('dashboard-sheet-open');

    // 열림 전이당 1회만 등록: 시트가 열린 채 슬롯을 추가 선택해도 중복 등록 없음.
    if (!wasOpen) {
        document.addEventListener('keydown', handleQuickInputSheetKeydown);
    }

    const firstTag = sheet.querySelector('.tag-btn');
    const closeBtn = sheet.querySelector('[data-dashboard-sheet-close]');
    (firstTag || closeBtn || sheet).focus({ preventScroll: true });
}

function closeQuickInputSheet() {
    const sheet = document.getElementById('quickInputSheet');
    const backdrop = document.getElementById('quickInputSheetBackdrop');
    if (!sheet || !backdrop) return;

    document.removeEventListener('keydown', handleQuickInputSheetKeydown);

    const firstSelected = Math.min(...selectedSlots);
    const focusTarget = Number.isFinite(firstSelected) ? blockForSlot(firstSelected) : null;
    if (focusTarget) {
        focusTarget.focus({ preventScroll: true });
    }

    sheet.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    sheet.setAttribute('aria-hidden', 'true');
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('dashboard-sheet-open');
}

