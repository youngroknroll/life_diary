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

    document.getElementById('createNewTagBtn').addEventListener('click', function() {
        window.openTagFormModal();
    });

    const manageTagsBtn = document.getElementById('manageTagsBtn');
    if (manageTagsBtn) {
        manageTagsBtn.addEventListener('click', function() {
            const tagsUrl = document.getElementById('quickInputSidebar').dataset.tagsUrl;
            window.location.href = tagsUrl;
        });
    }

    document.querySelectorAll('[data-dashboard-sheet-close]').forEach((el) => {
        el.addEventListener('click', closeQuickInputSheet);
    });

    syncQuickInputSheetForLayout();
    window.addEventListener('resize', syncQuickInputSheetForLayout);
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

// ── 슬롯 선택 ──

const selectSlot = (slotIndex, event) => {
    const isMultiSelect = !!(event && (event.ctrlKey || event.metaKey));

    if (!isMultiSelect) {
        selectedSlots.clear();
        selectedSlots.add(slotIndex);
    } else if (selectedSlots.has(slotIndex)) {
        selectedSlots.delete(slotIndex);
    } else {
        selectedSlots.add(slotIndex);
    }

    renderSelection();
    showSlotInfo(Array.from(selectedSlots));
    updateButtons();
    openQuickInputSheet();
};

const clearSelection = () => {
    selectedSlots.clear();
    renderSelection();
};

const renderSelection = () => {
    document.querySelectorAll('.day-row[data-hour]').forEach(row => {
        const layer = row.querySelector('.day-row__selection');
        if (!layer) return;

        const hour = parseInt(row.dataset.hour, 10);
        layer.textContent = '';

        let column = 0;
        while (column < SLOTS_PER_HOUR) {
            if (!selectedSlots.has(rowColToSlot(hour, column))) {
                column += 1;
                continue;
            }

            let span = 0;
            while (
                column + span < SLOTS_PER_HOUR &&
                selectedSlots.has(rowColToSlot(hour, column + span))
            ) {
                span += 1;
            }

            const chunk = document.createElement('div');
            chunk.className = 'is-selected';
            chunk.style.gridColumn = `${column + 1} / span ${span}`;
            layer.appendChild(chunk);

            column += span;
        }
    });

};

// ── 드래그 ──

const restoreBaseSelection = () => {
    dragBaseSelection.forEach(index => selectedSlots.add(index));
};

const dragOver = (slotIndex) => {
    if (!isDragging || startSlot === null) return;

    const startPos = slotToRowCol(startSlot);
    const endPos = slotToRowCol(slotIndex);

    selectedSlots.clear();
    if (isAdditiveDrag) restoreBaseSelection();

    if (startPos.col === endPos.col && startPos.row !== endPos.row) {
                const minRow = Math.min(startPos.row, endPos.row);
        const maxRow = Math.max(startPos.row, endPos.row);
        for (let row = minRow; row <= maxRow; row++) {
            selectedSlots.add(rowColToSlot(row, startPos.col));
        }
    } else {
                const minIndex = Math.min(startSlot, slotIndex);
        const maxIndex = Math.max(startSlot, slotIndex);
        for (let index = minIndex; index <= maxIndex; index++) {
            selectedSlots.add(index);
        }
    }

    renderSelection();
    showSlotInfo(Array.from(selectedSlots));
    updateButtons();
};

const endDrag = () => {
    if (!isDragging) return;

    isDragging = false;
    startSlot = null;
    isAdditiveDrag = false;
    dragBaseSelection = new Set();
    showSlotInfo(Array.from(selectedSlots));
    updateButtons();
    openQuickInputSheet();
};

/**
 * 포인터 없이도 기록할 수 있어야 한다. 기록은 이 제품의 핵심 루프다.
 * 방향키로 칸을 옮기고, Shift를 누른 채 옮기면 범위가 늘어난다.
 */
