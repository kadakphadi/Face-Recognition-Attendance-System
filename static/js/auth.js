// static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {

    const loginForm = document.getElementById('loginForm');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const toggleBtn = document.getElementById('togglePasswordBtn');

    // --------------------------------------------------
    // 1. Password Show / Hide Toggle
    // --------------------------------------------------
    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', () => {
            const isHidden = passwordInput.type === 'password';
            passwordInput.type = isHidden ? 'text' : 'password';

            const icon = document.getElementById('toggleIcon');
            if (icon) {
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            }
        });
    }

    // --------------------------------------------------
    // 2. Login Button Loading State
    // ✅ Uses textContent not innerHTML
    // --------------------------------------------------
    if (loginForm && loginBtn) {
        loginForm.addEventListener('submit', () => {

            loginBtn.disabled = true;

            // ✅ Clear and rebuild button safely
            loginBtn.textContent = '';

            const spinner = document.createElement('span');
            spinner.className = 'spinner-border spinner-border-sm me-2';
            spinner.setAttribute('role', 'status');

            loginBtn.appendChild(spinner);
            loginBtn.appendChild(
                document.createTextNode('Authenticating...')
            );

            // ✅ Auto restore if server slow
            setTimeout(() => {
                if (loginBtn.disabled) {
                    loginBtn.disabled = false;
                    loginBtn.textContent = '';

                    const icon = document.createElement('i');
                    icon.className = 'fas fa-sign-in-alt ms-2';

                    loginBtn.appendChild(
                        document.createTextNode('Login ')
                    );
                    loginBtn.appendChild(icon);
                }
            }, 6000);
        });
    }

    // --------------------------------------------------
    // 3. Client-side Validation
    // --------------------------------------------------
    const inputs = document.querySelectorAll('.form-control');

    inputs.forEach(input => {
        input.addEventListener('blur', () => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });

        input.addEventListener('input', () => {
            if (input.classList.contains('is-invalid') &&
                input.value.trim()) {
                input.classList.remove('is-invalid');
            }
        });
    });

});