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
            // Shift+방향키로 넓혀 둔 범위가 있으면 그것을 확정한다.
            // selectSlot 은 범위를 지우고 한 칸으로 되돌리므로 여기서 부르면
            // 키보드 사용자는 여러 칸을 기록할 방법이 없어진다.
            if (selectedSlots.size > 1 && selectedSlots.has(cursorSlot)) {
                openQuickInputSheet();
                return;
            }
            anchorSlot = cursorSlot;
            selectSlot(cursorSlot, event);
            return;
        }

        if (!(event.key in STEP)) return;
        event.preventDefault();

        const origin = cursorSlot;
        const target = origin + STEP[event.key];
        if (target < 0 || target >= TOTAL_SLOTS) return;
        cursorSlot = target;

        if (event.shiftKey) {
            // Enter 없이 Shift+방향키로 시작하면 기준점이 없다. 움직이기 전
            // 자리를 기준으로 삼는다.
            if (anchorSlot === null) anchorSlot = origin;
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

/** 빈 화면에서 다음 동작 하나만 제시한다 — 지금 시각 한 칸을 고른다. */
function initializeFillNow() {
    const button = document.getElementById('fillNowBtn');
    if (!button) return;

    button.addEventListener('click', () => {
        const now = new Date();
        const slotIndex = now.getHours() * SLOTS_PER_HOUR
            + Math.floor(now.getMinutes() / 10);

        selectSlot(slotIndex, null);

        // CSS 미디어쿼리는 브라우저 스크롤 애니메이션을 막지 못한다.
        // 모션을 줄여 달라는 설정은 여기서 직접 봐야 지켜진다.
        const target = blockForSlot(slotIndex);
        if (!target) return;
        target.scrollIntoView({ block: 'center', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });

        // 버튼에 포커스가 남으면 어느 칸이 잡혔는지 알 수 없다. 모바일은
        // openQuickInputSheet 가 시트로 포커스를 옮기므로 건드리지 않는다.
        if (!isMobileDashboardLayout()) {
            target.focus({ preventScroll: true });
        }
    });
}

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
        inlineEl.innerHTML = `<span class="quick-input-sheet__prompt">${escapeHtml(promptText)}</span>`;
        return;
    }

    const hasFilledSlot = slotIndexes.some(idx =>
        isSlotFilled(idx)
    );

    // 시간을 선택했어요. 원하는 태그를 선택하세요. — 아래 infoHTML 대입보다
    // 앞에 두는 순서를 테스트가 고정한다(test_selected_slot_info_prompts_tag_selection).
    const nextActionPrompt = gettext('시간을 선택했어요. 원하는 태그를 선택하세요.');
    const deleteLabel = gettext('삭제');
    let timeRange, metaLine, memoLine = '';

    if (slotIndexes.length === 1) {
        const slotIndex = slotIndexes[0];
        timeRange = `${slotIndexToTime(slotIndex)}–${slotIndexToTime(slotIndex + 1)}`;
        const tagInfo = slotTagInfo(slotIndex);
        const tagName = tagInfo ? tagInfo.tagName : gettext('빈 슬롯');
        metaLine = `${escapeHtml(tagName)} · ${escapeHtml(nextActionPrompt)}`;
        if (tagInfo && tagInfo.memo) {
            memoLine = `<span class="quick-input-sheet__memo-preview">${escapeHtml(tagInfo.memo)}</span>`;
        }
    } else {
        const sortedSlots = slotIndexes.slice().sort((a, b) => a - b);
        timeRange = `${slotIndexToTime(sortedSlots[0])}–${slotIndexToTime(sortedSlots[sortedSlots.length - 1] + 1)}`;
        const slotsLabel = interpolate(
            ngettext('%s칸 선택', '%s칸 선택', slotIndexes.length),
            [slotIndexes.length]
        );
        metaLine = `${escapeHtml(slotsLabel)} · ${escapeHtml(nextActionPrompt)}`;
    }

    const infoHTML = `
        <span class="quick-input-sheet__time num">${escapeHtml(timeRange)}</span>
        <span class="quick-input-sheet__meta">${metaLine}</span>
        ${memoLine}
        ${hasFilledSlot ? `<button type="button" class="quick-input-sheet__delete" onclick="deleteSlot()">${escapeHtml(deleteLabel)}</button>` : ''}
    `;

    inlineEl.innerHTML = infoHTML;
};

