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
- **Service Layer Pattern**: Models = data definitions, Services = business logic/orchestration, Routes = thin HTTP handlers, Helpers = technical utilities (even if just 1 function)
- **String References**: Use `relationship("ModelName", back_populates="attribute")` for all cross-entity relationships (SQLAlchemy 2.x standard, prevents circular imports)
- **Bidirectional Relationships**: Add reciprocal `back_populates` on both sides per SQLAlchemy 2.x standard (Category.listings ↔ Listing.category, User.listings ↔ Listing.owner)
- **No Circular Imports**: Prevent circular imports through design (string references, extensions.py, proper import order) - verify through testing
- **Template Organization**: Move templates into entity packages with explicit `template_folder='templates'` configuration
- **Data Structures**: Services return data dictionaries (flexible, matches current pattern)
- **Current Standards**: SQLAlchemy 2.x with `Mapped[]` type hints, no deprecated methods

---

## Steps

### 0. Preparation: Tests, documentation, and migration audit

Create test fixtures in `tests/conftest.py` for services layer testing (mock Category, User, Listing objects, mock db session); audit ALL migration files in `migrations/versions/` and update any import statements from old paths (`from app.models import`) to new entity paths (`from app.categories.models import Category`, `from app.users.models import User`, `from app.listings.models import Listing, ListingImage`) - migrations must continue to work; append to `.github/instructions/python-flask.instructions.md` a new section "Entity Creation Pattern" documenting the standard structure for new entities: package with `__init__.py` (blueprint factory with `template_folder='templates'`), `models.py` (SQLAlchemy models with string references), `forms.py` (WTForms), `services.py` (business logic returning dicts), `routes/` package with `__init__.py`/`admin.py`/`public.py`/`helpers.py` (as needed), `templates/entityname/` directory; document blueprint registration order requirement in same file.

**Test**: run existing test suite to establish baseline, verify migrations can still run with updated imports

---

### 1. Foundation: Extensions and shared utilities

Create `app/extensions.py` with `db = SQLAlchemy()`, `login_manager = LoginManager()`, `mail = Mail()`, `migrate = Migrate()` extracted from `app/__init__.py` and `app/models.py`; create `app/shared/` package with `__init__.py`, `utils.py` moving all functions from `app/routes/utils.py` (`generate_thumbnail`, `commit_file`, `rollback_file`, `finalize_file`, `cleanup_temp_files`, `move_image_files_to_temp`, `restore_files_from_temp`) and `decorators.py` extracting `admin_required`, `login_required` from `app/routes/decorators.py`; update `app/__init__.py` to import from extensions with proper initialization order (`db.init_app(app)` before any model imports to prevent circular imports).

**Test**: run app startup, verify no import errors or circular import warnings, check that no module imports create cycles

---

### 2. Auth entity: Extract authentication with service layer

Create `app/auth/` package with:
- `__init__.py` creating `auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')`
- `models.py` (empty file with comment `# Placeholder for future OAuth/session tracking models`)
- `forms.py` (extract from `app/forms.py`: `RegistrationForm`, `LoginForm`, `ForgotPasswordForm`, `ResetPasswordForm` with all validators and methods)
- `services.py` (create `send_password_reset_email(user, reset_url)` extracting email orchestration and MAIL_SERVER check/fallback logic from `app/routes/auth.py`, function returns dict with `{'success': bool, 'method': 'email'|'flash'}`)
- `services/` package with `__init__.py` and `ad_validator.py` (move entire `app/ldap_auth.py` contents preserving all functions)
- `routes/` package with `__init__.py`, `local.py` (extract login, register, logout routes from `app/routes/auth.py` calling auth services with thin route handlers), `password.py` (extract forgot_password, reset_password routes calling `send_password_reset_email` service)
- `templates/auth/` directory (move login.html, register.html, forgot_password.html, reset_password.html from `app/templates/`)

Update `app/__init__.py` to import `from app.auth import auth_bp` and register it; update all auth route `render_template()` calls to "auth/login.html" etc.

