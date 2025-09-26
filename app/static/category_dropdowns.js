// This script dynamically creates category dropdowns for each level of the category tree.
// It uses the /subcategories_for_parent/<parent_id> endpoint to fetch children.
$(function() {
    // Container for dynamic dropdowns
    var $categoryContainer = $('<div id="category-dropdowns"></div>');
    $('#category').closest('.mb-3').before($categoryContainer);
    $('#category').hide(); // Hide the original WTForms dropdown

    // Helper to create a dropdown
    function createDropdown(level, parentId, selectedId, callback) {
        var $dropdown = $('<select class="form-select mb-2" data-level="' + level + '"></select>');
        $dropdown.append($('<option value="">Select...</option>'));
        $.getJSON('/subcategories_for_parent/' + parentId, function(data) {
            $.each(data, function(idx, cat) {
                $dropdown.append($('<option>').attr('value', cat.id).text(cat.name));
            });
            if (selectedId) $dropdown.val(selectedId);
            if (typeof callback === 'function') callback($dropdown, data);
        });
        return $dropdown;
    }

    // Start with only one root dropdown
    $categoryContainer.empty();
    $categoryContainer.append(createDropdown(0, 0));

    // When a dropdown changes, remove all lower levels and add next level if needed
    $categoryContainer.on('change', 'select', function() {
        var level = parseInt($(this).data('level'));
        var selectedId = $(this).val();
        // Remove all dropdowns below this level
        $categoryContainer.find('select').filter(function() {
            return parseInt($(this).data('level')) > level;
        }).remove();
        // Set hidden WTForms field to selectedId
        $('#category').val(selectedId);
        if (selectedId) {
            // Check if this category has children
            $.getJSON('/subcategories_for_parent/' + selectedId, function(data) {
                if (data.length > 0) {
                    $categoryContainer.append(createDropdown(level + 1, selectedId));
                }
            });
        }
    });

    // If editing, pre-select the correct path
    var initialId = $('#category').val();
    if (initialId) {
        // Fetch the breadcrumb path for the initial category
        $.getJSON('/category_breadcrumb/' + initialId, function(path) {
            $categoryContainer.empty();
            var parentId = 0;
            var lastIdx = path.length - 1;
            function addDropdown(idx) {
                if (idx > lastIdx) return;
                var cat = path[idx];
                createDropdown(idx, parentId, cat.id, function($dropdown, data) {
                    $categoryContainer.append($dropdown);
                    parentId = cat.id;
                    addDropdown(idx + 1);
                });
            }
            addDropdown(0);
        });
    }
});
