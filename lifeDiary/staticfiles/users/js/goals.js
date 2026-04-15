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
});