**Test**: app starts with no circular imports, login flow (local and LDAP if configured), registration with validation, password reset with email, password reset with flash fallback, logout

---

### 3. Categories entity: Extract with hierarchy services

Create `app/categories/` package with:
- `__init__.py` creating `categories_bp = Blueprint('categories', __name__, url_prefix='/categories', template_folder='templates')`
- `models.py` (extract `Category`, `CategoryView`, `RESERVED_CATEGORY_NAMES` constant from `app/models.py`, ensure all relationships use string references: `parent: Mapped[Optional["Category"]] = relationship("Category", remote_side="Category.id", back_populates="children", ...)`, `children: Mapped[List["Category"]] = relationship("Category", back_populates="parent", ...)`, **add reciprocal** `listings: Mapped[List["Listing"]] = relationship("Listing", back_populates="category")` per SQLAlchemy 2.x standard, move cycle detection SQLAlchemy event listener `@event.listens_for(Session, "before_flush")` from `app/models.py` to this file)
- `forms.py` (extract `CategoryForm` from `app/forms.py` with all validators)
- `services.py` (extract business logic from `app/routes/categories.py`: create `validate_category_inputs(name, url_name, parent_id, category_id=None)` with cycle detection and reserved name checking returning `dict{'valid': bool, 'error': str|None}`, `count_listings_recursive(category_id)` returning int, move `_validate_category_inputs` and `_count_listings_recursive` helper functions into services, move `generate_url_name()` function from `app/models.py` here)
- `routes/` package with `__init__.py`, `admin.py` (CRUD routes from `app/routes/categories.py` calling category services), `public.py` (API endpoints: `get_children`, `get_breadcrumb` from `app/routes/categories.py`), evaluate if `helpers.py` needed (only create if non-business-logic utilities remain after service extraction)
- `templates/categories/` (move category_form.html, admin_categories.html from `app/templates/`)

Register `categories_bp` in `app/__init__.py`.

**Test**: app starts with no circular imports, category CRUD operations, hierarchy validation prevents cycles, reserved name validation, listing count in tree, API endpoints return correct JSON, breadcrumb generation

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
- `services.py` (extract from `app/routes/listings/helpers.py`: create `get_showcase_data(category_path=None)` returning `dict{'category': Category|None, 'category_showcases': list[dict], 'any_categories_exist': bool}` for reuse by main blueprint, `get_index_showcase_categories()` returning `list[Category]`, `build_category_showcases(categories, display_slots, fetch_limit)` returning `list[dict]`, `create_listing_with_images(form_data, files, user_id)` orchestrating listing creation and image processing using shared utils returning `dict{'success': bool, 'listing': Listing|None, 'error': str|None}`, `delete_listing_with_cleanup(listing_id)` with file cleanup using ACID pattern, `update_listing_images(listing_id, new_files)` for image updates, extract ALL business logic from helpers following service layer pattern)
- `routes/` package with `__init__.py`, `public.py` (listing detail, category view with path routing `/<path:category_path>`, listing create, edit, delete routes from `app/routes/listings/routes.py` calling listing services), `admin.py` (admin listing list with pagination/sorting, bulk delete operations from `app/routes/listings/routes.py` admin section calling services), evaluate `helpers.py` for any listing-specific formatters/utilities after service extraction (only create if such utilities exist)
- `templates/listings/` (move listing_detail.html, listing_form.html, admin_listings.html from `app/templates/`)

Register `listings_bp` in `app/__init__.py`.

**Test**: app starts with no circular imports, listing CRUD with images and thumbnails, category filtering works, showcase display with configured categories, admin bulk operations, image upload with ACID file operations, no N+1 queries in showcase loading (verify with performance tests from Step 0)

---

### 6. Main blueprint: Global pages reusing services

