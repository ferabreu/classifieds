/**
 * Select All Checkbox Functionality
 *
 * Provides "select all" functionality for form checkboxes.
 * Assumes the following structure:
 * - A checkbox with id="select-all" in the table header
 * - Row checkboxes with class="row-checkbox"
 *
 * When the select-all checkbox is toggled, all row checkboxes are checked/unchecked.
 * When any row checkbox is changed, the select-all checkbox is synced to reflect
 * whether all, some, or none of the row checkboxes are selected.
 */

document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');

    if (!selectAllCheckbox || rowCheckboxes.length === 0) {
        return; // Exit if select-all or row checkboxes don't exist
    }

    // When header checkbox is toggled, set all row checkboxes
    selectAllCheckbox.addEventListener('change', function() {
        rowCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
    });

    // When any row checkbox is changed, sync the header checkbox
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', syncSelectAllCheckbox);
    });

    function syncSelectAllCheckbox() {
        const total = rowCheckboxes.length;
        const checked = document.querySelectorAll('.row-checkbox:checked').length;

        selectAllCheckbox.checked = total > 0 && checked === total;
        // Optionally, set indeterminate state when some (but not all) are checked
        selectAllCheckbox.indeterminate = checked > 0 && checked < total;
    }
});
