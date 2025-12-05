## Plan: Refactor routes by entity type

Reorganize Flask routes from user-type separation (`admin.py` vs regular routes) to entity-based organization (`categories.py`, `listings.py`, `users.py`). Move all category, listing, and user operations—whether admin or public—into their respective entity modules while preserving authorization patterns and minimizing URL changes.

### Steps

1. **(DONE)** **Create `app/routes/decorators.py`** with `@admin_required` decorator that implies `@login_required` (admin privileges require login). Move `admin_required` from `utils.py` to this new file. Add optional helper `owner_or_admin_check(resource, user)` for inline permission checks. Import `login_required` from `flask_login` (Flask-Login provides this; don't reimplement).

2. **(DONE)** **Add `url_name` column to `Category` model** for URL-safe category names (migration required). Generate from display name: "Real Estate" → "real-estate". Ensure uniqueness within same parent. Create helper `Category.from_path("vehicles/motorcycles")` to traverse hierarchy and return `Category` object. Reserve route names that can't be category names: `admin`, `auth`, `profile`, `listing`, `new`, `edit`, `delete`, `static`, `utils`.

   - **(DONE)** Database Migration and Helpers:

     1. **(DONE)** **Add `url_name` column to Category model:**
        - Migration: Add `url_name = db.Column(db.String(128), unique=False, nullable=False, index=True)`
        - **IMPORTANT**: Database is SQLite3 (production database). SQLite does NOT support `ALTER COLUMN` operations.
        - Use `server_default='temp'` when adding NOT NULL columns, then backfill data
        - Avoid `op.alter_column()` with nullable changes - it will fail on SQLite
        - Uniqueness constraint: Unique within same parent (siblings can't share url_name)
        - Generate from `name`: "Real Estate" → "real-estate", "Motorcycles" → "motorcycles"
        - Backfill existing categories via migration data script or CLI command
        - Validation: Check against reserved route names on create/edit

     2. **(DONE)** **Helper function `Category.from_path(path_string)`:**
        - Parse: `"vehicles/motorcycles"` → `["vehicles", "motorcycles"]`
        - Walk: Start at root, match first segment, then traverse children
        - Return: `Category` object or `None` if path invalid
        - Use in route: `category = Category.from_path(category_path) or abort(404)`

     3. **(DONE)** **Generate `url_name` from display name:**
        - Lowercase, replace spaces/special chars with hyphens
        - Strip leading/trailing hyphens
        - Example: `"Real Estate & Rentals"` → `"real-estate-rentals"`

3. **(DONE)** **Create `app/routes/categories.py`** with:
   - Admin routes at `/admin/categories/*`: list, create, edit, delete (from `admin.py`)
     - Update the edit route so that it updates `url_name` when the category name is altered.
   - AJAX endpoints: `/api/subcategories/<parent_id>`, `/api/category_breadcrumb/<category_id>`
   - Register `categories_bp` with `/admin/categories` prefix for admin routes, or without prefix if AJAX endpoints need root-level access
   - Ensure admin routes use `@admin_required` decorator
   - Preserve category cycle prevention and cascade deletion logic
   - No public listing browsing routes (those stay in `listings.py`) 

4. **Reorganize `app/routes/listings.py`**:
   - Move admin listing routes from `admin.py` (list all, bulk delete) into existing `listings.py`.
   - For admin edit, use existing `edit_listing()` in `listings.py` directly:
     - route it from both URLs: `/listing/edit/<id>` for users, `/admin/listings/edit/<id>` for admins, using permission checks to differentiate.
     - show edit button to admins on listing detail/list pages.
   - For admin delete, use existing `delete_listing()` in `listings.py` directly:
     - route it from both URLs: `/listing/delete/<id>` for users, `/admin/listings/delete/<id>` for admins, using permission checks to differentiate.
     - show delete button to admins on listing detail/list pages.
   - Keep and enhance public routes:
     - `GET /` → homepage/index (all listings)
     - `GET /listing/<int:listing_id>` → listing detail
     - `GET /<path:category_path>` → **category-filtered listing browsing** (e.g., `/vehicles/motorcycles`) - uses `Category.from_path()` helper to get category, then filters listings by category + descendants
   - User routes: `/listing/new`, `/listing/edit/<int:listing_id>`, `/listing/delete/<int:listing_id>`
   - Admin routes: `/admin/listings`, `/admin/listings/edit/<id>`, `/admin/listings/delete/<id>`, `/admin/listings/delete_selected`
   - Register `listings_bp` without URL prefix (catch-all `/<path:category_path>` must be root-level)
   - Ensure admin routes use `@admin_required` decorator
   - Ensure user routes use `@login_required` and owner-or-admin check
   - Maintain temp-commit-move file pattern for all image operations
   - Centralize listing query/pagination/sorting logic for reuse across index and category views
   - Remove remaining admin listing routes from `admin.py`.

5. **Reorganize `app/routes/users.py`** with all user-related routes:
   - Self-service at `/profile` (no ID, uses `current_user`): view and edit
   - Admin routes at `/admin/users/*`: list, view profile, edit, delete (from `admin.py`)
   - Admin routes: `/admin/users`, `/admin/users/profile/<int:user_id>`, `/admin/users/edit/<int:user_id>`, `/admin/users/delete/<int:user_id>`
   - Register `users_bp` without URL prefix (to handle both `/profile` and `/admin/users/*`)
   - Preserve last admin safeguards (prevent demoting/deleting last admin)
   - Ensure admin routes use `@admin_required` decorator
   - Ensure self-service routes use `@login_required` decorator
   - User details on listing pages: expose `listing.owner` relationship (already in model)
   - remove remaining admin user routes from `admin.py`.

6. **Create `app/routes/admin_dashboard.py`** with dashboard route (`GET /admin/dashboard`) showing stats (user count, category count, listing count). Register `admin_dashboard_bp` with `/admin` prefix. Use `@admin_required` decorator. Render existing `admin/admin_dashboard.html` template.

7. **Update all template `url_for()` references** (~20+ locations):
   - **(DONE)** Change `admin.*` to entity-based: `categories.admin_*`, `listings.admin_*`, `users.admin_*`, `admin_dashboard.dashboard`
   - **(DONE)** Update category browsing from `url_for('listings.category_listings', category_id=id)` to build category path and use direct href (or helper to build path from category object)
   - Update profile links from `url_for('users.user_profile')` to `url_for('users.profile')`
   - **(PARTIAL)** Files: `base.html`, `admin_categories.html`, `admin_listings.html`, `admin_users.html`, `admin_dashboard.html`, `listing_detail.html`, `listing_form.html`, `user_profile.html`, `user_edit.html`
     - Updated: `admin_categories.html`, `admin_listings.html`, `admin_dashboard.html`, `listing_detail.html`, `listing_form.html`, `macros/breadcrumb.html`, `macros/category_list.html`, `macros/sidebar_category_tree.html`
     - Pending: `base.html`, `admin_users.html`, `user_profile.html`, `user_edit.html` (waiting for Step 5)

8. **Remove `app/routes/admin.py` and `app/routes/utils.py`** (move `create_thumbnail` to `app/utils/images.py`). Update blueprint registration in `app/__init__.py`:
   - Remove: `admin_bp`, `utils_bp`
   - Add: `categories_bp`, `admin_dashboard_bp`
   - Registration order matters: register specific routes BEFORE catch-all category route
   - Order: `auth_bp`, `admin_dashboard_bp`, `users_bp`, `listings_bp`, `errors_bp`, then `categories_bp` (catch-all last)

### Further Considerations

1. **URL prefix strategy**: `/admin` remains for admin routes within entity modules (e.g., `/categories/admin/list`), for security clarity.

2. **Shared utilities**: Create `app/routes/decorators.py` with `admin_required` decorator and optional `owner_or_admin_check(resource, user)` helper. Move `create_thumbnail` from `utils.py` to `app/utils/images.py`.

3. **AJAX endpoint consistency**: Move AJAX endpoints to `/api/*` namespace within `categories.py`: `/api/subcategories/<parent_id>` and `/api/category_breadcrumb/<category_id>`. Update frontend JavaScript in `category_dropdowns.js` to use new endpoints.

4. **URL structure preference**: Keep `/admin` prefix for admin routes (e.g., `/admin/categories`, `/admin/listings`, `/admin/users`) to maintain clear separation. Use clean URLs for public routes: `/vehicles/motorcycles` (hierarchical category paths), `/profile` (self-service), `/listing/<id>` (listing detail).

5. **Admin dashboard**: the admin dashboard (`/admin/dashboard`) stay as-is in a separate file. It's a break from the entity-based structure, but, because it doesn't fit neatly into categories, listings, or users, it may be best kept separate.

6. **Breaking changes tolerance**: it's okay changing all admin URLs.

### Current Route Inventory

#### Admin Routes (admin.py - to be distributed)
- **Dashboard**: `GET /admin/dashboard` → `admin.admin_dashboard`
- **Categories**: 4 endpoints
  - `GET /admin/categories` → `admin.admin_categories`
  - `GET/POST /admin/categories/new` → `admin.admin_category_new`
  - `GET/POST /admin/categories/edit/<id>` → `admin.admin_category_edit`
  - `POST /admin/categories/delete/<id>` → `admin.admin_category_delete`
- **Listings**: 3 endpoints
  - `GET /admin/listings` → `admin.admin_listings`
  - `POST /admin/listings/delete/<id>` → `admin.admin_listing_delete`
  - `GET/POST /admin/listings/edit/<id>` → `admin.admin_listing_edit`
  - `POST /admin/listings/delete_selected` → `admin.admin_listing_delete_selected`
- **Users**: 4 endpoints
  - `GET /admin/users` → `admin.admin_users`
  - `GET /admin/users/profile/<id>` → `admin.admin_user_profile`
  - `GET/POST /admin/users/edit/<id>` → `admin.admin_user_edit`
  - `POST /admin/users/delete/<id>` → `admin.admin_user_delete`

#### Public/User Routes (to be consolidated by entity)
- **Listings** (listings.py): 
  - Public: index (`/`), category-filtered browsing (`/<path:category_path>`), detail (`/listing/<id>`)
  - User: create (`/listing/new`), edit (`/listing/edit/<id>`), delete (`/listing/delete/<id>`)
- **Categories** (categories.py): Admin CRUD only, no public listing views
- **Users** (users.py): 2 endpoints for self-service at `/profile` and `/profile/edit`
- **AJAX/API**: Subcategories and breadcrumb endpoints in categories.py at `/api/*` (or alternative namespace TBD)

### Authorization Patterns to Preserve

1. **User self-service**: Use `@login_required` only
2. **Owner or admin check**: Inline logic `if listing.user_id != current_user.id and not current_user.is_admin`
3. **Last admin safeguards**: Prevent demoting/deleting last admin (check `User.query.filter_by(is_admin=True).count()`)

### Authorization Patterns to refactor

1. **Admin routes**: use `@login_required` decorator, and make sure `@admin_required` imply `@login_required`.

### Special Logic to Preserve

1. **Temp-commit-move pattern** (file safety): Used by all listing image operations
2. **Category cycle prevention**: Both route-level UX checks and model-level validation
3. **Cascade category deletion**: Check descendants for listings before allowing deletion
4. **Thumbnail creation**: Via `utils.create_thumbnail()` function

### Template Updates Required

Files containing `url_for('admin.*')` references:
- `templates/base.html` (navbar links)
- `templates/admin/admin_categories.html`
- `templates/admin/admin_listings.html`
- `templates/admin/admin_users.html`
- `templates/admin/admin_dashboard.html`
- `templates/listings/listing_detail.html` (make edit link visible to admins)
- `templates/listings/listing_form.html` (cancel buttons)

### Implementation Approach

**Hierarchical category URLs with `/admin` prefix for admin routes**

This approach provides clean public URLs and clear admin separation:

- Admin category routes: `/admin/categories/*` in `categories.py`
- Category-filtered listing browsing: `/<path:category_path>` in `listings.py` (e.g., `/vehicles`, `/vehicles/motorcycles`)
- Admin listing routes: `/admin/listings/*` in `listings.py`
- Public listing routes: `/` (homepage), `/listing/<id>` (detail) in `listings.py`
- Admin user routes: `/admin/users/*` in `users.py`
- User self-service: `/profile`, `/profile/edit` in `users.py`
- Dashboard: `/admin/dashboard` in `admin_dashboard.py`
- AJAX/API: `/api/subcategories/<id>`, `/api/category_breadcrumb/<id>` in `categories.py` (namespace TBD)

**Reserved route names** (cannot be used as category `url_name`):
- `admin`, `auth`, `profile`, `listing`, `api`, `static`, `new`, `edit`, `delete`, `utils`

**Blueprint registration order** (specific before catch-all):
1. `auth_bp` (`/auth`)
2. `admin_dashboard_bp` (`/admin`)
3. `categories_bp` (prefix varies: `/admin/categories` for admin, possibly no prefix for AJAX)
4. `users_bp` (no prefix, handles `/profile` and `/admin/users/*`)
5. `errors_bp` (no prefix)
6. `listings_bp` (no prefix, handles `/`, `/listing/*`, `/admin/listings/*`, and catch-all `/<path:category_path>` LAST)

### Testing Checklist

After implementation:
- [ ] All admin category management works (create, edit, delete, list)
- [ ] Public category browsing works (shows listings filtered by category)
- [ ] All admin listing management works
- [ ] Public listing browsing works
- [ ] User creation, editing (admin) works
- [ ] User self-service profile editing works
- [ ] Last admin protection still works
- [ ] Temp-commit-move pattern still works for images
- [ ] Category cycle prevention still works
- [ ] All navbar links work
- [ ] All template buttons/links work
- [ ] AJAX endpoints work (subcategories, breadcrumb)
- [ ] Error pages still render correctly
- [ ] No import errors
- [ ] No blueprint conflicts
- [ ] `@admin_required` implies `@login_required`
- [ ] Hierarchical category URLs work (`/vehicles`, `/vehicles/motorcycles`)
- [ ] Can navigate up by trimming URL path segments
- [ ] Reserved route names don't conflict with categories
- [ ] Profile URLs work without IDs (`/profile`, `/profile/edit`)
- [ ] Category `url_name` migration applied and backfilled
- [ ] AJAX endpoints at `/api/*` work correctly

### Risk Mitigation

1. **Template URL references**: Use grep/search to find ALL `url_for('admin.*')` and update systematically
2. **Import errors**: Update all imports when moving code between files
3. **Blueprint conflicts**: Ensure unique blueprint names across all modules
4. **Test coverage**: Manually test each moved endpoint after changes
5. **Rollback plan**: Commit each phase separately for easy rollback if needed

### Additional Clarifications and Improvements

- **All `/api/*` endpoints return JSON only** (never HTML). This is for AJAX, future REST, or PWA use. Document this in route docstrings and comments.
- **Entity separation in `/api/*` namespace:**
  - Use `/api/categories/breadcrumb/<id>` and `/api/categories/children/<parent_id>` (not `/api/category_breadcrumb/<id>` or `/api/subcategories/<id>`)
  - "Children" is preferred over "subcategories" since the model is recursive and supports multiple levels. Example: `/api/categories/children/vehicles` returns direct children of "vehicles".
  - Future endpoints for listings, users, etc. should follow `/api/listings/...`, `/api/users/...` for consistency.
- **Reserved route names:**
  - Explicitly list reserved names in migration and validation logic: `admin`, `auth`, `profile`, `listing`, `api`, `static`, `new`, `edit`, `delete`, `utils`, `categories`, `users`, `listings`, `dashboard`.
  - Validate on category creation/edit to prevent conflicts.
- **Blueprint registration order:**
  - Catch-all route for category-filtered listings (`/<path:category_path>`) in `listings.py` must be registered last to avoid conflicts with other routes.
  - Document this in `app/__init__.py` and in the plan for future maintainers.
- **Testing checklist additions:**
  - [ ] All `/api/*` endpoints return correct JSON and are not accessible as HTML pages
  - [ ] Reserved route names are enforced and do not conflict with categories
  - [ ] Category children endpoint works for all levels
  - [ ] Breadcrumb endpoint returns correct hierarchy
- **Migration step:**
  - Backfill `url_name` for all existing categories
  - Validate uniqueness within siblings and against reserved names
  - Document migration steps and add a CLI script for backfilling if needed
  - **IMPORTANT**: Use SQLite-compatible migration patterns (no `ALTER COLUMN`, use `server_default` for NOT NULL columns)
- If **opening a new terminal to run commands for checking/testing, first load the venv** (`source /home/ferabreu/Code/classifieds/venv/bin/activate`), so that all the required dependencies and utilities are available. Prefer to run commands on an already opened terminal with the venv loaded.
