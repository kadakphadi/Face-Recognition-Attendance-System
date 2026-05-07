// static/js/reports.js

document.addEventListener('DOMContentLoaded', () => {

    const searchInput = document.getElementById('tableSearch');

    // ✅ Debounce helper
    function debounce(fn, delay = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    }

    // ✅ Table search — covers all columns
    function filterTable() {
        if (!searchInput) return;

        const filter = searchInput.value.trim().toLowerCase();
        const rows = document.querySelectorAll('#reportTable tbody tr');

        rows.forEach(row => {
            // Skip empty state row
            if (row.cells.length <= 1) return;

            // Search across ALL columns
            const text = Array.from(row.cells)
                .map(cell => cell.innerText.toLowerCase())
                .join(' ');

            row.style.display = text.includes(filter) ? '' : 'none';
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterTable));
    }

});

// ✅ Print function
function printReport() {
    window.print();
}