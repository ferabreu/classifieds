<!-- Copilot instructions for the `classifieds` Flask app -->
# Quick orientation for automated coding assistants

## Code style & standards

Follow these lightweight, project-specific conventions on every edit to keep the codebase consistent and reviewable.

- Python formatting and tooling
  - Follow PEP 8. Use 4 spaces for indentation.
  - Prefer Black for automatic formatting (line length 88) and isort for import ordering.
  - Run a basic import/test smoke check after edits:
    - python -m pyflakes . || true
    - python -c "import importlib; importlib.import_module('app')"
  - Use descriptive names (snake_case for functions/variables, PascalCase for classes). Avoid single-letter names except for short loops.
  - Prefer single quotes for Python strings where not conflicting with content; let Black / team tooling normalize quotes automatically.
  - Add type hints for public functions where helpful.

- Imports & modules
  - Avoid wildcard imports. Use explicit imports.
  - Order imports: stdlib, third-party, local (use isort).
  - Add new helper functions in existing utilities modules (e.g., app/routes/utils.py) when they logically belong there.

- Flask & SQLAlchemy patterns
  - Follow existing blueprint patterns (bp = Blueprint(...)) and register in create_app().
  - DB & fileflow: always follow the temp -> commit -> move pattern for uploaded files:
    1. Save uploads to current_app.config['TEMP_DIR']
    2. Create thumbnails in TEMP_DIR
    3. db.session.add(...); db.session.commit()
    4. If commit OK: move files to UPLOAD_DIR/THUMBNAIL_DIR
    5. On DB error: delete temp files and rollback
  - Use current_app.config to read dirs and options. Do not hardcode paths.
  - Wrap DB commits in try/except and ensure rollback on errors.

- Jinja templates
  - Keep logic minimal in templates — build and prepare data in view functions.
  - Use macros for reusable markup; place macro files under templates/macros/.
  - Import macros at the start of the block where they are used (improves locality) using namespaced imports:
    - `{% import 'macros/file.html' as file_macros %}`
    - Call as `{{ file_macros.some_macro(...) }}`
  - If multiple blocks require the same macro, consider importing once at top-of-file or in a shared partial.
  - Avoid heavy data transformation in templates. Prefer pre-sorted or pre-structured data (e.g., build nested category trees in the view).
  - Use explicit escaping; only use `|safe` when the content is guaranteed safe.

- HTML / Jinja quoting and whitespace
  - Use double quotes for HTML attributes (consistent with common tooling).
  - Use single quotes inside Jinja expressions when embedding string literals that will be rendered into HTML attributes to minimize escaping conflicts, e.g.:
    - `<a href="{{ url_for('foo', id=item.id) }}">`
  - Use 4-space indentation for HTML/Jinja blocks to match Python indentation visually.

- JavaScript / CSS
  - Prefer placing scripts in `{% block scripts %}` and keep inline scripts minimal.
  - Use modern JS (let/const) and avoid global variables.
  - Load external libraries via the project's pattern (CDN or local) consistent with existing templates.

- Tests / QA
  - There are no automated tests in-repo; run the dev server and exercise critical flows:
    - Create/edit listings (images + thumbnails)
    - Delete listings/images and confirm file cleanup
    - Admin actions (do not remove last admin)
  - Include a short manual QA checklist in PRs when touching uploads or DB changes.

- Misc
  - When changing models, provide migration steps (flask db migrate/upgrade) or document why migrations are deferred.
  - Keep commits focused and include a brief rationale.
  - If unsure, keep changes small and ask for a quick review.


## Project-specific patterns and commands when making changes.

- Project type: Flask (Python 3.10+), single WSGI app in `wsgi.py`. App factory: `app.create_app()` in `app/__init__.py`.
- DB: SQLAlchemy (Flask-SQLAlchemy). Migrations present (Alembic) under `migrations/` but app uses `db.create_all()` in the CLI `flask init` helper for quick local setup.
- Storage: uploaded images in `app/static/uploads/`; thumbnails in `app/static/uploads/thumbnails/`; a TEMP_DIR (`static/temp`) is used for ACID-like file operations. See `app/config.py` and `app/__init__.py` for path resolution.

When editing application logic, prefer these patterns used throughout the codebase:

