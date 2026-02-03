# Plan: Entity-Based Blueprint Refactoring with Service Layer Pattern

**Date:** 2026-02-01 (Updated: 2026-02-02)  
**Author:** GitHub Copilot (Claude Sonnet 4.5), updated by ferabreu 
**Issue:** https://github.com/ferabreu/classifieds/issues/87  
**Goal:** Refactor codebase to entity-based Flask's Blueprint pattern with Service Layer architecture

---

## Agent Role

You are an experienced developer versed in software development best practices with excellent knowledge of the Pythonic Way. You will optimize database query performance by refactoring an N+1 query pattern into efficient batch operations while maintaining identical user-facing behavior.

---

## Objective

Comprehensive, global refactoring of the entire Flask application from monolithic architecture to entity-based blueprint structure with service layer pattern. This affects EVERY part of the application - models, forms, routes, templates, tests, and migrations.

---

## Core Principles (Apply Throughout):

- **NO DEPRECATED METHODS**: Use current best practices (SQLAlchemy 2.x, Flask latest patterns)
- **Service Layer Pattern**: Models = data definitions, Services = business logic/orchestration, Routes = thin HTTP handlers (see detailed rules below)
- **String References**: Use `relationship("ModelName", back_populates="attribute")` for all cross-entity relationships (SQLAlchemy 2.x standard, prevents circular imports)
- **Bidirectional Relationships**: Add reciprocal `back_populates` on both sides per SQLAlchemy 2.x standard (Category.listings ↔ Listing.category, User.listings ↔ Listing.owner)
- **No Circular Imports**: Prevent circular imports through design (string references, extensions.py, proper import order) - verify through testing
- **Template Organization**: Move templates into entity packages with explicit `template_folder='templates'` configuration for entity blueprints; main blueprint uses shared app/templates/ by default (no template_folder parameter)
- **Data Structures**: Services return data dictionaries (flexible, matches current pattern)
- **Current Standards**: SQLAlchemy 2.x with `Mapped[]` type hints, no deprecated methods

### Service Layer Pattern - Detailed Rules

**Services** (`entity/services.py`): Business logic that orchestrates models, database operations, and cross-cutting concerns. Returns dictionaries for flexibility.
  - Examples: `validate_category_inputs()`, `create_listing_with_images()`, `send_password_reset_email()`
  - Use for: validation logic, multi-step operations, data transformation for views
  
**Shared Utils** (`app/shared/utils.py`): Cross-entity technical utilities with NO business logic. Pure functions.
  - Examples: `create_thumbnail()`, `move_image_files_to_temp()`, `cleanup_temp_files()`
  - Use for: file operations, image processing, data formatting
  - These are NOT entity-specific and can be used by any entity

**Route Helpers** (`entity/routes/helpers.py`): Entity-specific technical utilities (NOT business logic). RARE - only create if truly needed.
  - Examples: `parse_listing_sort_params()`, `format_category_breadcrumb_json()`
  - Use for: HTTP-specific formatting, query parameter parsing (if not reusable as service)
  - **DO NOT create helpers.py unless absolutely necessary** - most "helpers" are actually services or shared utils
  
**Models** (`entity/models.py`): Data definitions AND utility methods that operate on single instances.
  - Examples: Category model with `generate_url_name()` function (used by `__init__`), `User.check_password()`
  - Keep standalone utilities that models depend on IN the models file (prevents circular imports)
  
**Routes** (`entity/routes/*.py`): Thin HTTP handlers that call services and return responses.
  - Responsibilities: request validation, calling services, flash messages, redirects, render_template
  - Do NOT put business logic in routes - extract to services

---

## Steps

### 0. Preparation: Tests, documentation, and migration audit

Create test fixtures in `tests/conftest.py` for services layer testing (mock Category, User, Listing objects, mock db session); append to `.github/instructions/python-flask.instructions.md` a new section "Entity Creation Pattern" documenting the standard structure for new entities: package with `__init__.py` (blueprint factory, `template_folder='templates'` for entity-specific templates), `models.py` (SQLAlchemy models with string references), `forms.py` (WTForms), `services.py` (business logic returning dicts), `routes/` package with `__init__.py`/`admin.py`/`public.py` (helpers.py only if technical utilities remain after service extraction), `templates/entityname/` directory; document blueprint registration order requirement and service layer pattern distinction (services=business logic, shared/utils=cross-entity utilities, helpers=rare technical utilities) in same file.

