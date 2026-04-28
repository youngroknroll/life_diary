/**
 * =================================================================================
 * 목표 관리 JavaScript
 * - 기간(daily/weekly/monthly)에 따른 목표 시간 최대값 자동 조절
 * =================================================================================
 */

function updateTargetHoursMax() {
    const periodSelect = document.querySelector('select[name="period"]');
    const targetHoursInput = document.querySelector('input[name="target_hours"]');

    if (!periodSelect || !targetHoursInput) return;

    const maxByPeriod = { daily: 24, weekly: 100, monthly: 300 };
    const maxValue = maxByPeriod[periodSelect.value] || 24;

    targetHoursInput.max = maxValue;
    targetHoursInput.placeholder = interpolate(
        gettext('최대 %s시간까지 입력 가능'),
        [maxValue]
    );
}

document.addEventListener('DOMContentLoaded', function() {
    updateTargetHoursMax();

    const periodSelect = document.querySelector('select[name="period"]');
    if (periodSelect) {
        periodSelect.addEventListener('change', updateTargetHoursMax);
    }

    // 목표 추가 폼: AJAX 제출 + partial 갱신 + 중복 제출 방지
    const goalForm = document.getElementById('goalAddForm');
    const statusEl = document.getElementById('goalSaveStatus');
    const listBlock = document.getElementById('goalListBlock');

    function resetStatus(delayMs) {
        if (!statusEl) return;
        setTimeout(function() {
            statusEl.textContent = '';
            statusEl.classList.remove('text-success', 'text-muted', 'text-danger');
        }, delayMs);
    }

    if (goalForm && listBlock) {
        const partialUrl = goalForm.dataset.partialUrl;

        function setStatus(text, kind) {
            if (!statusEl) return;
            statusEl.classList.remove('text-success', 'text-muted', 'text-danger');
            if (kind) statusEl.classList.add(kind);
            statusEl.textContent = text;
        }

        const ajaxHeaders = { 'X-Requested-With': 'XMLHttpRequest' };

        goalForm.addEventListener('submit', async function(e) {
            const submitBtn = goalForm.querySelector('button[type="submit"]');
            if (!submitBtn || submitBtn.disabled) return;

            e.preventDefault();
            submitBtn.disabled = true;
            setStatus(gettext('저장중...'), 'text-muted');

            try {
                await apiCall(goalForm.action || window.location.pathname, {
                    method: 'POST',
                    body: new FormData(goalForm),
                    headers: ajaxHeaders,
                    showLoading: false,
                });

                const partialHtml = await apiCall(partialUrl, {
                    headers: ajaxHeaders,
                    responseType: 'text',
                    showLoading: false,
                });
                listBlock.innerHTML = partialHtml;

                goalForm.reset();
                updateTargetHoursMax();

                setStatus(gettext('저장완료!'), 'text-success');
                resetStatus(2500);
            } catch (err) {
                console.error('목표 저장 오류:', err);
                let msg;
                if (err.data && err.data.errors) {
                    msg = Object.values(err.data.errors).flat().join(' / ');
                } else if (err.status) {
                    msg = gettext('저장 실패');
                } else {
                    msg = gettext('저장 실패 - 네트워크 오류');
                }
                setStatus(msg, 'text-danger');
                resetStatus(4000);
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    if (statusEl && statusEl.textContent.trim() === gettext('저장완료!')) {
        setTimeout(function() {
            statusEl.textContent = '';
            if (history.replaceState) {
                const url = new URL(window.location.href);
                url.searchParams.delete('saved');
                history.replaceState({}, '', url.toString());
            }
        }, 2500);
    }
});
