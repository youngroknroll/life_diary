(function () {
    'use strict';

    const T = (typeof gettext === 'function') ? gettext : (s) => s;

    function makeToggleButton(input) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-toggle';
        btn.setAttribute('aria-label', T('비밀번호 표시'));
        btn.setAttribute('aria-pressed', 'false');
        btn.tabIndex = -1;
        btn.innerHTML = '<i class="fas fa-eye" aria-hidden="true"></i>';

        btn.addEventListener('click', () => {
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            btn.setAttribute('aria-pressed', String(!showing));
            btn.setAttribute('aria-label', showing ? T('비밀번호 표시') : T('비밀번호 숨기기'));
            btn.querySelector('i').className = showing ? 'fas fa-eye' : 'fas fa-eye-slash';
        });

        return btn;
    }

    function makeCapsWarning() {
        const el = document.createElement('div');
        el.className = 'caps-lock-warning';
        el.setAttribute('role', 'status');
        el.hidden = true;
        el.innerHTML = '<i class="fas fa-arrow-up" aria-hidden="true"></i> ' + T('Caps Lock이 켜져 있습니다');
        return el;
    }

    function enhance(input) {
        if (input.dataset.enhanced === '1') return;
        input.dataset.enhanced = '1';

        const wrapper = document.createElement('div');
        wrapper.className = 'password-field';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        wrapper.appendChild(makeToggleButton(input));

        const caps = makeCapsWarning();
        wrapper.parentNode.insertBefore(caps, wrapper.nextSibling);

        const checkCaps = (e) => {
            if (typeof e.getModifierState !== 'function') return;
            caps.hidden = !e.getModifierState('CapsLock');
        };
        input.addEventListener('keydown', checkCaps);
        input.addEventListener('keyup', checkCaps);
        input.addEventListener('blur', () => { caps.hidden = true; });
    }

    document.addEventListener('DOMContentLoaded', () => {
        const inputs = document.querySelectorAll('.auth-card input[type="password"]');
        inputs.forEach(enhance);
    });
})();