**Test**: run existing test suite to establish baseline (`python -m pytest`), verify app starts without circular imports (`python -c "from app import create_app; create_app()"`).

---

### 1. Foundation: Extensions and shared utilities

Create `app/extensions.py` with `db = SQLAlchemy()`, `login_manager = LoginManager()`, `mail = Mail()`, `migrate = Migrate()` extracted from `app/__init__.py` and `app/models.py`; create `app/shared/` package with `__init__.py`, `utils.py` moving all functions from `app/routes/utils.py` (`create_thumbnail`, `move_image_files_to_temp`, `restore_files_from_temp`, `cleanup_temp_files`, `commit_file`, `rollback_file`, `finalize_file` - preserve ACID file operation pattern), and `decorators.py` moving ALL decorators from `app/routes/decorators.py` (`admin_required`, `owner_or_admin_check` - note: these use `flask_login.login_required` and `flask_login.current_user`, not custom login_required); update `app/__init__.py` to import from extensions with proper initialization order (`db.init_app(app)` before any model imports to prevent circular imports).

**Test**: run app startup (`python -c "from app import create_app; app = create_app(); print('Success')"`), verify no import errors or circular import warnings, check that decorators work correctly

---

### 2. Auth entity: Extract authentication with service layer

Create `app/auth/` package with:
- `__init__.py` creating `auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')`
- `models.py` (empty file with comment `# Placeholder for future OAuth/session tracking models`)
- `forms.py` (extract from `app/forms.py`: `RegistrationForm`, `LoginForm`, `ForgotPasswordForm`, `ResetPasswordForm` with all validators and methods)
- `services.py` (create `send_password_reset_email(user, reset_url)` extracting email orchestration and MAIL_SERVER check/fallback logic from `app/routes/auth.py`, function returns dict with `{'success': bool, 'method': 'email'|'flash'}`)
- `services/` package with `__init__.py` and `ad_validator.py` (move entire `app/ldap_auth.py` contents preserving ALL functions including configuration checks - LDAP functions must check if LDAP_SERVER and LDAP_DOMAIN are configured before attempting authentication)
- `routes/` package with `__init__.py`, `local.py` (extract login, register, logout routes from `app/routes/auth.py` calling auth services with thin route handlers - preserve LDAP config check: `ldap_enabled = bool(current_app.config.get('LDAP_SERVER') and current_app.config.get('LDAP_DOMAIN'))`), `password.py` (extract forgot_password, reset_password routes calling `send_password_reset_email` service)
- `templates/auth/` directory (move login.html, register.html, forgot_password.html, reset_password.html from `app/templates/`)

Update `app/__init__.py` to import `from app.auth import auth_bp` and register it; update all auth route `render_template()` calls to "auth/login.html" etc.

**Test**: app starts with no circular imports, login flow (local and LDAP if configured), registration with validation, password reset with email, password reset with flash fallback, logout

---

### 3. Categories entity: Extract with hierarchy services

Create `app/categories/` package with:
- `__init__.py` creating `categories_bp = Blueprint('categories', __name__, url_prefix='/categories', template_folder='templates')`
- `models.py` (extract `Category`, `CategoryView`, `RESERVED_CATEGORY_NAMES` constant, AND `generate_url_name()` function from `app/models.py` - CRITICAL: keep generate_url_name here because Category.__init__ uses it, moving to services would create circular imports; ensure all relationships use string references: `parent: Mapped[Optional["Category"]] = relationship("Category", remote_side="Category.id", back_populates="children", ...)`, `children: Mapped[List["Category"]] = relationship("Category", back_populates="parent", ...)`, **add reciprocal** `listings: Mapped[List["Listing"]] = relationship("Listing", back_populates="category")` per SQLAlchemy 2.x standard, move cycle detection SQLAlchemy event listener `@event.listens_for(Session, "before_flush")` from `app/models.py` to this file)
- `forms.py` (extract `CategoryForm` from `app/forms.py` with all validators, import `from app.categories.models import generate_url_name, RESERVED_CATEGORY_NAMES`)
- `services.py` (extract business logic from `app/routes/categories.py`: create `validate_category_inputs(name, url_name, parent_id, category_id=None)` with cycle detection and reserved name checking returning `dict{'valid': bool, 'error': str|None}`, `count_listings_recursive(category_id)` returning int, move `_validate_category_inputs` and `_count_listings_recursive` helper functions into services; can import `generate_url_name` from `.models` if needed)
- `routes/` package with `__init__.py`, `admin.py` (CRUD routes from `app/routes/categories.py` calling category services), `public.py` (API endpoints: `get_children`, `get_breadcrumb` from `app/routes/categories.py`), do NOT create `helpers.py` unless non-business-logic technical utilities remain after service extraction (unlikely)
- `templates/categories/` (move category_form.html, admin_categories.html from `app/templates/`)

