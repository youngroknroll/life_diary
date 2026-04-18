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

    // 목표 추가 폼 중복 제출 방지
    const goalForm = document.querySelector('form[method="post"]');
    if (goalForm) {
        goalForm.addEventListener('submit', function() {
            const submitBtn = goalForm.querySelector('button[type="submit"]');
            if (!submitBtn || submitBtn.disabled) return;

            submitBtn.disabled = true;
            submitBtn.innerHTML =
                '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>저장 중...';
        });
    }
});
