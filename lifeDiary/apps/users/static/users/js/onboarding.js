/**
 * 온보딩 화면 상호작용.
 *
 * STEP1 의 체크는 아무것도 저장하지 않는다. 고르지 않은 태그를 지우려면
 * 제품을 한 번도 못 본 사람에게 첫 화면부터 되돌릴 수 없는 삭제를 시키는
 * 셈이고, 순서만 바꾸려 해도 Tag.display_order 가 아직 없다. 지금은 무엇을
 * 쓸지 눈으로 확인하는 자리다.
 */
document.addEventListener('DOMContentLoaded', function () {
    initializePickCount();
    initializeAddTag();
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