function initializeGridKeyboard() {
    const grid = document.getElementById('timeGrid');
    if (!grid) return;

    const STEP = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -SLOTS_PER_HOUR, ArrowDown: SLOTS_PER_HOUR };
    let anchorSlot = null;
    let cursorSlot = null;

    grid.addEventListener('keydown', (event) => {
        const block = event.target.closest('.slot-block');
        if (!block) return;

        // 블록 하나가 여러 칸을 덮으므로 커서를 따로 든다. 블록의 시작점을
        // 쓰면 넓은 블록 안에서 방향키가 제자리를 맴돈다.
        const blockStart = parseInt(block.dataset.start, 10);
        const blockSpan = parseInt(block.dataset.span, 10);
        if (cursorSlot === null || cursorSlot < blockStart || cursorSlot >= blockStart + blockSpan) {
            cursorSlot = blockStart;
        }

        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            anchorSlot = cursorSlot;
            selectSlot(cursorSlot, event);
            return;
        }

        if (!(event.key in STEP)) return;
        event.preventDefault();

        const target = cursorSlot + STEP[event.key];
        if (target < 0 || target >= TOTAL_SLOTS) return;
        cursorSlot = target;

        if (event.shiftKey) {
            if (anchorSlot === null) anchorSlot = slotIndex;
            selectRange(anchorSlot, target);
        } else {
            anchorSlot = target;
            selectedSlots.clear();
            selectedSlots.add(target);
            renderSelection();
            showSlotInfo(Array.from(selectedSlots));
            updateButtons();
        }

        blockForSlot(target)?.focus({ preventScroll: false });
    });
}

const selectRange = (from, to) => {
    selectedSlots.clear();
    for (let index = Math.min(from, to); index <= Math.max(from, to); index++) {
        selectedSlots.add(index);
    }
    renderSelection();
    showSlotInfo(Array.from(selectedSlots));
    updateButtons();
};

/** 모바일 세로 스와이프는 touch-action:pan-y 가 스크롤로 가져간다. */
function initializeGridDrag() {
    const grid = document.getElementById('timeGrid');
    if (!grid) return;

    let movedDuringDrag = false;

    grid.addEventListener('pointerdown', (event) => {
        if (event.button !== 0 && event.pointerType === 'mouse') return;

        const slotIndex = slotFromPoint(event.clientX, event.clientY);
        if (slotIndex === null) return;

        isDragging = true;
        movedDuringDrag = false;
        startSlot = slotIndex;
        isAdditiveDrag = !!(event.ctrlKey || event.metaKey);
        dragBaseSelection = isAdditiveDrag ? new Set(selectedSlots) : new Set();

        if (!isAdditiveDrag) {
            selectedSlots.clear();
        }
        selectedSlots.add(slotIndex);
        renderSelection();

        grid.setPointerCapture(event.pointerId);
    });

    grid.addEventListener('pointermove', (event) => {
        if (!isDragging) return;

        const slotIndex = slotFromPoint(event.clientX, event.clientY);
        if (slotIndex === null || slotIndex === startSlot) return;

        movedDuringDrag = true;
        dragOver(slotIndex);
    });

    grid.addEventListener('pointerup', (event) => {
        if (!isDragging) return;

        if (grid.hasPointerCapture(event.pointerId)) {
            grid.releasePointerCapture(event.pointerId);
        }

        if (!movedDuringDrag && startSlot !== null) {
            const clicked = startSlot;
            isDragging = false;
            startSlot = null;
            selectSlot(clicked, event);
            return;
        }

        endDrag();
    });

    grid.addEventListener('pointercancel', () => {
        if (!isDragging) return;

        isDragging = false;
        startSlot = null;
        isAdditiveDrag = false;

        // pointerdown 이 이미 한 칸을 칠해 뒀다. 스크롤로 넘어간 제스처가
        // 선택만 남기고 사라지면 화면과 저장 버튼 상태가 어긋난다.
        selectedSlots = new Set(dragBaseSelection);
        dragBaseSelection = new Set();
        renderSelection();
        showSlotInfo(Array.from(selectedSlots));
        updateButtons();
    });
}

