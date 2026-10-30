// ── 버튼/태그 선택 ──

const updateButtons = () => {
    const saveBtn = document.getElementById('saveBtn');
    if (!saveBtn) return;
    saveBtn.disabled = !(selectedSlots.size > 0 && selectedTag !== null);
    saveBtn.textContent = selectedSlots.size > 0
        ? interpolate(ngettext('%s칸 저장', '%s칸 저장', selectedSlots.size), [selectedSlots.size])
        : gettext('저장');
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
    if (!token) return;
    if (!snackbar) {
        // 이 그리드를 빌려 쓰는 화면에는 스낵바가 없다. 조용히 넘어가면
        // 저장됐다는 사실이 아무에게도 전달되지 않는다.
        showNotification(message, 'success');
        return;
    }

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
        // 닫기를 선택 해제보다 먼저 한다. closeQuickInputSheet 는 남아 있는
        // 선택으로 포커스를 되돌릴 칸을 찾는데, 순서가 뒤집히면 되돌릴 칸이
        // 없어 포커스가 시트 안에 남은 채 aria-hidden 이 걸린다.
        closeQuickInputSheet();
        clearSelection();
        updateButtons();
        showUndoSnackbar(result.message, result.undo_token);

        // 이 그리드를 빌려 쓰는 화면이 저장 성공을 알아야 다음으로 넘어갈지
        // 판단할 수 있다. 실패는 catch 로 가므로 여기까지 오면 저장된 것이다.
        document.dispatchEvent(new CustomEvent('time-blocks-saved', {
            detail: { date: date, slotIndexes: slotIndexes },
        }));

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

let isDeleting = false;

const deleteSlot = async () => {
    if (isDeleting) return;

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

    isDeleting = true;
    let result;
    try {
        const date = document.getElementById('dateSelector').value;

        result = await apiCall('/api/time-blocks/', {
            method: 'DELETE',
            data: {
                slot_indexes: filledSlots,
                date: date
            }
        });
    } catch (error) {
        showNotification(interpolate(gettext('삭제 실패: %s'), [error.message]), 'error');
        console.error('Delete error:', error);
        return;
    } finally {
        isDeleting = false;
    }

    try {
        renderRows(result.runs);
        renderDayStats(result.stats);
        // 닫기를 선택 해제보다 먼저 한다. closeQuickInputSheet 는 남아 있는
        // 선택으로 포커스를 되돌릴 칸을 찾는데, 순서가 뒤집히면 되돌릴 칸이
        // 없어 포커스가 시트 안에 남은 채 aria-hidden 이 걸린다.
        closeQuickInputSheet();
        clearSelection();
        updateButtons();
        showUndoSnackbar(result.message, result.undo_token);
    } catch (error) {
        console.error('Delete render error:', error);
        showNotification(
            gettext('삭제되었지만 화면을 새로고침하지 못했습니다. 페이지를 새로고침해주세요.'),
            'warning',
            8000
        );
    }
};

