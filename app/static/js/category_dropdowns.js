// This script dynamically creates category dropdowns for each level of the category tree.
// It uses the /subcategories_for_parent/<parent_id> endpoint to fetch children.
document.addEventListener('DOMContentLoaded', function() {
    // Container for dynamic dropdowns
    var categoryContainer = document.getElementById('category-dropdowns');
    var categoryHidden = document.getElementById('category');
    if (categoryHidden) categoryHidden.style.display = 'none'; // Hide the original WTForms dropdown

    // Helper to create a dropdown
    function createDropdown(level, parentId, selectedId, callback) {
        var dropdown = document.createElement('select');
        dropdown.className = 'form-select mb-2';
        dropdown.setAttribute('data-level', level);
        var option = document.createElement('option');
        option.value = '';
        option.textContent = 'Select...';
        dropdown.appendChild(option);
        fetch('/subcategories_for_parent/' + parentId)
            .then(response => response.json())
            .then(data => {
                data.forEach(function(cat) {
                    var opt = document.createElement('option');
                    opt.value = cat.id;
                    opt.textContent = cat.name;
                    dropdown.appendChild(opt);
                });
                if (selectedId) dropdown.value = selectedId;
                if (typeof callback === 'function') callback(dropdown, data);
            });
        return dropdown;
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
            fetch('/subcategories_for_parent/' + selectedId)
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        var newDropdown = createDropdown(level + 1, selectedId);
                        categoryContainer.appendChild(newDropdown);
                    }
                });
        }
    });

    // Initialize dropdowns for new or edit forms
    categoryContainer.innerHTML = '';
    var initialId = categoryHidden ? categoryHidden.value : null;
    if (initialId) {
        // If editing: build the breadcrumb path, then check for children and add next-level dropdown if needed
        fetch('/category_breadcrumb/' + initialId)
            .then(response => response.json())
            .then(function(path) {
                categoryContainer.innerHTML = '';
                var parentId = 0;
                var lastIdx = path.length - 1;
                function addDropdown(idx) {
                    if (idx > lastIdx) {
                        // After last breadcrumb, check for children and add dropdown if needed
                        fetch('/subcategories_for_parent/' + parentId)
                            .then(response => response.json())
                            .then(function(data) {
                                if (data.length > 0) {
                                    // Add a new dropdown for the next level, no selection
                                    var newDropdown = createDropdown(idx, parentId, null, function(dropdown, data) {
                                        categoryContainer.appendChild(dropdown);
                                    });
                                }
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
            });
    } else {
        // If creating new: show only the root dropdown
        categoryContainer.appendChild(createDropdown(0, 0, null));
    }
});