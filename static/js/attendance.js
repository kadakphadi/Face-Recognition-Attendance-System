// static/js/attendance.js

document.addEventListener('DOMContentLoaded', () => {

    const videoStream = document.getElementById('video-stream');
    const statusLabel = document.getElementById('status-label');
    const cameraError = document.getElementById('camera-error');
    const logBox      = document.getElementById('attendance-logs');
    const countEl     = document.getElementById('present-count');

    // ✅ Track already logged students to avoid duplicate entries
    const loggedToday = new Set();


    // --------------------------------------------------
    // 1. Camera Stream
    // --------------------------------------------------
    // ✅ Start camera stream immediately — no delay
    if (videoStream) {
        const url = videoStream.dataset.url;
        videoStream.src = url + '?' + new Date().getTime();

        videoStream.onerror = () => {
            if (cameraError) {
                cameraError.classList.remove('d-none');
            }

            if (statusLabel) {
                // ✅ Safe — static string not user data
                statusLabel.innerHTML =
                    '<i class="fas fa-circle me-1" ' +
                    'style="font-size:8px"></i> Camera Error';
                statusLabel.className = 'badge bg-danger px-3 py-2';
            }

            addLog('system', 'Camera Error', 'Could not connect');
        };
    }

    // ✅ Stop camera on page leave
    window.addEventListener('beforeunload', () => {
        if (videoStream) videoStream.src = '';
        navigator.sendBeacon('/stop_camera');
    });


    // --------------------------------------------------
    // 2. Live Clock
    // --------------------------------------------------
    function updateClock() {
        const clockEl = document.getElementById('live-clock');
        if (!clockEl) return;

        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        clockEl.textContent = `${h}:${m}:${s}`;
    }
    setInterval(updateClock, 1000);
    updateClock();


    // --------------------------------------------------
    // 3. Fetch Today's Count
    // --------------------------------------------------
    function fetchTodayCount() {
        fetch('/api/today_count')
            .then(res => res.json())
            .then(data => {
                if (data.count !== undefined && countEl) {
                    countEl.textContent = data.count;
                }
            })
            .catch(() => {});
    }
    setInterval(fetchTodayCount, 5000);
    fetchTodayCount();


    // --------------------------------------------------
    // 4. Fetch Recent Attendance Logs
    // --------------------------------------------------
    function fetchRecentLogs() {
        fetch('/api/recent_attendance')
            .then(res => res.json())
            .then(data => {
                if (!data.records || data.records.length === 0) return;

                // ✅ Clear initializing message on first load
                const placeholder = logBox.querySelector('.text-muted');
                if (placeholder) placeholder.remove();

                data.records.forEach(record => {

                    // ✅ Only add new entries not already shown
                    const key = `${record.student_id}-${record.time}`;
                    if (loggedToday.has(key)) return;

                    loggedToday.add(key);
                    addLog(
                        'success',
                        record.name,
                        record.department,
                        record.time
                    );

                    showToast(record.name, record.time);
                });
            })
            .catch(() => {});
    }
    setInterval(fetchRecentLogs, 4000);
    fetchRecentLogs();


    // --------------------------------------------------
    // 5. Add Log Entry
    // ✅ Uses textContent instead of innerHTML for user data
    // --------------------------------------------------
    function addLog(type, name, department, time) {

        const item = document.createElement('div');
        item.className =
            'log-item d-flex justify-content-between ' +
            'align-items-center border-bottom py-2 px-1';

        if (type === 'system') {

            // ✅ System messages are static — safe to use textContent
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger small';

            const icon = document.createElement('i');
            icon.className = 'fas fa-exclamation-circle me-1';

            errorDiv.appendChild(icon);
            // ✅ textContent for name (could be user data)
            errorDiv.appendChild(
                document.createTextNode(`${name}: ${department}`)
            );

            item.appendChild(errorDiv);

        } else {

            // Left side — name and department
            const leftDiv = document.createElement('div');

            const nameDiv = document.createElement('div');
            nameDiv.className = 'fw-bold small';

            const checkIcon = document.createElement('i');
            checkIcon.className = 'fas fa-user-check text-success me-1';
            nameDiv.appendChild(checkIcon);

            // ✅ textContent prevents XSS for student name
            nameDiv.appendChild(document.createTextNode(name));

            const deptDiv = document.createElement('div');
            deptDiv.className = 'text-muted';
            deptDiv.style.fontSize = '11px';
            // ✅ textContent prevents XSS for department
            deptDiv.textContent = department;

            leftDiv.appendChild(nameDiv);
            leftDiv.appendChild(deptDiv);

            // Right side — time badge
            const badge = document.createElement('span');
            badge.className =
                'badge bg-success-subtle text-success ' +
                'border border-success-subtle';
            // ✅ textContent prevents XSS for time
            badge.textContent = time;

            item.appendChild(leftDiv);
            item.appendChild(badge);
        }

        // ✅ Add to top of log
        logBox.insertBefore(item, logBox.firstChild);

        // ✅ Keep only last 20 entries
        const items = logBox.querySelectorAll('.log-item');
        if (items.length > 20) {
            items[items.length - 1].remove();
        }
    }


    // --------------------------------------------------
    // 6. Toast Notification
    // ✅ Uses textContent instead of innerHTML for user data
    // --------------------------------------------------
    function showToast(name, time) {
        const toastContainer = document.getElementById('attendanceToast');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className =
            'alert alert-success d-flex align-items-center ' +
            'shadow mb-2 py-2 px-3 rounded-3';
        toast.style.animation = 'slideIn 0.3s ease';

        // ✅ Build toast with textContent not innerHTML
        const icon = document.createElement('i');
        icon.className = 'fas fa-check-circle me-2 fs-5';

        const textDiv = document.createElement('div');

        const nameDiv = document.createElement('div');
        nameDiv.className = 'fw-bold';
        // ✅ textContent prevents XSS for student name
        nameDiv.textContent = name;

        const timeDiv = document.createElement('div');
        timeDiv.style.fontSize = '11px';
        // ✅ textContent prevents XSS for time
        timeDiv.textContent = `Attendance marked at ${time}`;

        textDiv.appendChild(nameDiv);
        textDiv.appendChild(timeDiv);

        toast.appendChild(icon);
        toast.appendChild(textDiv);

        toastContainer.appendChild(toast);

        // ✅ Auto remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s';
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }

});