Register `categories_bp` in `app/__init__.py`; IMPORTANT: add early import for event listener registration: `from app.categories.models import Category  # Register cycle detection event listener` with comment.

**Test**: app starts with no circular imports, category CRUD operations, hierarchy validation prevents cycles, reserved name validation, listing count in tree, API endpoints return correct JSON, breadcrumb generation, cycle detection listener works

---

### 4. Users entity: Extract with validation services

Create `app/users/` package with:
- `__init__.py` creating `users_bp = Blueprint('users', __name__, url_prefix='/users', template_folder='templates')`
- `models.py` (extract `User` model from `app/models.py`, preserve UserMixin, all methods like `set_password`, `check_password`, **add reciprocal** `listings: Mapped[List["Listing"]] = relationship("Listing", back_populates="owner")` per SQLAlchemy 2.x standard)
- `forms.py` (extract `UserEditForm` from `app/forms.py`)
- `services.py` (extract business logic: create `can_delete_user(user_id)` checking if last admin and listing ownership from `app/routes/users.py` deletion logic returning `dict{'can_delete': bool, 'reason': str|None}`, `get_user_statistics(user_id)` if dashboard needs it returning dict, extract any other business logic from route handlers into service functions)
- `routes/` package with `__init__.py`, `public.py` (profile view/edit routes from `app/routes/users.py` approximately first 80 lines calling user services), `admin.py` (user list with pagination/sorting, admin user edit/delete from `app/routes/users.py` remaining lines calling user services), evaluate `helpers.py` (only if technical utilities remain)
- `templates/users/` (move user_profile.html, user_form.html, admin_users.html from `app/templates/`)

Update `login_manager.user_loader` in `app/__init__.py` to import `from app.users.models import User`; register `users_bp`.

**Test**: app starts with no circular imports, user profile view and edit, admin user list with pagination and sorting, admin user edit, user deletion blocked if last admin, user deletion cascade checks for listings, login_manager.user_loader works

---

### 5. Listings entity: Refactor with showcase services

Create `app/listings/` package with:
- `__init__.py` creating `listings_bp = Blueprint('listings', __name__, template_folder='templates')` (no url_prefix for catch-all routes)
- `models.py` (extract `Listing`, `ListingImage` from `app/models.py`, **critical use string references with back_populates**: `category: Mapped["Category"] = relationship("Category", back_populates="listings")` and `owner: Mapped["User"] = relationship("User", back_populates="listings")` following SQLAlchemy 2.x bidirectional pattern)
- `forms.py` (extract `ListingForm` from `app/forms.py`)
- `services.py` (extract from `app/routes/listings/helpers.py`: create `get_showcase_data(category_path=None)` returning `dict{'category': Category|None, 'category_showcases': list[dict], 'any_categories_exist': bool}` for reuse by main blueprint, `get_index_showcase_categories()` returning `list[Category]`, `build_category_showcases(categories, display_slots, fetch_limit)` returning `list[dict]`, `create_listing_with_images(form_data, files, user_id)` orchestrating listing creation and image processing returning `dict{'success': bool, 'listing': Listing|None, 'error': str|None}`, `delete_listing_with_cleanup(listing_id)` with file cleanup, `update_listing_images(listing_id, new_files)` for image updates, extract ALL business logic from helpers following service layer pattern; CRITICAL: preserve ATOMIC file operations pattern from current helpers.py - services must import from `app.shared.utils`: `create_thumbnail`, `move_image_files_to_temp`, `restore_files_from_temp`, `cleanup_temp_files`; pattern is: 1) stage files to temp, 2) attempt DB commit, 3) if success: finalize/cleanup temp, 4) if failure: restore from temp and rollback; see current `_delete_listing_impl` and `_edit_listing_impl` for reference implementations)
- `routes/` package with `__init__.py`, `public.py` (listing detail `/listing/<int:listing_id>`, listing create `/new`, edit `/edit/<id>`, delete `/delete/<id>`, category view with catch-all path routing `/<path:category_path>` - MUST be defined LAST in file, index route `/` moved to main blueprint), `admin.py` (admin listing list `/admin/listings` with pagination/sorting, bulk delete operations from `app/routes/listings/routes.py` admin section calling services), do NOT create `helpers.py` unless listing-specific technical utilities remain after service extraction (unlikely)
- `templates/listings/` (move listing_detail.html, listing_form.html, admin_listings.html from `app/templates/`)

