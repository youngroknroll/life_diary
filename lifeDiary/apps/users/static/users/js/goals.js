/**
 * 목표 관리 — 인라인 편집 · 추가 · 행 안 삭제 확인 · 되돌리기.
 *
 * 모든 동작은 그 자체로 동작하는 POST 폼이고 이 파일은 그 위에 얹는 향상
 * 레이어다. JS 가 없으면 저장 버튼이 늘 보이고, 삭제는 확인 화면으로 간다.
 *
 * 서버가 늦을 수 있으므로 왕복하는 모든 버튼은 스피너 + aria-disabled + aria-busy
 * 로 잠기고, 성공·실패·예외 어느 경로로든 반드시 풀린다.
 */
(function () {
    const block = document.getElementById('goalManagerBlock');
    if (!block) return;

    const statusEl = document.getElementById('goalSaveStatus');
    const countEl = document.getElementById('goalCount');
    const snackbar = document.getElementById('goalSnackbar');
    const snackbarText = document.getElementById('goalSnackbarText');
    const undoForm = document.getElementById('goalUndoForm');

    const PERIOD_MAX = { daily: 24, weekly: 100, monthly: 300 };
    const INVALID_GROUPS = {
        tag: ['tag', 'period'],
        period: ['tag', 'period', 'target_hours'],
        target_hours: ['target_hours'],
        due_date: ['due_date'],
        no_due_date: ['due_date'],
    };
    const cleanValues = new WeakMap();
    let statusTimer = null;
    let snackbarTimer = null;
    let snackbarHidePending = false;
    let busy = false;

    function setStatus(message, kind) {
        if (!statusEl) return;
        clearTimeout(statusTimer);
        if (!message) {
            statusEl.textContent = '';
            return;
        }
        const pill = document.createElement('span');
        pill.className = 'goal-status__pill' + (kind === 'error' ? ' is-error' : '');
        pill.textContent = message;
        statusEl.replaceChildren(pill);
        if (!kind) {
            statusTimer = setTimeout(function () {
                statusEl.textContent = '';
            }, 2600);
        }
    }

    function lock(button) {
        if (!button) return function () {};
        button.setAttribute('aria-disabled', 'true');
        button.setAttribute('aria-busy', 'true');
        button.classList.add('is-busy');
        return function unlock() {
            button.removeAttribute('aria-disabled');
            button.removeAttribute('aria-busy');
            button.classList.remove('is-busy');
        };
    }

    function submitButtons() {
        const buttons = Array.from(block.querySelectorAll('button[type="submit"]'));
        if (undoForm) buttons.push(undoForm.querySelector('.goal-snackbar__undo'));
        return buttons;
    }

    function lockOthers(button) {
        submitButtons().forEach(function (control) {
            if (control === button) return;
            if (control === document.activeElement && button) button.focus();
            control.disabled = true;
        });
    }

    function unlockAll() {
        submitButtons().forEach(function (control) {
            control.disabled = false;
        });
    }

    function focusAddTag() {
        const select = block.querySelector('#goalAddTag');
        if (select) select.focus();
    }

    function focusInvalid() {
        const invalid = block.querySelector('[aria-invalid="true"]');
        if (invalid) invalid.focus();
    }

    function focusRow(goalId, name) {
        const row = block.querySelector('.goal-row[data-goal-id="' + goalId + '"]');
        if (!row) return;
        const control = name ? row.elements[name] : null;
        if (control && !control.disabled) {
            control.focus();
            return;
        }
        row.elements.tag.focus();
    }

    function focusRestoredRow() {
        const tag = undoForm.elements.tag.value;
        const period = undoForm.elements.period.value;
        const row = Array.from(block.querySelectorAll('.goal-row')).find(function (form) {
            return form.elements.tag.value === tag && form.elements.period.value === period;
        });
        if (row) {
            row.elements.tag.focus();
            return;
        }
        focusAddTag();
    }

    function cancelSnackbarHide() {
        clearTimeout(snackbarTimer);
        snackbarHidePending = false;
    }

    function hideSnackbar() {
        cancelSnackbarHide();
        if (!snackbar) return;
        if (snackbar.contains(document.activeElement)) focusAddTag();
        snackbar.hidden = true;
    }

    function showSnackbar(text, restore) {
        if (!snackbar || !undoForm) return;
        snackbarText.textContent = text;
        undoForm.querySelector('[name="tag"]').value = restore.tag;
        undoForm.querySelector('[name="period"]').value = restore.period;
        undoForm.querySelector('[name="target_hours"]').value = restore.hours;
        undoForm.querySelector('[name="due_date"]').value = restore.dueDate;
        undoForm.querySelector('[name="no_due_date"]').disabled = Boolean(restore.dueDate);
        snackbar.hidden = false;
        scheduleSnackbarHide();
    }

    function hideSnackbarWhenIdle() {
        if (busy) {
            snackbarHidePending = true;
            return;
        }
        hideSnackbar();
    }

    function scheduleSnackbarHide() {
        cancelSnackbarHide();
        snackbarTimer = setTimeout(hideSnackbarWhenIdle, 8000);
    }

    /** 응답 본문으로 진행률과 표를 통째로 갈아끼운다. 목표가 바뀌면 진행률도
     *  같이 낡으므로 둘을 따로 갱신하지 않는다. */
    function swapBody(html, submitted) {
        const drafts = collectDrafts(submitted);
        block.innerHTML = html;
        const manager = block.querySelector('#goalManager');
        if (countEl && manager && manager.dataset.countLabel) {
            countEl.textContent = manager.dataset.countLabel;
        }
        bind();
        restoreDrafts(drafts);
    }

    async function request(action, form) {
        try {
            const response = await fetch(action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                credentials: 'same-origin',
            });
            return { ok: response.ok, status: response.status, html: await response.text() };
        } catch (error) {
            return { ok: false, status: 0, html: '' };
        }
    }

    async function submitForm(form, button, options) {
        if (busy) return;
        busy = true;
        const unlock = lock(button);
        lockOthers(button);
        setStatus(gettext('처리 중...'), 'pending');

        const outcome = await request(options.action || form.action, form);

        busy = false;
        unlock();
        unlockAll();
        if (snackbarHidePending) scheduleSnackbarHide();

        if (outcome.ok) {
            swapBody(outcome.html, form);
            setStatus(options.successMessage);
            if (options.onSuccess) options.onSuccess();
            return;
        }
        if (outcome.status === 422) {
            // 서버가 오류 문구를 심은 본문을 그대로 돌려준다.
            swapBody(outcome.html, form);
            setStatus('', 'error');
            focusInvalid();
            return;
        }
        setStatus(
            gettext('처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'),
            'error'
        );
        if (document.activeElement === document.body && button && button.isConnected) {
            button.focus();
        }
    }

    function readValues(form) {
        return {
            tag: form.elements.tag.value,
            period: form.elements.period.value,
            target_hours: String(form.elements.target_hours.value).trim(),
            due_date: form.elements.due_date.value,
            no_due_date: form.elements.no_due_date.checked,
        };
    }

    function serializeValues(values) {
        return [
            values.tag,
            values.period,
            values.target_hours,
            values.due_date,
            values.no_due_date ? '1' : '0',
        ].join('|');
    }

    function emptyAddValues(form) {
        return {
            tag: '',
            period: form.elements.period.options[0].value,
            target_hours: '',
            due_date: '',
            no_due_date: true,
        };
    }

    function isDirty(form) {
        return serializeValues(readValues(form)) !== cleanValues.get(form);
    }

    function refreshDirty(form) {
        const save = form.querySelector('.goal-row__save');
        if (!save) return;
        const dirty = isDirty(form);
        form.classList.toggle('is-dirty', dirty);
        save.hidden = !dirty;
    }

    function writeValues(form, values) {
        form.elements.tag.value = values.tag;
        form.elements.period.value = values.period;
        form.elements.target_hours.value = values.target_hours;
        form.elements.due_date.value = values.due_date;
        form.elements.no_due_date.checked = values.no_due_date;
        paintSwatch(form);
        applyPeriodMax(form);
        syncDueDate(form);
        refreshDirty(form);
    }

    function collectDrafts(submitted) {
        return Array.from(block.querySelectorAll('.goal-row, #goalAddForm'))
            .filter(function (form) { return form !== submitted; })
            .map(function (form) {
                return {
                    goalId: form.dataset.goalId || '',
                    values: isDirty(form) ? readValues(form) : null,
                    confirming: form.classList.contains('is-confirming'),
                };
            })
            .filter(function (draft) { return draft.values || draft.confirming; });
    }

    function findForm(goalId) {
        if (!goalId) return block.querySelector('#goalAddForm');
        return block.querySelector('.goal-row[data-goal-id="' + goalId + '"]');
    }

    function restoreDrafts(drafts) {
        drafts.forEach(function (draft) {
            const form = findForm(draft.goalId);
            if (!form) return;
            if (draft.values) writeValues(form, draft.values);
            if (draft.confirming) openConfirm(form);
        });
    }

    function clearInvalid(form, control) {
        const names = INVALID_GROUPS[control.name];
        if (!names) return;
        names.forEach(function (name) {
            form.elements[name].removeAttribute('aria-invalid');
            form.elements[name].removeAttribute('aria-describedby');
        });
        if (form.querySelector('[aria-invalid="true"]')) return;
        const error = form.querySelector('.goal-row__error');
        if (error) error.remove();
        const hint = form.querySelector('.goal-add__hint');
        if (hint) hint.hidden = false;
    }

    function syncDueDate(form) {
        form.elements.due_date.disabled = form.elements.no_due_date.checked;
    }

    function toggleDueDate(form) {
        syncDueDate(form);
        if (!form.elements.no_due_date.checked) form.elements.due_date.focus();
    }

    function paintSwatch(form) {
        const swatch = form.querySelector('[data-goal-swatch]');
        const option = form.elements.tag.selectedOptions[0];
        if (!swatch) return;
        const color = option ? option.dataset.color : '';
        swatch.style.backgroundColor = color || 'transparent';
    }

    function applyPeriodMax(form) {
        const max = PERIOD_MAX[form.elements.period.value];
        if (max) form.elements.target_hours.max = max;
    }

    function bindRow(form) {
        const save = form.querySelector('.goal-row__save');
        const deleteLink = form.querySelector('.goal-row__delete');
        cleanValues.set(form, serializeValues(readValues(form)));

        // JS 가 붙은 뒤에는 바뀐 행에만 저장 버튼을 보인다. 없는 환경에서는
        // 늘 보이는 채로 남는다.
        save.hidden = true;

        form.addEventListener('input', function (event) {
            clearInvalid(form, event.target);
            refreshDirty(form);
        });
        form.addEventListener('change', function (event) {
            if (event.target === form.elements.tag) paintSwatch(form);
            if (event.target === form.elements.period) applyPeriodMax(form);
            if (event.target === form.elements.no_due_date) toggleDueDate(form);
            clearInvalid(form, event.target);
            refreshDirty(form);
        });

        deleteLink.addEventListener('click', function (event) {
            event.preventDefault();
            askDelete(form);
        });

        applyPeriodMax(form);
        syncDueDate(form);

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            const submitter = event.submitter;
            if (submitter && submitter.dataset.goalAction === 'delete') {
                confirmDeleteRow(form, submitter);
                return;
            }
            const goalId = form.dataset.goalId;
            const focusedName = form.contains(document.activeElement)
                ? document.activeElement.name || ''
                : '';
            submitForm(form, save, {
                successMessage: gettext('목표를 저장했습니다'),
                onSuccess: function () {
                    focusRow(goalId, focusedName);
                },
            });
        });
    }

    /** 삭제 확인을 행 안에서 받는다 — 별도 화면으로 나가면 표에서의 맥락이 끊긴다. */
    function openConfirm(form) {
        if (form.classList.contains('is-confirming')) return null;
        form.classList.add('is-confirming');

        const text = document.createElement('span');
        text.className = 'goal-confirm__text';
        text.textContent = form.dataset.goalLabel;

        const actions = document.createElement('span');
        actions.className = 'goal-confirm__actions';

        const yes = document.createElement('button');
        yes.type = 'submit';
        yes.className = 'btn-sian goal-confirm__yes';
        yes.formAction = form.dataset.deleteUrl;
        yes.formNoValidate = true;
        yes.dataset.goalAction = 'delete';
        yes.textContent = gettext('삭제');
        yes.disabled = busy;

        const no = document.createElement('button');
        no.type = 'button';
        no.className = 'btn-sian goal-confirm__no';
        no.textContent = gettext('취소');
        no.addEventListener('click', function () {
            form.classList.remove('is-confirming');
            form.querySelectorAll('.goal-confirm__text, .goal-confirm__actions')
                .forEach(function (node) { node.remove(); });
            form.querySelector('.goal-row__delete').focus();
        });

        actions.append(yes, no);
        form.append(text, actions);
        return { yes: yes, no: no };
    }

    function askDelete(form) {
        const confirm = openConfirm(form);
        if (!confirm) return;
        (confirm.yes.disabled ? confirm.no : confirm.yes).focus();
    }

    function confirmDeleteRow(form, button) {
        const restore = {
            tag: form.elements.tag.value,
            period: form.elements.period.value,
            hours: form.elements.target_hours.value,
            dueDate: form.elements.no_due_date.checked ? '' : form.elements.due_date.value,
        };
        const deletedLabel = form.dataset.goalDeletedLabel;

        submitForm(form, button, {
            action: form.dataset.deleteUrl,
            successMessage: '',
            onSuccess: function () {
                showSnackbar(deletedLabel, restore);
                undoForm.querySelector('.goal-snackbar__undo').focus();
            },
        });
    }

    function bindAddForm(form) {
        const submit = form.querySelector('.goal-add__submit');
        cleanValues.set(form, serializeValues(emptyAddValues(form)));

        form.addEventListener('input', function (event) {
            clearInvalid(form, event.target);
        });
        form.addEventListener('change', function (event) {
            if (event.target === form.elements.tag) paintSwatch(form);
            if (event.target === form.elements.period) applyPeriodMax(form);
            if (event.target === form.elements.no_due_date) toggleDueDate(form);
            clearInvalid(form, event.target);
        });

        paintSwatch(form);
        applyPeriodMax(form);
        syncDueDate(form);

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            if (!form.reportValidity()) return;
            submitForm(form, submit, {
                successMessage: gettext('목표를 추가했습니다'),
                onSuccess: focusAddTag,
            });
        });
    }

    function bind() {
        block.querySelectorAll('.goal-row').forEach(bindRow);
        const addForm = block.querySelector('#goalAddForm');
        if (addForm) bindAddForm(addForm);
    }

    if (undoForm) {
        undoForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            if (busy) return;
            cancelSnackbarHide();
            await submitForm(undoForm, undoForm.querySelector('.goal-snackbar__undo'), {
                successMessage: gettext('삭제를 되돌렸습니다'),
                onSuccess: function () {
                    focusRestoredRow();
                    hideSnackbar();
                },
            });
            if (!snackbar.hidden) scheduleSnackbarHide();
        });
    }

    bind();
})();