- Blueprints: routes are grouped by feature under `app/routes/` and registered in `create_app()`. Add new routes as blueprints and register them there.
- DB session and filesystem coordination: the code uses a "move-to-temp, commit DB, then move-to-final (or restore)" pattern for image uploads and deletes. Mirror this pattern when modifying listing/image flows. See `app/routes/listings.py` and `app/routes/admin.py` for examples.
- Thumbnails: creation via `app/routes/utils.create_thumbnail(image_path, thumbnail_path)` (Pillow). Thumbnails are saved as JPEG 224x224, centered on white background. Use this helper rather than inline PIL logic.
- Auth: Flask-Login + optional LDAP. Local password storage uses Werkzeug hashes via `User.set_password()/check_password()`. LDAP auth helper: `app/ldap_auth.authenticate_with_ldap(email, password)` — LDAP is optional and controlled by env vars `LDAP_SERVER` and `LDAP_DOMAIN`.

Useful files to reference or update when changing behavior:

- `app/__init__.py` — app factory, CLI commands: `flask init`, `flask backfill-thumbnails`.
- `app/config.py` — environment-driven config (UPLOAD_DIR, TEMP_DIR, THUMBNAIL_DIR, MAIL, LDAP, DB URI). App resolves these to absolute paths at startup.
- `app/models.py` — domain model (Type, Category, User, Listing, ListingImage) and relationships. Note the unique constraint on Category `(name, type_id)`.
- `app/forms.py` — WTForms validations (title, description length, price decimal rules). Reuse or extend validators here.
- `app/routes/*.py` — primary logic: `auth.py`, `listings.py`, `admin.py`, `users.py`, `utils.py`.

Developer workflows (commands you can run inside the repo root):

- Local init (creates sqlite DB and folders):
  FLASK_APP=app flask init

- Run dev server (use virtualenv):
  FLASK_APP=app FLASK_ENV=development flask run --debug

- Generate thumbnails for legacy images:
  FLASK_APP=app flask backfill-thumbnails

- Production WSGI entrypoint: `wsgi.py` — run with Gunicorn from project root:
  gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

Conventions and gotchas to preserve

- File-system atomicity: never write uploaded images directly into `UPLOAD_DIR` before DB commit. Follow the temp->commit->move pattern. Breaking this will leave orphaned files or inconsistent DB state.
- Thumbnail filenames are stored on ListingImage.thumbnail_filename; thumbnails are generated as `.jpg` regardless of original extension.
- Do not assume MAIL is configured; the app falls back to flashing reset links when MAIL_SERVER is not set. When adding email-related behavior, check for `current_app.config.get('MAIL_SERVER')`.
- Admin safety: admin removal/deletion checks prevent removing the last admin (see `admin.edit_user` and `admin.delete_user`). Keep those guards when modifying user admin flows.

Examples to copy/paste when creating similar features

- Create a blueprint and register it in `create_app()`:
  from flask import Blueprint
  bp = Blueprint("feature", __name__)
  # implement routes
  app.register_blueprint(bp, url_prefix="/feature")

- Use the temp file pattern (simplified):
  1) save uploaded files to `current_app.config['TEMP_DIR']`
  2) create thumbnails in temp
  3) db.session.add(...) and db.session.commit()
  4) if commit succeeds, move files from TEMP_DIR to UPLOAD_DIR and THUMBNAIL_DIR
  5) on DB error, delete temp files and rollback

Where to look for tests / how to run them

- There are no automated test suites included. For quick validation, run the Flask dev server, exercise forms (create/edit listings), and use `flask backfill-thumbnails` to test image processing.

If you change database models

- Update `migrations/` via Alembic locally (project uses Flask-Migrate). There is an initial migrations directory but no automated script in this repo — prefer running `flask db migrate`/`flask db upgrade` if you add real migration steps.

Final notes

- Keep changes small and prefer code examples present in `app/routes/*` as a pattern source.
- If unsure about file paths, reference `app/__init__.py` where UPLOAD_DIR/TEMP_DIR/THUMBNAIL_DIR are resolved to absolute paths at runtime.


## Quick additions for safe edits

Below are focused items every automated editor should follow before committing changes.

### 1) Naming symbols

Avoid using single-character names for variables, functions, classes, or other symbols. Descriptive names (e.g. user_email, listing_price, create_thumbnail) make the code easier to read and maintain—this is especially helpful because most of the project will be edited by Copilot and reviewed by a non-expert.

