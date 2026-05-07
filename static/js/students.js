// static/js/students.js

document.addEventListener('DOMContentLoaded', () => {

    const searchInput = document.getElementById('studentSearch');
    const tbody = document.querySelector('tbody');

    // --------------------------------------------------
    // Debounce helper
    // ✅ Fixed — use func(...args) not func.apply(this, args)
    // --------------------------------------------------
    const debounce = (func, delay = 250) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            // ✅ Arrow functions don't have own 'this'
            // so use spread instead of apply
            timeout = setTimeout(() => func(...args), delay);
        };
    };

    // --------------------------------------------------
    // Live Search
    // --------------------------------------------------
    const filterStudents = () => {
        if (!tbody || !searchInput) return;

        const rows = tbody.querySelectorAll('tr');
        const term = searchInput.value.trim().toLowerCase();
        let found = 0;

        rows.forEach(row => {
            // Skip empty state row
            if (row.cells.length <= 1) return;

            const idCell     = row.children[1]?.textContent.toLowerCase() || '';
            const nameCell   = row.children[2]?.textContent.toLowerCase() || '';
            const fatherCell = row.children[3]?.textContent.toLowerCase() || '';
            const deptCell   = row.children[4]?.textContent.toLowerCase() || '';

            const matches =
                idCell.includes(term) ||
                nameCell.includes(term) ||
                fatherCell.includes(term) ||
                deptCell.includes(term);

            row.style.display = matches ? '' : 'none';
            if (matches) found++;
        });

        const noDataRow = document.getElementById('noDataRow');
        if (noDataRow) {
            noDataRow.style.display = found === 0 ? '' : 'none';
        }
    };

    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterStudents));
    }

});