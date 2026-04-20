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
let touchStartX = 0, touchStartY = 0, touchDecided = false;

// ── 그리드 칼럼 수 (반응형) ──

function getGridColumns() {
    return window.innerWidth <= 768 ? 6 : 12;
}

function slotToRowCol(slotIndex) {
    const cols = getGridColumns();
    return { row: Math.floor(slotIndex / cols), col: slotIndex % cols };
}

function rowColToSlot(row, col) {
    return row * getGridColumns() + col;
}

// ── 초기화 ──

document.addEventListener('DOMContentLoaded', function() {
    // 카테고리 데이터 전역 공유 (tag.js 모달에서 사용)
    apiCall('/api/categories/').then(data => {
        window._categories = data.categories;
    }).catch(err => console.error('카테고리 로드 오류:', err));

    initializeDashboard();

    // 태그 업데이트 이벤트 수신 (동적 변경 시에만 API 호출)
    document.addEventListener('tags-updated', function() {
        loadAvailableTags();
    });
});

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
}

// ── 슬롯 선택 ──

const selectSlot = (slotIndex) => {
    if (isDragging) return;

    const slotElement = document.querySelector(`[data-slot-index="${slotIndex}"]`);
    if (!slotElement) return;

    const isMultiSelect = event.ctrlKey || event.metaKey;

    if (!isMultiSelect) {
        clearSelection();
        selectedSlots.add(slotIndex);
        slotElement.classList.add('selected');
    } else {
        if (selectedSlots.has(slotIndex)) {
            selectedSlots.delete(slotIndex);
            slotElement.classList.remove('selected');
        } else {
            selectedSlots.add(slotIndex);
            slotElement.classList.add('selected');
        }
    }

    showSlotInfo(Array.from(selectedSlots));
    updateButtons();
};

const clearSelection = () => {
    selectedSlots.clear();
    document.querySelectorAll('.time-slot').forEach(slot => {
        slot.classList.remove('selected');
    });
};

// ── 드래그 ──

const startDrag = (slotIndex) => {
    isDragging = true;
    startSlot = slotIndex;
    clearSelection();
    selectedSlots.add(slotIndex);
    const slotElement = document.querySelector(`[data-slot-index="${slotIndex}"]`);
    if (slotElement) slotElement.classList.add('selected');
};

const handleTouchStart = (slotIndex, event) => {
    const touch = event.touches[0];
    touchStartX = touch.clientX;
    touchStartY = touch.clientY;
    touchDecided = false;
    startDrag(slotIndex);
};

const dragOver = (slotIndex) => {
    if (!isDragging || startSlot === null) return;

    const startPos = slotToRowCol(startSlot);
    const endPos = slotToRowCol(slotIndex);
    const minRow = Math.min(startPos.row, endPos.row);
    const maxRow = Math.max(startPos.row, endPos.row);
    const minCol = Math.min(startPos.col, endPos.col);
    const maxCol = Math.max(startPos.col, endPos.col);

    clearSelection();
    for (let r = minRow; r <= maxRow; r++) {
        for (let c = minCol; c <= maxCol; c++) {
            const idx = rowColToSlot(r, c);
            selectedSlots.add(idx);
            const slotElement = document.querySelector(`[data-slot-index="${idx}"]`);
            if (slotElement) slotElement.classList.add('selected');
        }
    }
    showSlotInfo(Array.from(selectedSlots));
    updateButtons();
};

const endDrag = () => {
    if (isDragging) {
        isDragging = false;
        startSlot = null;
        showSlotInfo(Array.from(selectedSlots));
        updateButtons();
    }
};

const handleTouchMove = (event) => {
    if (!isDragging) return;
    const touch = event.touches[0];

    if (!touchDecided) {
        const dx = Math.abs(touch.clientX - touchStartX);
        const dy = Math.abs(touch.clientY - touchStartY);
        if (dx < 5 && dy < 5) return;
        touchDecided = true;
    }

    event.preventDefault();
    const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
    if (elementBelow && elementBelow.classList.contains('time-slot')) {
        const slotIndex = parseInt(elementBelow.dataset.slotIndex, 10);
        if (!isNaN(slotIndex)) {
            dragOver(slotIndex);
        }
    }
};

document.addEventListener('mouseup', endDrag);
document.addEventListener('mouseleave', endDrag);

// ── 슬롯 정보 표시 ──

