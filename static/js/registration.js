// static/js/registration.js

document.addEventListener('DOMContentLoaded', () => {

    const form = document.getElementById('registrationForm');
    const submitBtn = document.getElementById('submitBtn');
    const alertContainer = document.getElementById('alertContainer');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        // ✅ Step 1: Stop camera stream so backend can use camera
        if (typeof stopCamera === 'function') stopCamera();
        showCaptureOverlay('Stopping stream...');

        // ✅ Step 2: Wait for camera to release
        await new Promise(resolve => setTimeout(resolve, 1500));

        // ✅ Step 3: Show countdown
        showCaptureOverlay('Preparing camera...');
        startCaptureCountdown();

        const formData = new FormData(form);

        try {
            const response = await fetch('/register_student', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            resetButton();
            hideCaptureOverlay();

            if (data.status === 'success') {
                showAlert('success', data.message);
                form.reset();

                // ✅ Restart camera after success
                setTimeout(() => {
                    if (typeof startCamera === 'function') startCamera();
                }, 2000);

            } else {
                showAlert('error', data.message);

                // ✅ Restart camera after error
                setTimeout(() => {
                    if (typeof startCamera === 'function') startCamera();
                }, 1000);
            }

        } catch (err) {
            resetButton();
            hideCaptureOverlay();
            showAlert('error', 'Network error. Please try again.');

            setTimeout(() => {
                if (typeof startCamera === 'function') startCamera();
            }, 1000);
        }
    });


    // --------------------------------------------------
    // Countdown During Capture
    // --------------------------------------------------
    function startCaptureCountdown() {
        let frames = 15;
        submitBtn.disabled = true;

        updateSubmitBtn(`Capturing... ${frames}`, 'fa-camera');

        const interval = setInterval(() => {
            frames--;

            // ✅ Update overlay message too
            if (typeof showCaptureOverlay === 'function') {
                showCaptureOverlay(`Capturing face... ${frames}`);
            }

            if (frames <= 0) {
                clearInterval(interval);
                updateSubmitBtn('Processing...', 'fa-spinner fa-spin');
                if (typeof showCaptureOverlay === 'function') {
                    showCaptureOverlay('Processing encoding...');
                }
            } else {
                updateSubmitBtn(
                    `Capturing... ${frames}`, 'fa-camera'
                );
            }
        }, 250);

        submitBtn.dataset.interval = interval;
    }


    // --------------------------------------------------
    // Update Button Safely
    // --------------------------------------------------
    function updateSubmitBtn(text, iconClass) {
        submitBtn.textContent = '';
        const icon = document.createElement('i');
        icon.className = `fas ${iconClass} me-2`;
        submitBtn.appendChild(icon);
        submitBtn.appendChild(document.createTextNode(text));
    }


    // --------------------------------------------------
    // Reset Button
    // --------------------------------------------------
    function resetButton() {
        if (submitBtn.dataset.interval) {
            clearInterval(parseInt(submitBtn.dataset.interval));
        }
        submitBtn.disabled = false;
        updateSubmitBtn('Capture & Register', 'fa-camera');
    }


    // --------------------------------------------------
    // Show Alert
    // --------------------------------------------------
    function showAlert(type, message) {
        if (!alertContainer) return;

        alertContainer.innerHTML = '';

        const alertClass = type === 'success'
            ? 'alert-success' : 'alert-danger';
        const iconClass = type === 'success'
            ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} reg-alert mt-3`;
        alertDiv.style.whiteSpace = 'pre-line';

        const icon = document.createElement('i');
        icon.className = `${iconClass} me-2`;
        alertDiv.appendChild(icon);
        alertDiv.appendChild(document.createTextNode(message));

        alertContainer.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 8000);
    }

});