// ── 슬롯 정보 표시 ──

const showSlotInfo = (slotIndexes) => {
    const inlineEl = document.getElementById('slotInfoInline');
    if (!inlineEl) return;

    if (!slotIndexes || slotIndexes.length === 0) {
        const promptText = gettext('그리드에서 시간을 선택하세요');
        inlineEl.innerHTML = `<small class="text-muted"><i class="fas fa-hand-pointer me-1"></i>${promptText}</small>`;
        return;
    }

    const hasFilledSlot = slotIndexes.some(idx =>
        isSlotFilled(idx)
    );

    const nextActionPrompt = gettext('시간을 선택했어요. 원하는 태그를 선택하세요.');
    let infoHTML = '';
    if (slotIndexes.length === 1) {
        const slotIndex = slotIndexes[0];
        const timeRange = `${slotIndexToTime(slotIndex)}–${slotIndexToTime(slotIndex + 1)}`;
        const tagInfo = slotTagInfo(slotIndex);
        const tagName = tagInfo ? tagInfo.tagName : gettext('빈 슬롯');
        const memo = tagInfo ? tagInfo.memo : '';

        const labelTime = gettext('시간:');
        const labelStatus = gettext('상태:');
        const deleteLabel = gettext('삭제');
        infoHTML = `<div class="d-flex justify-content-between align-items-start">
            <div>
                <div class="text-muted"><strong>${labelTime}</strong> ${timeRange}</div>
                <div class="text-muted"><strong>${labelStatus}</strong> ${tagName}</div>
                ${memo ? `<div class="text-muted small">${memo}</div>` : ''}
                <div class="text-primary small mt-1"><i class="fas fa-tags me-1"></i>${nextActionPrompt}</div>
            </div>
            ${hasFilledSlot ? `<button class="btn btn-outline-danger btn-sm" onclick="deleteSlot()"><i class="fas fa-trash me-1"></i>${deleteLabel}</button>` : ''}
        </div>`;
    } else {
        const sortedSlots = slotIndexes.slice().sort((a, b) => a - b);
        const startTime = slotIndexToTime(sortedSlots[0]);
        const endTime = slotIndexToTime(sortedSlots[sortedSlots.length - 1] + 1);
        const duration = slotIndexes.length * 10;
        const slotsLabel = interpolate(
            ngettext('%s개 슬롯', '%s개 슬롯', slotIndexes.length),
            [slotIndexes.length]
        );
        const durationLabel = interpolate(
            gettext('%(h)s시간 %(m)s분'),
            { h: Math.floor(duration / 60), m: duration % 60 },
            true
        );
        const deleteLabel = gettext('삭제');

        infoHTML = `<div class="d-flex justify-content-between align-items-start">
            <div>
                <div class="text-muted"><strong>${slotsLabel}</strong> ${startTime} - ${endTime}</div>
                <div class="text-muted small">${durationLabel}</div>
                <div class="text-primary small mt-1"><i class="fas fa-tags me-1"></i>${nextActionPrompt}</div>
            </div>
            ${hasFilledSlot ? `<button class="btn btn-outline-danger btn-sm" onclick="deleteSlot()"><i class="fas fa-trash me-1"></i>${deleteLabel}</button>` : ''}
        </div>`;
    }

    inlineEl.innerHTML = infoHTML;
};

// ── 버튼/태그 선택 ──

const updateButtons = () => {
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn) saveBtn.disabled = !(selectedSlots.size > 0 && selectedTag !== null);
};

const selectTag = (tagId, tagColor, tagName) => {
    document.querySelectorAll('.tag-btn').forEach(btn => btn.classList.remove('active'));
    const targetBtn = event.target.closest('.tag-btn');
    if (targetBtn) targetBtn.classList.add('active');
    selectedTag = { id: tagId, color: tagColor, name: tagName };
    updateButtons();
};