Register `listings_bp` in `app/__init__.py`.

**Test**: app starts with no circular imports, listing CRUD with images and thumbnails, category filtering works, showcase display with configured categories, admin bulk operations, image upload with ACID file operations (stage→commit→finalize/rollback), no N+1 queries in showcase loading

---

### 6. Main blueprint: Global pages reusing services

Create `app/main/` package with:
- `__init__.py` creating `main_bp = Blueprint('main', __name__)` (no url_prefix, NO template_folder parameter - Flask will use app/templates/ by default for shared templates)
- `routes.py` containing: import `from app.listings.services import get_showcase_data`, create index route `@main_bp.route('/')` calling `data = get_showcase_data()` and `render_template('index.html', **data)` demonstrating service layer reuse without code duplication, extract all error handlers from `app/routes/errors.py` (`@main_bp.app_errorhandler(404)`, `@main_bp.app_errorhandler(500)`, `@main_bp.app_errorhandler(403)` - these use `render_template('error.html', ...)`), extract admin dashboard route from `app/routes/admin.py` (route: `/admin/dashboard`, uses `render_template('admin/dashboard.html', ...)`)

Keep shared templates in `app/templates/` root directory (base.html, error.html, index.html remain global NOT moved, macros/ directory stays global, admin/dashboard.html stays in admin/ subdirectory - these are NOT entity-specific); main_bp accesses these via default Flask template resolution; register `main_bp` in `app/__init__.py`.

**Test**: app starts with no circular imports, index page displays showcases correctly using listings service, error pages render (404/500/403), admin dashboard shows statistics, shared templates and macros work

---

### 7. App factory: Update registrations and imports

Comprehensively update `app/__init__.py`:
- Import extensions `from app.extensions import db, login_manager, mail, migrate`
- Import all blueprints (`from app.main import main_bp`, `from app.auth import auth_bp`, `from app.categories import categories_bp`, `from app.users import users_bp`, `from app.listings import listings_bp`)
- Import models for event listeners and context processors: `from app.categories.models import Category  # Register cycle detection event listener` and `from app.users.models import User`
- Register blueprints in **CRITICAL ORDER** with prominent multi-line comment block:
  - Register `main_bp` first (no prefix, handles `/` index route and error handlers)
  - Then `auth_bp` (prefix `/auth`)
  - Then `categories_bp` (prefix `/categories` for admin routes, no prefix for API routes like `/api/categories/*`)
  - Then `users_bp` (no prefix, handles `/profile`, `/profile/edit`, `/admin/users/*`)
  - Then add comment block:
    ```python
    # CRITICAL: listings_bp MUST be registered LAST
    # Due to catch-all /<path:category_path> route that would shadow other blueprints
    # if registered earlier. DO NOT change this order.
    ```
  - Register `listings_bp` last (no prefix, contains catch-all route)
