/**
 * Form Selection Handler
 *
 * Provides utilities for handling form submissions with radio button selection.
 * Supports:
 * - Getting the selected radio button value
 * - Handling edit actions by navigating to an edit URL
 * - Handling delete actions with confirmation dialogs
 *
 * Used with forms that have:
 * - Radio buttons with name="selected_id"
 * - Action buttons with data attributes specifying behavior
 */

function getSelectedId(radioName = 'selected_user_id') {
    const selected = document.querySelector(`input[name="${radioName}"]:checked`);
    if (!selected) {
        alert('Please select an item first.');
        return null;
    }
    return selected.value;
}

function handleEdit(editUrlTemplate) {
    const id = getSelectedId();
    if (id) {
        window.location.href = editUrlTemplate.replace('{id}', id);
    }
}

function handleDelete(deleteUrlTemplate, radioName = 'selected_user_id') {
    const selected = document.querySelector(`input[name="${radioName}"]:checked`);
    if (!selected) {
        alert('Please select an item first.');
        return;
    }

    const id = selected.value;
    const dataAttribute = selected.getAttribute('data-listing-count');
    const listingCount = dataAttribute ? parseInt(dataAttribute) : 0;

    let message = 'Delete this item?';
    if (listingCount > 0) {
        message += `\n\nWarning: This user has ${listingCount} listing(s) associated with their account. These listings will also be deleted.`;
    }

    if (confirm(message)) {
        const deleteUrl = deleteUrlTemplate.replace('{id}', id);
        // Create a temporary form and submit
        const form = document.createElement('form');
        form.method = 'post';
        form.action = deleteUrl;
        document.body.appendChild(form);
        form.submit();
    }
}
