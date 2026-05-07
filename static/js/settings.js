// static/js/settings.js

document.addEventListener('DOMContentLoaded', () => {

    // --------------------------------------------------
    // 1. Enable promote button only when PROMOTE typed
    // --------------------------------------------------
    const confirmPromote = document.getElementById('confirmPromote');
    const promoteBtn = document.getElementById('promoteBtn');

    if (confirmPromote && promoteBtn) {
        confirmPromote.addEventListener('input', function () {
            promoteBtn.disabled = this.value !== 'PROMOTE';
        });
    }

    // --------------------------------------------------
    // 2. Enable clear button only when CLEAR typed
    // --------------------------------------------------
    const confirmClear = document.getElementById('confirmClear');
    const clearBtn = document.getElementById('clearBtn');

    if (confirmClear && clearBtn) {
        confirmClear.addEventListener('input', function () {
            clearBtn.disabled = this.value !== 'CLEAR';
        });
    }

    // --------------------------------------------------
    // 3. Live password match check
    // --------------------------------------------------
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    const passError = document.getElementById('passError');

    if (confirmPassword && newPassword && passError) {
        confirmPassword.addEventListener('input', function () {
            if (this.value && this.value !== newPassword.value) {
                passError.classList.remove('d-none');
            } else {
                passError.classList.add('d-none');
            }
        });
    }

    // --------------------------------------------------
    // 4. Password strength indicator
    // --------------------------------------------------
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');

    if (newPassword && strengthBar && strengthText) {
        newPassword.addEventListener('input', function () {
            const val = this.value;
            let strength = 0;

            if (val.length >= 8) strength++;
            if (/[A-Z]/.test(val)) strength++;
            if (/[a-z]/.test(val)) strength++;
            if (/\d/.test(val)) strength++;
            if (/[^a-zA-Z0-9]/.test(val)) strength++;

            const levels = [
                { width: '0%',   color: '',           label: '' },
                { width: '25%',  color: 'bg-danger',  label: 'Weak' },
                { width: '50%',  color: 'bg-warning', label: 'Fair' },
                { width: '75%',  color: 'bg-info',    label: 'Good' },
                { width: '100%', color: 'bg-success', label: 'Strong' },
                { width: '100%', color: 'bg-success', label: 'Very Strong' }
            ];

            const level = levels[strength] || levels[0];
            strengthBar.style.width = level.width;
            strengthBar.className = `progress-bar ${level.color}`;
            // ✅ textContent not innerHTML
            strengthText.textContent = level.label;
        });
    }

    // --------------------------------------------------
    // 5. Prevent double submit on password form
    // --------------------------------------------------
    const passwordForm = document.getElementById('passwordForm');
    const pwdSubmitBtn = document.getElementById('pwdSubmitBtn');

    if (passwordForm && pwdSubmitBtn) {
        passwordForm.addEventListener('submit', function (e) {
            const pwd = newPassword ? newPassword.value : '';
            const conf = confirmPassword ? confirmPassword.value : '';

            if (pwd !== conf) {
                e.preventDefault();
                if (passError) passError.classList.remove('d-none');
                return false;
            }

            pwdSubmitBtn.disabled = true;

            // ✅ Safe DOM manipulation — no innerHTML
            pwdSubmitBtn.textContent = '';
            const icon = document.createElement('i');
            icon.className = 'fas fa-spinner fa-spin me-1';
            pwdSubmitBtn.appendChild(icon);
            pwdSubmitBtn.appendChild(
                document.createTextNode(' Updating...')
            );
        });
    }

    // --------------------------------------------------
    // 6. ✅ Holiday delete confirmation
    // Uses data-reason attribute — no inline JS interpolation
    // --------------------------------------------------
    document.querySelectorAll('.delete-holiday-form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            // ✅ Read reason from data attribute safely
            const reason = this.dataset.reason || 'this holiday';

            if (confirm(`Remove holiday: ${reason}?`)) {
                this.submit();
            }
        });
    });

});