Create `app/main/` package with:
- `__init__.py` creating `main_bp = Blueprint('main', __name__, template_folder='templates')` (no url_prefix, explicit template_folder pointing to shared templates)
- `routes.py` containing: import `from app.listings.services import get_showcase_data`, create index route `@main_bp.route('/')` calling `data = get_showcase_data()` and `render_template('index.html', **data)` demonstrating service layer reuse without code duplication, extract all error handlers from `app/routes/errors.py` (`@main_bp.app_errorhandler(404)`, `@main_bp.app_errorhandler(500)`, `@main_bp.app_errorhandler(403)`), extract admin dashboard route from `app/routes/admin.py`

Keep shared templates in `app/templates/` root directory (base.html, error.html, index.html remain global NOT moved, macros/ directory stays global, admin/dashboard.html stays global - these are NOT entity-specific); configure main_bp template_folder to point to shared app/templates; register `main_bp` in `app/__init__.py`.

**Test**: app starts with no circular imports, index page displays showcases correctly using listings service, error pages render (404/500/403), admin dashboard shows statistics, shared templates and macros work

---

### 7. App factory: Update registrations and imports

Comprehensively update `app/__init__.py`:
- Import extensions `from app.extensions import db, login_manager, mail, migrate`
- Import all blueprints (`from app.main import main_bp`, `from app.auth import auth_bp`, `from app.categories import categories_bp`, `from app.users import users_bp`, `from app.listings import listings_bp`)
- Register blueprints in **CRITICAL ORDER** with prominent multi-line comment block:
  - Register `main_bp` first (handles index and errors)
  - Then `auth_bp`, `categories_bp`, `users_bp`
  - Then add comment block:
    ```python
    # CRITICAL: listings_bp MUST be registered LAST
    # Due to catch-all /<path:url_path> route that would shadow other blueprints
    # if registered earlier. DO NOT change this order.
    ```
  - Register `listings_bp` last
- Update context processors to import `from app.categories.models import Category` and `from app.users.models import User`
- Update `login_manager.user_loader` to import from `app.users.models`
- Context processors remain global in app factory (they inject data into ALL templates)
- Remove all old imports from deleted files
- Verify no circular imports in initialization order

**Test**: app starts with no circular imports, all routes accessible at correct paths, context processors work (navbar categories, title separator injected), blueprint order correct (listings doesn't shadow other routes)

---

### 8. Global import updates, testing, and cleanup

Systematically update:
- `app/cli/demo.py` and `app/cli/maintenance.py` to import from new entity structure (`from app.listings.models import Listing, ListingImage`, `from app.categories.models import Category`, `from app.users.models import User`, `from app.shared.utils import generate_thumbnail`)
- ALL test files in `tests/` to import from entity packages (test_admin_routes.py, test_auth.py, test_category_cycle_protection.py, test_listings.py, test_users_routes.py, update fixtures in conftest.py)
- Systematically search and update ALL `render_template()` calls throughout new entity route files to use entity-prefixed paths (auth routes: "auth/login.html", categories routes: "categories/form.html", listings routes: "listings/detail.html", users routes: "users/profile.html")

Delete obsolete files:
- `app/models.py`
- `app/forms.py`
- Entire `app/routes/` directory
- `app/ldap_auth.py`

Run syntax checker, import validator, code formatter (black, isort).

**Comprehensive manual testing**:
- App startup without errors or circular import warnings
- Auth flows (login/register/logout/password-reset with email+fallback/LDAP if configured)
- Category operations (CRUD/hierarchy/cycle-detection/API-endpoints)
- User operations (profile-view-edit/admin-list-with-pagination-sorting/admin-edit-delete/last-admin-protection/cascade-checks)
- Listing operations (CRUD-with-images/category-filtering/showcase-display/admin-bulk-operations/thumbnail-generation/ACID-file-operations)
- Global pages (index-with-showcases/error-pages-404-500-403/admin-dashboard)
- Template rendering (all entity templates/shared-templates/macros/context-processors)

Run full test suite including performance tests from Step 0; verify no N+1 queries in critical paths; verify all migrations still work with updated imports.

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