function renderRows(rows) {
    (rows || []).forEach(row => {
        const rowElement = document.querySelector(`.day-row[data-hour="${row.hour}"]`);
        if (!rowElement) return;

        const cells = rowElement.querySelector('.day-row__cells');
        const selectionLayer = cells.querySelector('.day-row__selection');

        cells.textContent = '';
        row.runs.forEach(run => cells.appendChild(buildBlock(run)));
        if (selectionLayer) cells.appendChild(selectionLayer);
    });

    renderSelection();
}

function buildBlock(run) {
    const block = document.createElement('div');
    block.className = run.tag_id ? 'slot-block' : 'slot-block is-empty';
    block.style.gridColumn = `span ${run.span}`;
    block.style.setProperty('--slot-span', run.span);
    block.dataset.start = run.start_index;
    block.dataset.span = run.span;

    block.setAttribute('role', 'button');
    block.setAttribute('tabindex', '0');

    if (run.tag_id) {
        block.style.backgroundColor = run.color;
        block.dataset.tagId = run.tag_id;
        block.title = run.memo ? `${run.tag_name} · ${run.memo}` : run.tag_name;
    } else {
        block.title = gettext('빈 구간');
    }

    if (run.label) {
        const label = document.createElement('span');
        label.className = 'slot-block__label';
        label.textContent = run.label;
        block.appendChild(label);
    }

    return block;
}

function renderDayStats(stats) {
    if (!stats) return;

    const filled = document.getElementById('filledSlots');
    const percentage = document.getElementById('fillPercentage');
    const loggedTime = document.getElementById('loggedTime');

    const empty = document.getElementById('emptySlots');
    const filledCount = Math.round(stats.logged_minutes / 10);
    if (filled) filled.textContent = filledCount;
    if (empty) empty.textContent = TOTAL_SLOTS - filledCount;
    if (percentage) percentage.textContent = `${stats.fill_percentage}%`;
    if (loggedTime) {
        loggedTime.textContent = interpolate(
            gettext('%(h)s시간 %(m)s분'),
            { h: Math.floor(stats.logged_minutes / 60), m: stats.logged_minutes % 60 },
            true
        );
    }
}

let undoTimer = null;

function showUndoSnackbar(message, token) {
    const snackbar = document.getElementById('undoSnackbar');
    if (!snackbar || !token) return;

    snackbar.querySelector('[data-undo-message]').textContent = message;
    snackbar.querySelector('[data-undo-action]').onclick = () => runUndo(token);
    snackbar.classList.add('is-open');

    clearTimeout(undoTimer);
    undoTimer = setTimeout(hideUndoSnackbar, 5000);
}

function hideUndoSnackbar() {
    const snackbar = document.getElementById('undoSnackbar');
    if (snackbar) snackbar.classList.remove('is-open');
    clearTimeout(undoTimer);
}

async function runUndo(token) {
    hideUndoSnackbar();

    try {
        const result = await apiCall('/api/time-blocks/undo/', {
            method: 'POST',
            data: { undo_token: token }
        });
        renderRows(result.runs);
        renderDayStats(result.stats);
        showNotification(result.message, 'success');
    } catch (error) {
        showNotification(
            interpolate(gettext('되돌리기 실패: %s'), [error.message]),
            'warning'
        );
    }
}

// ── 저장/삭제 ──

