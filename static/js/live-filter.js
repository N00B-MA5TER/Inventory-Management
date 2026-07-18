// Progressive enhancement only: the search box already works via normal form
// submit (page reload) without this script. This just makes the on-page list
// narrow instantly as you type, without waiting for a server round-trip.
// Matching is "starts with" on item name, company/brand name, or (for Spare
// Parts) vehicle manufacturer/model, and never changes the order items
// appear in — it only shows/hides rows already on the page.
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-live-filter-input]').forEach(function (input) {
        var list = document.querySelector(input.getAttribute('data-live-filter-input'));
        if (!list) return;

        var rows = list.querySelectorAll('.product-row');

        input.addEventListener('input', function () {
            var query = input.value.trim().toLowerCase();
            rows.forEach(function (row) {
                if (!query) {
                    row.style.display = '';
                    return;
                }
                var fields = [
                    row.getAttribute('data-title') || '',
                    row.getAttribute('data-company') || '',
                    row.getAttribute('data-vehicle-make') || '',
                    row.getAttribute('data-vehicle-model') || '',
                ];
                var matches = fields.some(function (field) { return field.indexOf(query) === 0; });
                row.style.display = matches ? '' : 'none';
            });
        });
    });
});
