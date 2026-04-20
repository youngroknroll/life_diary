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
    targetHoursInput.placeholder = `최대 ${maxValue}시간까지 입력 가능`;
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

        goalForm.addEventListener('submit', async function(e) {
            const submitBtn = goalForm.querySelector('button[type="submit"]');
            if (!submitBtn || submitBtn.disabled) return;

            e.preventDefault();
            submitBtn.disabled = true;
            if (statusEl) {
                statusEl.classList.remove('text-success', 'text-danger');
                statusEl.classList.add('text-muted');
                statusEl.textContent = '저장중...';
            }

            const formData = new FormData(goalForm);
            const csrfToken = formData.get('csrfmiddlewaretoken');

            try {
                const postRes = await fetch(goalForm.action || window.location.pathname, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken,
                    },
                    body: formData,
                    credentials: 'same-origin',
                });

                if (postRes.status === 204) {
                    const partialRes = await fetch(partialUrl, {
                        headers: { 'X-Requested-With': 'XMLHttpRequest' },
                        credentials: 'same-origin',
                    });
                    if (!partialRes.ok) throw new Error('partial fetch failed');
                    listBlock.innerHTML = await partialRes.text();

                    goalForm.reset();
                    updateTargetHoursMax();

                    if (statusEl) {
                        statusEl.classList.remove('text-muted', 'text-danger');
                        statusEl.classList.add('text-success');
                        statusEl.textContent = '저장완료!';
                    }
                    resetStatus(2500);
                } else {
                    let msg = '저장 실패';
                    try {
                        const data = await postRes.json();
                        if (data.errors) {
                            msg = Object.values(data.errors).flat().join(' / ');
                        }
                    } catch (_) {}
                    if (statusEl) {
                        statusEl.classList.remove('text-success', 'text-muted');
                        statusEl.classList.add('text-danger');
                        statusEl.textContent = msg;
                    }
                    resetStatus(4000);
                }
            } catch (err) {
                console.error('목표 저장 오류:', err);
                if (statusEl) {
                    statusEl.classList.remove('text-success', 'text-muted');
                    statusEl.classList.add('text-danger');
                    statusEl.textContent = '저장 실패 - 네트워크 오류';
                }
                resetStatus(4000);
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    if (statusEl && statusEl.textContent.trim() === '저장완료!') {
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
