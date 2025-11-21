// This script dynamically creates category dropdowns for each level of the category tree.
// It requires the template to provide configuration via data-* attributes on the container:
//   - data-hidden-field-id: id of the original WTForms <select> (hidden)
//   - data-subcategories-url: URL template with "{parent_id}" placeholder
//   - data-breadcrumb-url: URL template with "{category_id}" placeholder
document.addEventListener('DOMContentLoaded', function() {
    // Container for dynamic dropdowns
    var categoryContainer = document.getElementById('category-dropdowns');
    if (!categoryContainer) {
        console.error('category_dropdowns: container with id "category-dropdowns" not found. Abort.');
        return;
    }

    // Read required configuration from data-attributes
    var hiddenFieldId = categoryContainer.dataset.hiddenFieldId;
    var subcategoriesUrlTpl = categoryContainer.dataset.subcategoriesUrl;
    var breadcrumbUrlTpl = categoryContainer.dataset.breadcrumbUrl;
    var excludeIds = [];

    // optional: list of category ids (JSON) that must not be selectable (e.g. the category being edited + descendants)
    if (categoryContainer.dataset.excludeIds) {
        try {
            excludeIds = JSON.parse(categoryContainer.dataset.excludeIds);
        } catch (e) {
            console.error('category_dropdowns: invalid JSON in data-exclude-ids', e);
            excludeIds = [];
        }
    }

    if (!hiddenFieldId || !subcategoriesUrlTpl || !breadcrumbUrlTpl) {
        console.error('category_dropdowns: missing required data-* attributes on #category-dropdowns. Required: data-hidden-field-id, data-subcategories-url, data-breadcrumb-url');
        return;
    }

    var categoryHidden = document.getElementById(hiddenFieldId);
    if (!categoryHidden) {
        console.error('category_dropdowns: hidden field with id "' + hiddenFieldId + '" not found. Abort.');
        return;
    }
    categoryHidden.style.display = 'none'; // Hide the original WTForms dropdown

    function buildSubcategoriesUrl(parentId) {
        return subcategoriesUrlTpl.replace('{parent_id}', parentId);
    }
    function buildBreadcrumbUrl(categoryId) {
        return breadcrumbUrlTpl.replace('{category_id}', categoryId);
    }

    // Helper to create a dropdown
    // Returns a Promise that resolves to a dropdown element if there are items, or null if none.
    function createDropdown(level, parentId, selectedId, callback) {
        return fetch(buildSubcategoriesUrl(parentId))
            .then(response => response.json())
            .then(data => {
                if (!data || data.length === 0) {
                    // No items at all -> do not render a dropdown
                    return null;
                }
                // Apply excludeIds filter first; if all items are excluded, don't render
                var items = data.filter(function(cat) {
                    return !(excludeIds && excludeIds.indexOf(cat.id) !== -1);
                });
                if (!items || items.length === 0) {
                    // After filtering there's nothing selectable -> do not render
                    return null;
                }
                var dropdown = document.createElement('select');
                dropdown.className = 'form-select mb-2';
                dropdown.setAttribute('data-level', level);
                var option = document.createElement('option');
                option.value = '';
                option.textContent = 'Select...';
                dropdown.appendChild(option);
                items.forEach(function(cat) {
                    var opt = document.createElement('option');
                    opt.value = cat.id;
                    opt.textContent = cat.name;
                    dropdown.appendChild(opt);
                });
                if (selectedId) dropdown.value = selectedId;
                if (typeof callback === 'function') callback(dropdown, items);
                return dropdown;
            })
            .catch(function(err){
                console.error('category_dropdowns: error fetching subcategories for parent ' + parentId, err);
                return null;
            });
    }

    // Remove all dropdowns below a certain level
    function removeDropdownsBelow(level) {
        var selects = Array.from(categoryContainer.querySelectorAll('select'));
        selects.forEach(function(sel) {
            var selLevel = parseInt(sel.getAttribute('data-level'));
            if (selLevel > level) {
                sel.remove();
            }
        });
    }

    // Remove the placeholder from a dropdown after selection
    function removePlaceholder(dropdown) {
        var placeholder = dropdown.querySelector('option[value=""]');
        if (placeholder) placeholder.remove();
    }

    // Set hidden WTForms field to selectedId
    function setHiddenCategory(selectedId) {
        if (categoryHidden) categoryHidden.value = selectedId;
    }

    // Add event listener for change on the container (event delegation)
    categoryContainer.addEventListener('change', function(event) {
        var target = event.target;
        if (target.tagName.toLowerCase() !== 'select') return;
        var level = parseInt(target.getAttribute('data-level'));
        var selectedId = target.value;
        removeDropdownsBelow(level);
        removePlaceholder(target);
        setHiddenCategory(selectedId);
        if (selectedId) {
            // Let createDropdown handle fetch + exclusion filtering and append only if it returns a dropdown
            createDropdown(level + 1, selectedId).then(function(newDropdown) {
                if (newDropdown) categoryContainer.appendChild(newDropdown);
            });
        }
    });

    // Initialize dropdowns for new or edit forms
    categoryContainer.innerHTML = '';
    var initialId = categoryHidden ? categoryHidden.value : null;
    if (initialId) {
        // If editing: build the breadcrumb path, then check for children and add next-level dropdown if needed
        fetch(buildBreadcrumbUrl(initialId))
            .then(response => response.json())
            .then(function(path) {
                categoryContainer.innerHTML = '';
                var parentId = 0;
                var lastIdx = path.length - 1;
                function addDropdown(idx) {
                    if (idx > lastIdx) {
                        // After last breadcrumb, check for children and add dropdown if needed
                        createDropdown(idx, parentId, null).then(function(dropdown) {
                            if (dropdown) categoryContainer.appendChild(dropdown);
                        });
                        return;
                    }
                    var cat = path[idx];
                    createDropdown(idx, parentId, cat.id, function(dropdown, data) {
                        categoryContainer.appendChild(dropdown);
                        parentId = cat.id;
                        addDropdown(idx + 1);
                    });
                }
                addDropdown(0);
            })
            .catch(function(err){
                console.error('category_dropdowns: error fetching breadcrumb for ' + initialId, err);
            });
    } else {
        // If creating new: show only the root dropdown
        createDropdown(0, 0, null).then(function(dropdown) {
            if (dropdown) categoryContainer.appendChild(dropdown);
        });
    }
});