- DO NOT register `utils_bp` or `errors_bp` - these don't exist after refactoring (utils moved to app/shared/utils.py as module not blueprint, errors moved to main_bp routes)
- Update context processors to import `from app.categories.models import Category` and `from app.users.models import User`
- Update `login_manager.user_loader` to import from `app.users.models`
- Context processors remain global in app factory (they inject data into ALL templates)
- Remove all old imports from deleted files
- Verify no circular imports in initialization order (extensions initialized before model imports)

**Test**: app starts with no circular imports (`python -c "from app import create_app; app = create_app(); print('✓ No circular imports')"`), all routes accessible at correct paths, context processors work (navbar categories, title separator injected), blueprint order correct (listings catch-all doesn't shadow other routes), error handlers work

---

### 8. Global import updates, testing, and cleanup

Systematically update:
- `app/cli/demo.py` and `app/cli/maintenance.py` to import from new entity structure (`from app.listings.models import Listing, ListingImage`, `from app.categories.models import Category`, `from app.users.models import User`, `from app.shared.utils import create_thumbnail` - note: renamed from generate_thumbnail)
- ALL test files in `tests/` to import from entity packages (test_admin_routes.py, test_auth.py, test_category_cycle_protection.py, test_listings.py, test_users_routes.py, update fixtures in conftest.py to import from entity models)
- Systematically search and update ALL `render_template()` calls using grep:
  ```bash
  # Find all files with render_template calls
  grep -r "render_template" app/ --include="*.py" | cut -d: -f1 | sort -u
  ```
  For each entity route file, update paths:
  - Auth routes (`app/auth/routes/*.py`): "login.html" → "auth/login.html", "register.html" → "auth/register.html", "forgot_password.html" → "auth/forgot_password.html", "reset_password.html" → "auth/reset_password.html"
  - Categories routes (`app/categories/routes/*.py`): "category_form.html" → "categories/form.html", "admin_categories.html" → "categories/admin.html"
  - Listings routes (`app/listings/routes/*.py`): "listing_detail.html" → "listings/listing.html", "listing_form.html" → "listings/form.html", "admin_listings.html" → "listings/admin.html"
  - Users routes (`app/users/routes/*.py`): "user_profile.html" → "users/profile.html", "user_form.html" → "users/form.html", "admin_users.html" → "users/admin.html"
  - Main routes (`app/main/routes.py`): Keep as-is ("index.html", "error.html", "admin/dashboard.html" - these are shared templates)

Delete obsolete files:
- `app/models.py`
- `app/forms.py`
- Entire `app/routes/` directory
- `app/ldap_auth.py`

Run code quality checks:
```bash
python -m pytest tests/test_syntax.py  # Syntax validation
python -c "from app import create_app; create_app()"  # Circular import check
black app/ tests/  # Format code
isort app/ tests/  # Sort imports
```

**Comprehensive manual testing** (test each item and check off):
- ✓ App startup without errors or circular import warnings
- ✓ Auth flows (login/register/logout/password-reset with email+fallback/LDAP if configured)
- ✓ Category operations (CRUD/hierarchy/cycle-detection/API-endpoints)
- ✓ User operations (profile-view-edit/admin-list-with-pagination-sorting/admin-edit-delete/last-admin-protection/cascade-checks)
- ✓ Listing operations (CRUD-with-images/category-filtering/showcase-display/admin-bulk-operations/thumbnail-generation/ACID-file-operations)
- ✓ Global pages (index-with-showcases/error-pages-404-500-403/admin-dashboard)
- ✓ Template rendering (all entity templates/shared-templates/macros/context-processors)

Run full test suite:
```bash
python -m pytest  # All tests must pass
flask db upgrade  # Verify migrations work
```

Verify no N+1 queries in critical paths (showcase loading, pagination); verify all migrations still work.

---

## Success Criteria

- ✅ No circular imports in any part of the application
- ✅ All tests pass (including new performance tests)
- ✅ All migrations run successfully with updated imports
- ✅ Service layer enables code reuse (main blueprint uses listings services)
- ✅ Clear separation: models (data), services (logic), routes (HTTP), helpers (utilities)
- ✅ Consistent entity structure across all blueprints
- ✅ Blueprint registration order documented and enforced
- ✅ Template organization follows entity-based pattern
- ✅ SQLAlchemy 2.x patterns with bidirectional relationships
- ✅ No N+1 queries in showcase/pagination logic

---
