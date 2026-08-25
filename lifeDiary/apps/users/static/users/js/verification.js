(() => {
    const pad = (value) => String(value).padStart(2, "0");

    const countDown = (seconds, onTick, onDone) => {
        let remaining = seconds;
        onTick(remaining);
        const timer = window.setInterval(() => {
            remaining -= 1;
            if (remaining <= 0) {
                window.clearInterval(timer);
                onDone();
                return;
            }
            onTick(remaining);
        }, 1000);
    };

    const announce = (message) => {
        const notice = document.querySelector(".auth-code__notice");
        if (notice) {
            notice.textContent = message;
        }
    };

    const startExpiry = (node) => {
        const seconds = Number(node.dataset.expiresIn || 0);
        const template = node.dataset.template || "";
        if (!seconds || !template) {
            return;
        }
        countDown(
            seconds,
            (remaining) => {
                const clock = `${Math.floor(remaining / 60)}:${pad(remaining % 60)}`;
                node.textContent = template.replace("{time}", clock);
            },
            () => {
                const expired = node.dataset.expiredText || "";
                node.textContent = expired;
                announce(expired);
            }
        );
    };

    const startResend = (button) => {
        const seconds = Number(button.dataset.resendIn || 0);
        const waiting = button.dataset.waiting || "";
        const label = button.dataset.label || button.textContent.trim();
        if (!seconds || !waiting) {
            return;
        }
        button.disabled = true;
        countDown(
            seconds,
            (remaining) => {
                button.textContent = waiting.replace("{seconds}", remaining);
            },
            () => {
                button.disabled = false;
                button.textContent = label;
            }
        );
    };

    const focusCode = () => {
        const field = document.querySelector(".auth-code-input");
        if (field) {
            field.focus();
        }
    };

    document.querySelectorAll("[data-expires-in]").forEach(startExpiry);
    document.querySelectorAll("[data-resend-in]").forEach(startResend);
    focusCode();
})();