Allowed exceptions:
- Very-localized scopes such as simple loop indices (i, j, k) or short comprehensions where the intent is obvious.
- Trivial throwaway variables (e.g., `_` for unused values).

Preferred style:
- Use clear, concise names that describe purpose.
- Use snake_case for variables/functions and PascalCase for classes.

Rationale: placed here so the rule is visible during quick edits and before the quality/QA checklist, increasing the chance auto-edits follow it.

### 2) Quality gates / quick checks
- Run a syntax/import smoke test to catch immediate errors:

```bash
python -m pyflakes . || true   # optional lint, may not be installed
python -c "import importlib; importlib.import_module('app')"  # ensure app imports
```

- If `flake8` is available, run it; otherwise ensure no new syntax errors are introduced.

### 3) Required / optional env vars (reference)
- REQUIRED for reasonable local work: `SECRET_KEY` (dev ok), `DEV_DATABASE_URL` or `DATABASE_URL` (sqlite fallback used), `FLASK_ENV` (development/testing/production).
- OPTIONAL: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` (password reset emails), `LDAP_SERVER`, `LDAP_DOMAIN` (LDAP login).
- Example minimal `.env` snippet:

```env
SECRET_KEY=dev-secret-key
DEV_DATABASE_URL=sqlite:///classifieds.db
MAIL_SERVER=
LDAP_SERVER=
LDAP_DOMAIN=
```

### 4) Code-edit safety checklist (filesystem & DB edits)
- Contract for listing/image flows:
  - Inputs: uploaded files saved to `current_app.config['TEMP_DIR']` and DB records referencing final filenames.
  - Success: DB commit + files moved from TEMP_DIR -> UPLOAD_DIR and THUMBNAIL_DIR; ListingImage.filename and .thumbnail_filename set.
  - Failure: DB rollback and temp files removed or restored to original location.
- Edge cases to validate locally after edits:
  - `TEMP_DIR` missing -> code should fail gracefully (flash + no crash).
  - Thumbnail creation failure -> abort upload and clean temp files.
  - Deleting images/listings: if original file missing, handler should skip and not crash.

### 5) Migrations & model changes
- Project contains Alembic under `migrations/` and uses Flask-Migrate. If you change `models.py`:
  - Run locally: `flask db migrate -m "msg"` then `flask db upgrade` to generate/apply migration.
  - If you can't run migrations in CI, update `migrations/` and document changes in PR.
- For quick local work the `flask init` helper calls `db.create_all()` — rely on it only for dev/testing, not production.

### 6) Manual QA checklist (no automated tests present)
- Create a new listing with 1+ images and confirm thumbnails are generated in `static/uploads/thumbnails`.
- Edit a listing and delete an image; ensure file is removed and DB updated.
- Admin: delete a listing with images; files should be moved to temp then removed on commit.
- Auth: test local registration/login and LDAP login (if LDAP vars set).

### 7) More copy-paste examples
- Temp->commit->move (pattern):

```py
# 1) save uploads to TEMP_DIR
# 2) create thumbnail in TEMP_DIR
# 3) db.session.add(listing); db.session.commit()
# 4) if commit OK: move files from TEMP_DIR -> UPLOAD_DIR/THUMBNAIL_DIR
# 5) if commit fails: remove temp files and db.session.rollback()
```

- Register blueprint (exact lines to copy):

```py
from .routes.myfeature import my_bp
app.register_blueprint(my_bp, url_prefix='/myfeature')
```

### 8) "Do not" rules & risky places
- DO NOT write uploaded files directly to `UPLOAD_DIR` before DB commit.
- DO NOT remove or demote the last admin (see `admin.edit_user` / `admin.delete_user`).
- DO NOT assume `MAIL_SERVER` is configured — use the flash fallback in `auth.forgot_password`.
- Be cautious when changing `ListingImage.thumbnail_filename` behavior — thumbnails are always `.jpg`.

### 9) PR / commit guidance for automated editors
- Use focused commits with a one-line summary and a short description of why the change was made.
- If changing `models.py`, include migration files or a note explaining why migrations are deferred.
- When touching uploads/thumbnails logic, include a short QA checklist in the PR description referencing the manual QA steps above.
