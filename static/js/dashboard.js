// static/js/dashboard.js

document.addEventListener('DOMContentLoaded', () => {

    // --------------------------------------------------
    // 1. Live Clock
    // --------------------------------------------------
    const clockElement = document.getElementById('live-clock');

    function updateClock() {
        if (!clockElement) return;

        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        // ✅ Simple HH:MM:SS format matching dashboard.html
        clockElement.textContent = `${h}:${m}:${s}`;
    }

    updateClock();
    setInterval(updateClock, 1000);

    // --------------------------------------------------
    // 2. Dynamic Greeting
    // --------------------------------------------------
    const greetingElement = document.getElementById('greeting-text');

    if (greetingElement) {
        const hour = new Date().getHours();
        let greeting = 'Good Morning';

        if (hour >= 12 && hour < 17) greeting = 'Good Afternoon';
        else if (hour >= 17) greeting = 'Good Evening';

        // ✅ textContent not innerHTML
        greetingElement.textContent = greeting;
    }

    // --------------------------------------------------
    // 3. Animate progress bars on load
    // --------------------------------------------------
    document.querySelectorAll('.progress-bar').forEach(bar => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        bar.style.transition = 'width 1s ease';

        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 200);
    });

    // --------------------------------------------------
    // 4. Dim cards with 0% attendance
    // --------------------------------------------------
    document.querySelectorAll('.card.border').forEach(card => {
        const badge = card.querySelector('.badge');
        if (badge && badge.textContent.trim() === '0%') {
            card.style.opacity = '0.6';
        }
    });

});