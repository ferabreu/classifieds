// This script dynamically creates category dropdowns for each level of the category tree.
// It requires the template to provide configuration via data-* attributes on the container:
//   - data-hidden-field-id: id of the original WTForms <select> (hidden)
//   - data-subcategories-url: URL template with "{parent_id}" placeholder
//   - data-breadcrumb-url: URL template with "{category_id}" placeholder
document.addEventListener('DOMContentLoaded', function() {
    // Container for dynamic dropdowns
    const categoryContainer = document.getElementById('category-dropdowns');
    if (!categoryContainer) {
        console.error('category_dropdowns: container with id "category-dropdowns" not found. Abort.');
        return;
    }

    // Read required configuration from data-attributes
    const hiddenFieldId = categoryContainer.dataset.hiddenFieldId;
    const subcategoriesUrlTpl = categoryContainer.dataset.subcategoriesUrl;
    const breadcrumbUrlTpl = categoryContainer.dataset.breadcrumbUrl;

    // Normalize excludeIds to strings for robust comparison
    let excludeIds = [];
    if (categoryContainer.dataset.excludeIds) {
        try {
            const parsed = JSON.parse(categoryContainer.dataset.excludeIds);
            if (Array.isArray(parsed)) {
                excludeIds = parsed.map(function(id){ return String(id); });
            } else {
                excludeIds = [];
            }
        } catch (e) {
            console.error('category_dropdowns: invalid JSON in data-exclude-ids', e);
            excludeIds = [];
        }
    }

    if (!hiddenFieldId || !subcategoriesUrlTpl || !breadcrumbUrlTpl) {
        console.error('category_dropdowns: missing required data-* attributes on #category-dropdowns. Required: data-hidden-field-id, data-subcategories-url, data-breadcrumb-url');
        return;
    }

    const categoryHidden = document.getElementById(hiddenFieldId);
    if (!categoryHidden) {
        console.error('category_dropdowns: hidden field with id "' + hiddenFieldId + '" not found. Abort.');
        return;
    }
    categoryHidden.style.display = 'none'; // Hide the original WTForms dropdown

    // Determine whether this is a "new" form (no initial category selected).
    // Placeholders ("Select...") are useful for new forms but redundant for edit forms
    // where dropdowns will be rendered pre-populated from the breadcrumb.
    const showPlaceholders = !categoryHidden.value;
        const isEditing = Boolean(categoryHidden.value);

    function buildSubcategoriesUrl(parentId) {
        // ensure ids are encoded in case templates contain characters
        return subcategoriesUrlTpl.replace('{parent_id}', encodeURIComponent(parentId));
    }
    function buildBreadcrumbUrl(categoryId) {
        return breadcrumbUrlTpl.replace('{category_id}', encodeURIComponent(categoryId));
    }

    // Simple in-memory cache: parentId -> { promise, ts }
    const subcategoriesCache = new Map(); // key -> { promise, ts }
    const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes TTL; adjust if needed
    // Controllers per cache key so we can cancel in-flight requests on refresh
    const subcategoriesControllers = new Map();
    // Request token per level to avoid stale appends: level -> token number
    const latestRequestToken = {};

    // Helper to fetch subcategories (with caching)
    function fetchSubcategories(parentId) {
        const key = String(parentId);
        const now = Date.now();
        const existing = subcategoriesCache.get(key);
        if (existing && (now - existing.ts) < CACHE_TTL_MS) {
            // still fresh
            return existing.promise;
        }
        // If there is an in-flight controller for this key, abort it — we are starting a fresh fetch
        const prevController = subcategoriesControllers.get(key);
        if (prevController) {
            try { prevController.abort(); } catch (e) { /* ignore */ }
            subcategoriesControllers.delete(key);
        }

        const controller = new AbortController();
        subcategoriesControllers.set(key, controller);

        const p = fetch(buildSubcategoriesUrl(parentId), { signal: controller.signal })
            .then(function(response){
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ' when fetching subcategories for parent ' + parentId);
                }
                return response.json();
            })
            .then(function(data){
                if (!Array.isArray(data)) return [];
                return data;
            })
            .catch(function(err){
                if (err && err.name === 'AbortError') {
                    // aborted intentionally — return empty so callers treat as no-data
                    return [];
                }
                console.error('category_dropdowns: error fetching subcategories for parent ' + parentId, err);
                return [];
            })
            .finally(function(){
                // cleanup controller for this key if it matches
                const c = subcategoriesControllers.get(key);
                if (c === controller) subcategoriesControllers.delete(key);
            });

        subcategoriesCache.set(key, { promise: p, ts: now });
        return p;
    }

    // Helper to create a dropdown
    // Returns a Promise that resolves to a dropdown element if there are selectable items, or null if none.
    function createDropdown(level, parentId, selectedId) {
        // Track token for this level
        latestRequestToken[level] = (latestRequestToken[level] || 0) + 1;
        const token = latestRequestToken[level];

        return fetchSubcategories(parentId).then(function(data){
            // Only proceed if this request is still the latest for the level
            if (latestRequestToken[level] !== token) {
                // Stale; drop result
                return null;
            }

            if (!data || data.length === 0) {
                // No items at all -> do not render a dropdown
                return null;
            }
            // Apply excludeIds filter first; normalize cat.id to string for comparison
            const items = data.filter(function(cat){
                return excludeIds.indexOf(String(cat.id)) === -1;
            });
            if (!items || items.length === 0) {
                // After filtering there's nothing selectable -> do not render
                return null;
            }
            const dropdown = document.createElement('select');
            dropdown.className = 'form-select mb-2';
            dropdown.setAttribute('data-level', String(level));
            dropdown.setAttribute('data-parent-id', String(parentId));
            // Accessibility: link to the label container if present
            if (document.getElementById('category-dropdowns-label')) {
                dropdown.setAttribute('aria-labelledby', 'category-dropdowns-label');
            }
            // Show placeholder either when the whole form is a "new" form (showPlaceholders)
            // or when this specific dropdown has no pre-selected value (selectedId falsy).
            if (showPlaceholders || !selectedId) {
                 const placeholder = document.createElement('option');
                 placeholder.value = '';
                 placeholder.textContent = 'Select...';
                 dropdown.appendChild(placeholder);
             }
            // Allow moving a category to the top level by offering an explicit root option
            // on the first dropdown (level 0, parentId 0).
            if (level === 0 && (parentId === 0 || parentId === '0')) {
                const rootOpt = document.createElement('option');
                rootOpt.value = '0';
                rootOpt.textContent = 'Top level';
                dropdown.appendChild(rootOpt);
            }
                // When editing, allow selecting the current level (the parent represented by this dropdown)
                // to move a category to an intermediate ancestor without rebuilding from the top.
                // Only show when parentId is non-root to avoid duplicating the Top level option.
                if (isEditing && parentId && String(parentId) !== '0') {
                    const currentOpt = document.createElement('option');
                    currentOpt.value = String(parentId);
                    currentOpt.textContent = 'Current level';
                    dropdown.appendChild(currentOpt);
                }
             items.forEach(function(cat) {
                 const opt = document.createElement('option');
                 opt.value = String(cat.id);
                 opt.textContent = cat.name;
                 dropdown.appendChild(opt);
             });
            // Only set selected value when a non-null, non-empty selectedId is provided.
            // This handles ids like 0 correctly and avoids setting when selectedId is '' or null.
            if (selectedId != null && String(selectedId) !== '') {
                dropdown.value = String(selectedId);
            }
            return dropdown;
        });
    }

    // Remove all dropdowns below a certain level
    function removeDropdownsBelow(level) {
        const selects = Array.from(categoryContainer.querySelectorAll('select'));
        selects.forEach(function(sel) {
            const selLevel = parseInt(sel.getAttribute('data-level'), 10);
            if (selLevel > level) {
                sel.remove();
            }
        });
    }

    // Remove the placeholder from a dropdown after selection
    function removePlaceholder(dropdown) {
        const placeholder = dropdown.querySelector('option[value=""]');
        if (placeholder) placeholder.remove();
    }

    // Set hidden WTForms field to selectedId
    function setHiddenCategory(selectedId) {
        if (categoryHidden) categoryHidden.value = selectedId;
    }

    // Add event listener for change on the container (event delegation)
    categoryContainer.addEventListener('change', function(event) {
        const target = event.target;
        if (target.tagName.toLowerCase() !== 'select') return;
        const level = parseInt(target.getAttribute('data-level'), 10);
        const selectedId = target.value;
            const parentIdForDropdown = target.getAttribute('data-parent-id');
        removeDropdownsBelow(level);
        removePlaceholder(target);
        setHiddenCategory(selectedId);
            // If the user picks "Current level", we keep the selection at this level and do not expand further.
            if (parentIdForDropdown && selectedId === parentIdForDropdown) {
                return;
            }
        if (selectedId && selectedId !== '0') {
            // createDropdown handles fetch, filtering and token-checking.
            createDropdown(level + 1, selectedId).then(function(newDropdown) {
                if (newDropdown) categoryContainer.appendChild(newDropdown);
            });
        } else if (selectedId === '0') {
            // Explicitly choosing root clears deeper dropdowns and sets parent to None
            removeDropdownsBelow(level);
            setHiddenCategory('0');
        }
    });

    // Initialize dropdowns for new or edit forms
    categoryContainer.innerHTML = '';
    const initialId = categoryHidden ? categoryHidden.value : null;
    if (initialId) {
        // If editing: build the breadcrumb path, then check for children and add next-level dropdown if needed
        fetch(buildBreadcrumbUrl(initialId))
            .then(function(response){
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ' when fetching breadcrumb for ' + initialId);
                }
                return response.json();
            })
            .then(function(path) {
                categoryContainer.innerHTML = '';
                let parentId = 0;
                const lastIdx = path.length - 1;
                function addDropdown(idx) {
                    if (idx > lastIdx) {
                        // After last breadcrumb, check for children and add dropdown if needed
                        const selectedForRoot = (initialId === '0' && idx === 0) ? '0' : null;
                        createDropdown(idx, parentId, selectedForRoot).then(function(dropdown) {
                            if (dropdown) categoryContainer.appendChild(dropdown);
                        });
                        return;
                    }
                    const cat = path[idx];
                    // For breadcrumb entries we create dropdowns if there are siblings/children.
                    createDropdown(idx, parentId, cat.id).then(function(dropdown) {
                        if (dropdown) {
                            categoryContainer.appendChild(dropdown);
                        }
                        // Regardless of whether a dropdown was created (e.g. last-level has no siblings),
                        // advance parentId and continue building the breadcrumb.
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