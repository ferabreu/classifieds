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

## Merging of add_subcategories branch (2025-12-03)
Significant architectural change by replacing the Type/Category two-level model with a hierarchical self-referencing Category model supporting unlimited nesting. The refactoring includes comprehensive updates to models, routes, templates, JavaScript, and migrations, along with documentation improvements and tooling updates.

Key Changes:

  - Replaced Type and Category tables with a single self-referencing Category table using parent_id relationships.
    - Database Migrations:
      - Added parent_id column to Category table for hierarchical support.
      - Migrated existing Type entities into Category hierarchy and removed Type table.
      - Added sort_order field with alphabetical initialization for consistent category ordering.
  - Added hierarchical category navigation with collapsible sidebar UI and dynamic dropdown selections
  - Implemented cycle-detection safeguards and breadcrumb navigation for category trees
  - Changed license from MIT to GPL-2.0-only with corresponding header updates across Python files
  - Listing form: dynamic dropdowns for category/subcategory selection.
  - Backend
    - Added API endpoints to support dynamic subcategory dropdowns:
      - `GET /subcategories_for_parent/<parent_id>` — returns JSON array of {id, name}.
      - `GET /category_breadcrumb/<category_id>` — returns ordered breadcrumb (array of category objects).
    - Added server-side helper to produce category breadcrumb used by edit forms (utils.category_breadcrumb).
  - Frontend / Templates
    - Wired new frontend asset app/static/js/category_dropdowns.js into listing and admin forms.
    - Templates updated to expose required data-* attributes:
      - `data-subcategories-url`, `data-breadcrumb-url`, `data-hidden-field-id`, and optional `data-exclude-ids`.
  - QA & rollout
    - Included manual QA checklist for listing create/edit and admin category edit flows (see Unreleased section above).
    - No database migrations required for this change.
  - PR checklist
    - Ensure templates render the required data-* attributes.
    - Verify manual QA steps (create/edit listing, admin edit) before merging to main.

Reviewed Changes (File:	Description)
 - migrations/versions/befe2371cacf_add_parent_id_to_category_for_.py	Adds parent_id column to Category table for hierarchical support
 - migrations/versions/7f2e1a3b9cde_merge_types_to_category.py	Migrates Type entities into Category hierarchy and removes Type table
 - migrations/versions/a1b2c3d4e5f6_add_sort_order_to_category.py	Adds sort_order field with alphabetical initialization
 - app/models.py	Implements self-referencing Category model with cycle detection, breadcrumb generation, and descendant queries
 - app/forms.py	Updates forms to remove Type references and adds parent_id validation for categories
 - app/routes/listings.py	Refactors to use hierarchical categories, adds subcategory endpoints, removes Type-based filtering
 - app/routes/admin.py	Updates category management for hierarchy, adds cycle prevention, removes Type admin routes
 - app/routes/utils.py	Adds category breadcrumb endpoint and moves to Blueprint pattern
 - app/templates/base.html	Replaces type dropdowns with collapsible sidebar category tree
 - app/static/js/category_dropdowns.js	New JavaScript for dynamic multi-level category selection with caching and accessibility
 - app/templates/macros/*.html	New macros for rendering category trees, breadcrumbs, and lists
 - LICENSE	Changes from MIT to GPL-2.0-only
 - docs/*	Adds CODE_STYLE.md, CHANGELOG.md, license audit documentation, and Git reference guides
 - app/cli/*.py	Moves CLI commands to separate modules, adds demo data generation with Unsplash integration
