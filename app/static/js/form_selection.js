/*
 * SPDX-License-Identifier: GPL-2.0-only
 * Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
 *
 * Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
 * See LICENSE file in the project root for full license information.
 *
 * This code was written and annotated by GitHub Copilot
 * at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).
 */

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

function getSelectedId(radioName) {
    const selected = document.querySelector(`input[name="${radioName}"]:checked`);
    if (!selected) {
        alert('Please select a listing first.');
        return null;
    }
    return selected.value;
}

function handleEdit(editUrlTemplate, radioName) {
    const id = getSelectedId(radioName);
    if (id) {
        window.location.href = editUrlTemplate.replace('{id}', id);
    }
}

function handleDelete(deleteUrlTemplate, radioName, entityLabel) {
    const selected = document.querySelector(`input[name="${radioName}"]:checked`);
    if (!selected) {
        alert('Please select a listing first.');
        return;
    }

    const id = selected.value;
    // Some entity types (e.g., listings) don't track associated child entities,
    // so data-listing-count may be absent. Default to 0 for entities without it.
    const dataAttribute = selected.getAttribute('data-listing-count');
    const listingCount = dataAttribute ? parseInt(dataAttribute, 10) : 0;

    const baseLabel = entityLabel && typeof entityLabel === 'string' ? entityLabel : 'listing';
    let message = `Delete this ${baseLabel}?`;
    if (listingCount > 0) {
        message += `\n\nWarning: The selected ${baseLabel} has ${listingCount} associated listing(s). These will also be deleted.`;
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
