(function () {
    'use strict';

    // Relies on Django JavaScriptCatalog (base.html line 187) for global gettext().
    // Labels are evaluated at module load time so xgettext can extract them.
    const LEVELS = [
        { key: 'too-short', label: gettext('너무 짧음'), pct: 5,   cls: 'is-veryweak' },
        { key: 'weak',      label: gettext('약함'),       pct: 25,  cls: 'is-weak' },
        { key: 'fair',      label: gettext('보통'),       pct: 50,  cls: 'is-fair' },
        { key: 'good',      label: gettext('좋음'),       pct: 75,  cls: 'is-good' },
        { key: 'strong',    label: gettext('강함'),       pct: 100, cls: 'is-strong' },
    ];

    function score(pwd) {
        if (!pwd) return -1;
        if (pwd.length < 8) return 0;

        let points = 0;
        if (pwd.length >= 8)  points += 1;
        if (pwd.length >= 12) points += 1;
        if (pwd.length >= 16) points += 1;
        if (/[a-z]/.test(pwd)) points += 1;
        if (/[A-Z]/.test(pwd)) points += 1;
        if (/\d/.test(pwd))    points += 1;
        if (/[^A-Za-z0-9]/.test(pwd)) points += 1;
        if (/^(\d+|[a-zA-Z]+)$/.test(pwd)) points -= 1;
        if (/(.)\1\1/.test(pwd)) points -= 1;

        if (points <= 2) return 1;
        if (points <= 4) return 2;
        if (points <= 5) return 3;
        return 4;
    }

    function buildMeter() {
        const wrap = document.createElement('div');
        wrap.className = 'password-strength';
        wrap.hidden = true;
        wrap.innerHTML =
            '<div class="password-strength__bar" aria-hidden="true">' +
                '<div class="password-strength__fill"></div>' +
            '</div>' +
            '<div class="password-strength__label" aria-live="polite"></div>';
        return wrap;
    }

    function update(meter, input) {
        const s = score(input.value);
        if (s < 0) {
            meter.hidden = true;
            return;
        }
        meter.hidden = false;
        const level = LEVELS[s];
        const fill = meter.querySelector('.password-strength__fill');
        const label = meter.querySelector('.password-strength__label');

        LEVELS.forEach((l) => meter.classList.remove(l.cls));
        meter.classList.add(level.cls);
        fill.style.width = level.pct + '%';
        label.textContent = level.label;
        meter.setAttribute('data-level', level.key);
    }

    function attach(input) {
        if (input.dataset.strength === '1') return;
        input.dataset.strength = '1';

        const meter = buildMeter();
        const host = input.closest('.password-field') || input;
        host.parentNode.insertBefore(meter, host.nextSibling);

        input.addEventListener('input', () => update(meter, input));
    }

    document.addEventListener('DOMContentLoaded', () => {
        const inputs = document.querySelectorAll(
            '.auth-card input[type="password"][name="password1"]'
        );
        inputs.forEach(attach);
    });
})();
