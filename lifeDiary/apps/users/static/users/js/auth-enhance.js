(function () {
    'use strict';

    // Relies on Django JavaScriptCatalog (base.html line 187) for global gettext().

    function makeToggleButton(input) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-toggle';
        btn.setAttribute('aria-label', gettext('비밀번호 표시'));
        btn.setAttribute('aria-pressed', 'false');
        btn.textContent = gettext('표시');

        btn.addEventListener('click', () => {
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            btn.setAttribute('aria-pressed', String(!showing));
            btn.setAttribute('aria-label', showing ? gettext('비밀번호 표시') : gettext('비밀번호 숨기기'));
            btn.textContent = showing ? gettext('표시') : gettext('숨기기');
        });

        return btn;
    }

    function makeCapsWarning() {
        const el = document.createElement('div');
        el.className = 'caps-lock-warning';
        el.setAttribute('role', 'status');
        el.hidden = true;
        el.textContent = gettext('Caps Lock이 켜져 있습니다');
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

    // A failed submit re-renders the whole page, so focus would otherwise sit at
    // the document top and the user would never hear why the attempt failed.
    function focusFirstInvalid() {
        const field = document.querySelector('.auth-card [aria-invalid="true"]');
        if (!field) return;
        field.focus({ preventScroll: false });
        if (typeof field.select === 'function' && field.type !== 'checkbox') {
            field.select();
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const inputs = document.querySelectorAll('.auth-card input[type="password"]');
        inputs.forEach(enhance);
        focusFirstInvalid();
    });
})();
