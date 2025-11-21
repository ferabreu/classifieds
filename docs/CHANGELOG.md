# Changelog

All notable changes to this project are recorded here.

## Unreleased (2025-11-21)

### category dropdowns (frontend) — app/static/js/category_dropdowns.js
- Major refactor and hardening of dynamic category dropdown behaviour:
  - createDropdown is now Promise-only (removed callback parameter).
  - fetchSubcategories with in-memory cache (per parentId) and 5-minute TTL to reduce duplicate network calls.
  - Added AbortController per parent fetch so stale in-flight network requests can be cancelled when refreshed.
  - Added request-token logic per dropdown level to avoid stale DOM appends when out-of-order responses arrive.
  - Filtered fetched items by `data-exclude-ids` (normalized to strings) so dropdowns with no actual selectable items are not rendered (avoids placeholder-only selects).
  - Only render the "Select..." placeholder on "new" forms (no initial category selected). Edit forms omit placeholders to save space.
  - Use response.ok checks and return empty arrays on error to avoid throwing in UI logic.
  - Use encodeURIComponent when substituting ids into URL templates.
  - Accessibility: generated <select> elements now include `aria-labelledby="category-dropdowns-label"` when that element exists.
  - Replaced legacy `var` with `const`/`let` for clearer block scoping.

- Compatibility notes:
  - Requires backend endpoints to keep returning the same shapes:
    - `GET /subcategories_for_parent/<parent_id>` -> JSON array of {id, name}
    - `GET /category_breadcrumb/<category_id>` (utils.category_breadcrumb) -> ordered array of category objects (id, name) forming the breadcrumb
  - Templates must continue to set:
    - `data-hidden-field-id` referencing the hidden WTForms select id (e.g. "category" or "parent_id")
    - `data-subcategories-url` and `data-breadcrumb-url` templates with placeholders `{parent_id}` and `{category_id}`
    - `data-exclude-ids` (optional) as JSON array via `tojson` when used (admin edit)
  - The JS normalizes exclude ids to strings; ensure backend `tojson` outputs numeric or string ids (both handled).

### Files touched (summary)
- app/static/js/category_dropdowns.js
  - Refactor + caching, abort, tokening, placeholder logic, accessibility.
- Templates (no code changes required for compatibility)
  - app/templates/listings/listing_form.html
  - app/templates/admin/admin_category_form.html
  - Ensure these keep providing the same data-* attributes (they already do).

### QA / Testing notes
- Verify adding a listing:
  - Root dropdown appears with "Select..." placeholder.
  - Selecting a category adds child dropdowns only when the child list has selectable items.
- Verify editing a listing/category:
  - Breadcrumb-generated dropdowns appear without placeholder options.
  - No empty/select-only <select> elements are rendered.
  - Rapidly changing selections should not cause stale dropdowns to be appended.
- Verify admin edit category:
  - Categories listed in `data-exclude-ids` do not appear as options.
- Verify network behavior:
  - Repeated requests for same parent within 5 minutes use cached Promise.
  - Aborted in-flight requests do not produce errors in console (they return empty arrays).

### Notes / follow-ups
- Consider reducing TTL or exposing a cache-invalidation endpoint if category changes are frequent in admin.
- Optional improvements: localize the placeholder text, add stronger ARIA attributes, or move to an ES module/bundler build if the project adopts frontend bundling.