const saveSlot = async () => {
    if (selectedSlots.size === 0) {
        showNotification(gettext('슬롯을 선택해주세요.'), 'warning');
        return;
    }

    if (!selectedTag) {
        showNotification(gettext('태그를 선택해주세요.'), 'warning');
        return;
    }

    const saveBtn = document.getElementById('saveBtn');
    const slotIndexes = Array.from(selectedSlots);
    const affectedRows = snapshotRows(slotIndexes);

    paintSelectedSlots(selectedTag.color);

    try {
        const memo = document.getElementById('memoInput').value.trim();
        const date = document.getElementById('dateSelector').value;

        const result = await apiCall('/api/time-blocks/', {
            method: 'POST',
            data: {
                slot_indexes: slotIndexes,
                tag_id: selectedTag.id,
                memo: memo,
                date: date
            },
            loadingElement: saveBtn
        });

        renderRows(result.runs);
        renderDayStats(result.stats);
        clearSelection();
        updateButtons();
        closeQuickInputSheet();
        showUndoSnackbar(result.message, result.undo_token);

    } catch (error) {
        restoreRows(affectedRows);
        showNotification(interpolate(gettext('저장 실패: %s'), [error.message]), 'error');
        console.error('Save error:', error);
    }
};

function snapshotRows(slotIndexes) {
    const hours = new Set(slotIndexes.map(index => Math.floor(index / SLOTS_PER_HOUR)));

    return Array.from(hours).map(hour => {
        const cells = document
            .querySelector(`.day-row[data-hour="${hour}"]`)
            ?.querySelector('.day-row__cells');
        return { hour, html: cells ? cells.innerHTML : null };
    });
}

function restoreRows(snapshots) {
    snapshots.forEach(({ hour, html }) => {
        if (html === null) return;
        const cells = document
            .querySelector(`.day-row[data-hour="${hour}"]`)
            ?.querySelector('.day-row__cells');
        if (cells) cells.innerHTML = html;
    });
    renderSelection();
}

function paintSelectedSlots(color) {
    document.querySelectorAll('.day-row[data-hour]').forEach(row => {
        const hour = parseInt(row.dataset.hour, 10);
        const selected = [];
        for (let column = 0; column < SLOTS_PER_HOUR; column++) {
            if (selectedSlots.has(rowColToSlot(hour, column))) selected.push(column);
        }
        if (selected.length === 0) return;

        row.querySelectorAll('.slot-block').forEach(block => {
            const start = parseInt(block.dataset.start, 10);
            const span = parseInt(block.dataset.span, 10);
            const covered = [];
            for (let index = start; index < start + span; index++) {
                if (selectedSlots.has(index)) covered.push(index);
            }
            if (covered.length !== span) return;

            block.classList.remove('is-empty');
            block.style.backgroundColor = color;
        });
    });
}

const deleteSlot = async () => {
    if (selectedSlots.size === 0) {
        showNotification(gettext('삭제할 슬롯을 선택해주세요.'), 'warning');
        return;
    }

    const filledSlots = Array.from(selectedSlots).filter(idx =>
        isSlotFilled(idx)
    );

    if (filledSlots.length === 0) {
        showNotification(gettext('삭제할 기록이 없습니다.'), 'warning');
        return;
    }

    const confirmMsg = interpolate(
        ngettext(
            '%s개의 기록된 슬롯을 삭제하시겠습니까?',
            '%s개의 기록된 슬롯을 삭제하시겠습니까?',
            filledSlots.length
        ),
        [filledSlots.length]
    );
    if (!confirmDelete(confirmMsg)) {
        return;
    }

    const affectedRows = snapshotRows(filledSlots);

    try {
        const date = document.getElementById('dateSelector').value;

        const result = await apiCall('/api/time-blocks/', {
            method: 'DELETE',
            data: {
                slot_indexes: filledSlots,
                date: date
            }
        });

        renderRows(result.runs);
        renderDayStats(result.stats);
        clearSelection();
        updateButtons();
        closeQuickInputSheet();
        showUndoSnackbar(result.message, result.undo_token);

    } catch (error) {
        restoreRows(affectedRows);
        showNotification(interpolate(gettext('삭제 실패: %s'), [error.message]), 'error');
        console.error('Delete error:', error);
    }
};

// ── 태그 로딩/렌더링 ──

async function loadAvailableTags() {
    try {
        const result = await apiCall('/api/tags/');
        renderTagContainer(result.tags);
        renderTagLegend(result.tags);
    } catch (error) {
        showTagError(gettext('태그 로드 중 오류가 발생했습니다.'));
    }
}