const showSlotInfo = (slotIndexes) => {
    const inlineEl = document.getElementById('slotInfoInline');
    if (!inlineEl) return;

    if (!slotIndexes || slotIndexes.length === 0) {
        inlineEl.innerHTML = '<small class="text-muted"><i class="fas fa-hand-pointer me-1"></i>그리드에서 시간을 선택하세요</small>';
        return;
    }

    const hasFilledSlot = slotIndexes.some(idx =>
        document.querySelector(`[data-slot-index="${idx}"]`)?.classList.contains('filled')
    );

    let infoHTML = '';
    if (slotIndexes.length === 1) {
        const slotIndex = slotIndexes[0];
        const slotElement = document.querySelector(`[data-slot-index="${slotIndex}"]`);
        if (!slotElement) return;

        const timeRange = slotElement.getAttribute('title').split(' - ')[0];
        let tagName = '빈 슬롯';
        let memo = '';

        if (slotElement.classList.contains('filled')) {
            const titleParts = slotElement.title.split(' - ');
            if (titleParts.length > 1) {
                const tagAndMemo = titleParts[1];
                const colonIndex = tagAndMemo.indexOf(':');
                if (colonIndex !== -1) {
                    tagName = tagAndMemo.substring(0, colonIndex);
                    memo = tagAndMemo.substring(colonIndex + 1).trim();
                } else {
                    tagName = tagAndMemo;
                }
            } else {
                tagName = '알 수 없음';
            }
        }

        infoHTML = `<div class="d-flex justify-content-between align-items-start">
            <div>
                <div class="text-muted"><strong>시간:</strong> ${timeRange}</div>
                <div class="text-muted"><strong>상태:</strong> ${tagName}</div>
                ${memo ? `<div class="text-muted small">${memo}</div>` : ''}
            </div>
            ${hasFilledSlot ? `<button class="btn btn-outline-danger btn-sm" onclick="deleteSlot()"><i class="fas fa-trash me-1"></i>삭제</button>` : ''}
        </div>`;
    } else {
        const sortedSlots = slotIndexes.slice().sort((a, b) => a - b);
        const startTime = slotIndexToTime(sortedSlots[0]);
        const endTime = slotIndexToTime(sortedSlots[sortedSlots.length - 1] + 1);
        const duration = slotIndexes.length * 10;

        infoHTML = `<div class="d-flex justify-content-between align-items-start">
            <div>
                <div class="text-muted"><strong>${slotIndexes.length}개 슬롯</strong> ${startTime} - ${endTime}</div>
                <div class="text-muted small">${Math.floor(duration/60)}시간 ${duration%60}분</div>
            </div>
            ${hasFilledSlot ? `<button class="btn btn-outline-danger btn-sm" onclick="deleteSlot()"><i class="fas fa-trash me-1"></i>삭제</button>` : ''}
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

// ── 저장/삭제 ──

const saveSlot = async () => {
    if (selectedSlots.size === 0) {
        showNotification('슬롯을 선택해주세요.', 'warning');
        return;
    }

    if (!selectedTag) {
        showNotification('태그를 선택해주세요.', 'warning');
        return;
    }

    const saveBtn = document.getElementById('saveBtn');

    try {
        const memo = document.getElementById('memoInput').value.trim();
        const date = document.getElementById('dateSelector').value;

        const result = await apiCall('/api/time-blocks/', {
            method: 'POST',
            data: {
                slot_indexes: Array.from(selectedSlots),
                tag_id: selectedTag.id,
                memo: memo,
                date: date
            },
            loadingElement: saveBtn
        });

        showNotification(result.message, 'success');
        setTimeout(() => location.reload(), 1000);

    } catch (error) {
        showNotification(`저장 실패: ${error.message}`, 'error');
        console.error('Save error:', error);
    }
};

const deleteSlot = async () => {
    if (selectedSlots.size === 0) {
        showNotification('삭제할 슬롯을 선택해주세요.', 'warning');
        return;
    }

    const filledSlots = Array.from(selectedSlots).filter(idx =>
        document.querySelector(`[data-slot-index="${idx}"]`)?.classList.contains('filled')
    );

    if (filledSlots.length === 0) {
        showNotification('삭제할 기록이 없습니다.', 'warning');
        return;
    }

    if (!confirm(`${filledSlots.length}개의 기록된 슬롯을 삭제하시겠습니까?`)) {
        return;
    }

    try {
        const date = document.getElementById('dateSelector').value;

        const result = await apiCall('/api/time-blocks/', {
            method: 'DELETE',
            data: {
                slot_indexes: filledSlots,
                date: date
            }
        });

        showNotification(result.message, 'success');
        setTimeout(() => location.reload(), 1000);

    } catch (error) {
        showNotification(`삭제 실패: ${error.message}`, 'error');
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
        showTagError('태그 로드 중 오류가 발생했습니다.');
    }
}

function renderTagContainer(tags) {
    const tagContainer = document.getElementById('tagContainer');
    if (tags.length === 0) {
        tagContainer.innerHTML = `<div class="text-center py-2">
            <p class="text-muted small">태그가 없습니다.<br>'새 태그' 버튼으로 추가하세요.</p>
        </div>`;
        return;
    }

    tagContainer.innerHTML = tags.map(tag => `
        <button class="btn btn-outline-secondary btn-sm tag-btn text-start"
                    data-tag-id="${tag.id}"
                    onclick="selectTag(${tag.id}, '${tag.color}', '${tag.name}')">
                <span class="badge me-2" style="background-color: ${tag.color};">&nbsp;</span>
                ${tag.name}
            ${tag.is_default ? '<i class="fas fa-star text-warning ms-1" title="기본 태그"></i>' : ''}
            </button>
    `).join('');
}

function renderTagLegend(tags) {
    const tagLegend = document.getElementById('tagLegend');
    if (tags.length === 0) {
        tagLegend.innerHTML = '<small class="text-muted">생성된 태그가 없습니다.</small>';
        return;
    }
    tagLegend.innerHTML = tags.map(tag => `
        <span class="badge" style="background-color: ${tag.color}; color: ${getContrastTextColor(tag.color)};">${tag.name}</span>
    `).join('');
}

function showTagError(message) {
    const tagContainer = document.getElementById('tagContainer');
    tagContainer.innerHTML = `<div class="alert alert-danger p-2 small">${message}</div>`;
}

