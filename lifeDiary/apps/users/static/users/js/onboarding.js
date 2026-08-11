/**
 * 온보딩 화면 상호작용.
 *
 * STEP1 의 체크는 아무것도 저장하지 않는다. 고르지 않은 태그를 지우려면
 * 제품을 한 번도 못 본 사람에게 첫 화면부터 되돌릴 수 없는 삭제를 시키는
 * 셈이고, 순서만 바꾸려 해도 Tag.display_order 가 아직 없다. 지금은 무엇을
 * 쓸지 눈으로 확인하는 자리다.
 */
const SAVED_KEY = 'onboarding.saved';

document.addEventListener('DOMContentLoaded', function () {
    initializePickCount();
    initializeAddTag();
    initializeStepTwo();
});

function initializePickCount() {
    const output = document.getElementById('onboardingCount');
    if (!output) return;

    const checks = Array.from(document.querySelectorAll('.chip__check'));
    const template = output.dataset.label || '__N__';

    const render = () => {
        const picked = checks.filter((check) => check.checked).length;
        output.textContent = template.replace('__N__', picked);
    };

    checks.forEach((check) => check.addEventListener('change', render));
    render();
}

function initializeAddTag() {
    const button = document.getElementById('onboardingAddTag');
    if (!button) return;

    button.addEventListener('click', function () {
        // 기록 화면과 같은 모달을 쓴다. 온보딩 전용 폼을 따로 만들면 이름
        // 길이·카테고리 필수 같은 규칙이 두 벌로 갈린다.
        window.openTagFormModal();
    });

    // 태그를 만들면 목록을 새로 그려야 체크 대상에 들어온다. 온보딩은
    // 부분 갱신을 할 만큼 복잡하지 않으므로 그냥 다시 읽는다.
    document.addEventListener('tags-updated', function () {
        window.location.reload();
    });
}


/**
 * STEP2 는 기록 화면의 그리드를 그대로 빌려 쓴다. 드래그·키보드·저장은
 * dashboard.js 한 곳에만 있고, 여기서는 온보딩에만 필요한 두 가지를 더한다 —
 * 아직 아무것도 고르지 않았을 때 다음으로 못 넘어가게 막고, 저장한 구간을
 * 기억해 STEP3 에서 무를 수 있게 한다.
 */
function initializeStepTwo() {
    const saveButton = document.getElementById('saveBtn');
    const grid = document.getElementById('timeGrid');
    if (!saveButton || !grid) return;

    document.addEventListener('time-blocks-saved', function (event) {
        rememberSavedSlots(event.detail);
        window.location.href = '?step=3';
    });
}

function rememberSavedSlots(detail) {
    if (!detail || !detail.slotIndexes || !detail.slotIndexes.length) return;

    // 세션 저장소를 쓰는 이유는 되돌리기 토큰의 수명이 60초뿐이라서다.
    // STEP3 에서 잠깐 머뭇거리면 토큰이 만료돼 무를 방법이 사라진다.
    try {
        window.sessionStorage.setItem(SAVED_KEY, JSON.stringify({
            date: detail.date,
            slotIndexes: detail.slotIndexes,
        }));
    } catch (error) {
        // 시크릿 모드 등에서 막히면 취소 링크만 못 보여 줄 뿐 기록은 남는다.
        console.warn(error);
    }
}