function renderTagButton(tag) {
    const safeName = escapeHtml(tag.name);
    const safeColor = escapeHtml(tag.color);
    return `
        <button type="button" class="btn btn-outline-secondary btn-sm tag-btn text-start"
                data-tag-id="${tag.id}"
                data-tag-color="${safeColor}"
                data-tag-name="${safeName}">
            <span class="badge me-2" style="background-color: ${safeColor};">&nbsp;</span>
            ${safeName}
            ${tag.is_default ? `<i class="fas fa-star text-warning ms-1" title="${gettext('기본 태그')}"></i>` : ''}
        </button>`;
}

function renderCategoryHeader(categoryName, categoryCount = null) {
    const template = document.getElementById('tagCategoryHeaderTemplate');
    const safeName = escapeHtml(categoryName);
    if (!template || !template.content || !template.content.firstElementChild) {
        const countHtml = categoryCount === null ? '' :
            `<small class="text-muted ms-1">(${categoryCount})</small>`;
        return `<div class="tag-category-header small text-muted fw-bold mt-2 mb-1">- ${safeName}${countHtml}</div>`;
    }

    const header = template.content.firstElementChild.cloneNode(true);
    const nameEl = header.querySelector('[data-tag-category-name]');
    const countEl = header.querySelector('[data-tag-category-count]');
    if (nameEl) nameEl.textContent = `- ${categoryName}`;
    if (countEl) {
        if (categoryCount === null) {
            countEl.remove();
        } else {
            countEl.classList.remove('d-none');
            countEl.textContent = `(${categoryCount})`;
        }
    }

    return header.outerHTML;
}

function renderTagContainer(tags) {
    const tagContainer = document.getElementById('tagContainer');
    if (tags.length === 0) {
        const emptyHtml = gettext("태그가 없습니다.<br>'새 태그' 버튼으로 추가하세요.");
        tagContainer.innerHTML = `<div class="text-center py-2">
            <p class="text-muted small">${emptyHtml}</p>
        </div>`;
        return;
    }

    const categories = window._categories || [];
    // 카테고리 메타가 아직 로드되지 않았으면 flat 폴백
    if (categories.length === 0) {
        tagContainer.innerHTML = tags.map(renderTagButton).join('');
        return;
    }

    const byCategory = new Map();
    for (const tag of tags) {
        const key = tag.category_id;
        if (!byCategory.has(key)) byCategory.set(key, []);
        byCategory.get(key).push(tag);
    }

    const sorted = [...categories].sort(
        (a, b) => a.display_order - b.display_order
    );

    tagContainer.innerHTML = sorted
        .filter(cat => byCategory.has(cat.id))
        .map(cat => `
            <div class="tag-category-group">
                ${renderCategoryHeader(cat.name)}
                <div class="d-grid gap-1">
                    ${byCategory.get(cat.id).map(renderTagButton).join('')}
                </div>
            </div>
        `).join('');
}

function renderTagLegend(tags) {
    const tagLegend = document.getElementById('tagLegend');
    if (tags.length === 0) {
        tagLegend.innerHTML = `<small class="text-muted">${gettext('생성된 태그가 없습니다.')}</small>`;
        return;
    }
    tagLegend.innerHTML = tags.map(tag => {
        const textColor = getContrastTextColor(tag.color);
        return `
        <button type="button" class="badge btn-tag-legend"
                data-tag-id="${tag.id}"
                data-tag-color="${escapeHtml(tag.color)}"
                data-tag-name="${escapeHtml(tag.name)}"
                style="background-color: ${escapeHtml(tag.color)}; color: ${textColor}; border: 0;">${escapeHtml(tag.name)}</button>`;
    }).join('');
}

function showTagError(message) {
    const tagContainer = document.getElementById('tagContainer');
    tagContainer.innerHTML = `<div class="alert alert-danger p-2 small">${message}</div>`;
}
