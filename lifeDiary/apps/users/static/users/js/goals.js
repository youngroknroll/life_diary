/**
 * 목표 관리 — 인라인 편집 · 추가 · 행 안 삭제 확인 · 되돌리기.
 *
 * 모든 동작은 그 자체로 동작하는 POST 폼이고 이 파일은 그 위에 얹는 향상
 * 레이어다. JS 가 없으면 저장 버튼이 늘 보이고, 삭제는 확인 화면으로 간다.
 *
 * 서버가 늦을 수 있으므로 왕복하는 모든 버튼은 스피너 + disabled + aria-busy
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
    let statusTimer = null;
    let snackbarTimer = null;
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
        if (kind !== 'error') {
            statusTimer = setTimeout(function () {
                statusEl.textContent = '';
            }, 2600);
        }
    }

    function lock(button) {
        if (!button) return function () {};
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');
        button.classList.add('is-busy');
        return function unlock() {
            button.disabled = false;
            button.removeAttribute('aria-busy');
            button.classList.remove('is-busy');
        };
    }

    function hideSnackbar() {
        clearTimeout(snackbarTimer);
        if (snackbar) snackbar.hidden = true;
    }

    function showSnackbar(text, restore) {
        if (!snackbar || !undoForm) return;
        snackbarText.textContent = text;
        undoForm.querySelector('[name="tag"]').value = restore.tag;
        undoForm.querySelector('[name="period"]').value = restore.period;
        undoForm.querySelector('[name="target_hours"]').value = restore.hours;
        snackbar.hidden = false;
        clearTimeout(snackbarTimer);
        snackbarTimer = setTimeout(hideSnackbar, 8000);
    }

    /** 응답 본문으로 진행률과 표를 통째로 갈아끼운다. 목표가 바뀌면 진행률도
     *  같이 낡으므로 둘을 따로 갱신하지 않는다. */
    function swapBody(html) {
        block.innerHTML = html;
        const manager = block.querySelector('#goalManager');
        if (countEl && manager && manager.dataset.countLabel) {
            countEl.textContent = manager.dataset.countLabel;
        }
        bind();
    }

    async function submitForm(form, button, options) {
        if (busy) return;
        const action = options.action || form.action;
        busy = true;
        const unlock = lock(button);
        setStatus(gettext('처리 중...'));

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

            const html = await response.text();
            if (response.ok) {
                swapBody(html);
                setStatus(options.successMessage);
                if (options.onSuccess) options.onSuccess();
                return;
            }
            if (response.status === 422) {
                // 서버가 오류 문구를 심은 본문을 그대로 돌려준다.
                swapBody(html);
                setStatus('', 'error');
                return;
            }
            throw new Error('HTTP ' + response.status);
        } catch (error) {
            setStatus(
                gettext('처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'),
                'error'
            );
        } finally {
            busy = false;
            unlock();
        }
    }

    function currentValues(form) {
        return [
            form.elements.tag.value,
            form.elements.period.value,
            String(form.elements.target_hours.value).trim(),
        ].join('|');
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
        const clean = currentValues(form);

        // JS 가 붙은 뒤에는 바뀐 행에만 저장 버튼을 보인다. 없는 환경에서는
        // 늘 보이는 채로 남는다.
        save.hidden = true;

        function refreshDirty() {
            const dirty = currentValues(form) !== clean;
            form.classList.toggle('is-dirty', dirty);
            save.hidden = !dirty;
        }

        form.addEventListener('input', refreshDirty);
        form.addEventListener('change', function (event) {
            if (event.target === form.elements.tag) paintSwatch(form);
            if (event.target === form.elements.period) applyPeriodMax(form);
            refreshDirty();
        });

        deleteLink.addEventListener('click', function (event) {
            event.preventDefault();
            askDelete(form);
        });

        applyPeriodMax(form);

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            const submitter = event.submitter;
            if (submitter && submitter.dataset.goalAction === 'delete') {
                confirmDeleteRow(form, submitter);
                return;
            }
            submitForm(form, save, {
                successMessage: gettext('목표를 저장했습니다'),
            });
        });
    }

    /** 삭제 확인을 행 안에서 받는다 — 별도 화면으로 나가면 표에서의 맥락이 끊긴다. */
    function askDelete(form) {
        if (form.classList.contains('is-confirming')) return;
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
        yes.focus();
    }

    function confirmDeleteRow(form, button) {
        const restore = {
            tag: form.elements.tag.value,
            period: form.elements.period.value,
            hours: form.elements.target_hours.value,
        };
        const deletedLabel = form.dataset.goalDeletedLabel;

        submitForm(form, button, {
            action: form.dataset.deleteUrl,
            successMessage: '',
            onSuccess: function () {
                showSnackbar(deletedLabel, restore);
            },
        });
    }

    function bindAddForm(form) {
        const submit = form.querySelector('.goal-add__submit');

        form.addEventListener('change', function (event) {
            if (event.target === form.elements.tag) paintSwatch(form);
            if (event.target === form.elements.period) applyPeriodMax(form);
        });

        applyPeriodMax(form);

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            if (!form.reportValidity()) return;
            submitForm(form, submit, {
                successMessage: gettext('목표를 추가했습니다'),
            });
        });
    }

    function bind() {
        block.querySelectorAll('.goal-row').forEach(bindRow);
        const addForm = block.querySelector('#goalAddForm');
        if (addForm) bindAddForm(addForm);
    }

    if (undoForm) {
        undoForm.addEventListener('submit', function (event) {
            event.preventDefault();
            submitForm(undoForm, undoForm.querySelector('.goal-snackbar__undo'), {
                successMessage: gettext('삭제를 되돌렸습니다'),
                onSuccess: hideSnackbar,
            });
        });
    }

    bind();
})();
