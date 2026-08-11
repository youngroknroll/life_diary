// signup 폼 실시간 검증 (blur/input 시점).
// - username/email: 비동기 서버 조회 (300ms 디바운스)
// - password2: password1과 즉시 일치 비교
// - Bootstrap is-valid / is-invalid 토글 + 동적 피드백 메시지

(function () {
    'use strict';

    const form = document.getElementById('signupForm');
    if (!form) return;

    const CHECK_USERNAME_URL = form.dataset.checkUsernameUrl;
    const CHECK_EMAIL_URL = form.dataset.checkEmailUrl;
    const DEBOUNCE_MS = 300;

    const usernameInput = form.querySelector('input[name="username"]');
    const emailInput = form.querySelector('input[name="email"]');
    const password1Input = form.querySelector('input[name="password1"]');
    const password2Input = form.querySelector('input[name="password2"]');

    function fieldHost(input) {
        // password 인풋은 auth-enhance.js가 .password-field로 감싸므로
        // 피드백은 한 단계 위(.mb-3)에 부착해야 한다.
        return input.closest('.mb-3') || input.parentNode;
    }

    function ensureFeedback(input) {
        const host = fieldHost(input);
        let fb = host.querySelector(':scope > .realtime-feedback');
        if (!fb) {
            fb = document.createElement('div');
            fb.className = 'realtime-feedback';
            fb.setAttribute('role', 'status');
            fb.setAttribute('aria-live', 'polite');
            host.appendChild(fb);
        }
        return fb;
    }

    function setState(input, ok, message) {
        input.classList.remove('is-valid', 'is-invalid');
        const fb = ensureFeedback(input);
        if (message == null || message === '') {
            fb.textContent = '';
            fb.className = 'realtime-feedback';
            return;
        }
        if (ok) {
            input.classList.add('is-valid');
            fb.className = 'realtime-feedback valid-feedback d-block';
        } else {
            input.classList.add('is-invalid');
            fb.className = 'realtime-feedback invalid-feedback d-block';
        }
        fb.textContent = message;
    }

    function debounce(fn, ms) {
        let t;
        return function () {
            const args = arguments;
            const ctx = this;
            clearTimeout(t);
            t = setTimeout(function () { fn.apply(ctx, args); }, ms);
        };
    }

    async function fetchCheck(url, paramName, value) {
        const u = url + '?' + paramName + '=' + encodeURIComponent(value);
        try {
            const res = await fetch(u, {headers: {'Accept': 'application/json'}});
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            return null;
        }
    }

    // 동시 요청 race 방지: 최신 토큰의 응답만 반영
    let usernameToken = 0;
    let emailToken = 0;

    const checkUsername = debounce(async function () {
        const value = usernameInput.value.trim();
        if (!value) { setState(usernameInput, null, ''); return; }
        const myToken = ++usernameToken;
        const data = await fetchCheck(CHECK_USERNAME_URL, 'username', value);
        if (myToken !== usernameToken) return;
        if (data) setState(usernameInput, data.available, data.message);
    }, DEBOUNCE_MS);

    const checkEmail = debounce(async function () {
        const value = emailInput.value.trim();
        if (!value) { setState(emailInput, null, ''); return; }
        const myToken = ++emailToken;
        const data = await fetchCheck(CHECK_EMAIL_URL, 'email', value);
        if (myToken !== emailToken) return;
        if (data) setState(emailInput, data.available, data.message);
    }, DEBOUNCE_MS);

    function checkPasswordMatch() {
        const p1 = password1Input.value;
        const p2 = password2Input.value;
        if (!p2) { setState(password2Input, null, ''); return; }
        if (p1 === p2) {
            setState(password2Input, true, gettext('비밀번호가 일치합니다.'));
        } else {
            setState(password2Input, false, gettext('비밀번호가 일치하지 않습니다.'));
        }
    }

    // The form carries `novalidate`, so the checkbox's own `required` attribute
    // never fires. Without this guard the only thing stopping an unchecked
    // consent is a full server round trip.
    const consentInput = form.querySelector('input[name="consent"]');

    function consentError() {
        let node = document.getElementById(consentInput.id + '_error');
        if (!node) {
            node = document.createElement('div');
            node.id = consentInput.id + '_error';
            node.className = 'field-error';
            consentInput.closest('.form-check').appendChild(node);
        }
        return node;
    }

    function clearConsentError() {
        consentInput.removeAttribute('aria-invalid');
        consentInput.removeAttribute('aria-describedby');
        const node = document.getElementById(consentInput.id + '_error');
        if (node) node.textContent = '';
    }

    if (consentInput) {
        form.addEventListener('submit', function (event) {
            if (consentInput.checked) {
                clearConsentError();
                return;
            }
            event.preventDefault();
            const node = consentError();
            node.textContent = gettext('이용약관과 개인정보처리방침에 동의해야 가입할 수 있습니다.');
            consentInput.setAttribute('aria-invalid', 'true');
            consentInput.setAttribute('aria-describedby', node.id);
            consentInput.focus();
        });
        consentInput.addEventListener('change', function () {
            if (consentInput.checked) clearConsentError();
        });
    }

    if (usernameInput && CHECK_USERNAME_URL) {
        usernameInput.addEventListener('blur', checkUsername);
    }
    if (emailInput && CHECK_EMAIL_URL) {
        emailInput.addEventListener('blur', checkEmail);
    }
    if (password1Input && password2Input) {
        password2Input.addEventListener('input', checkPasswordMatch);
        password1Input.addEventListener('input', function () {
            if (password2Input.value) checkPasswordMatch();
        });
    }
})();
