<!-- Copilot instructions for the `classifieds` Flask app -->
# Quick orientation for automated coding assistants

## About the developer

- The developer has a good grasp of the "logic" that good software requires. However, he is not an experienced developer.
- The developer relies on AI assistance for most code writing and refactoring, and will review and test all changes.
- Do not assume the developer asks rhetorical questions or understands advanced concepts without explanation. Assume the developer's questions are sincere. When answering, explain concepts clearly.
- Always consider established best practices, code readability, and maintainability when suggesting changes.
- When in doubt, ask the developer for further clarification.

## Code style & standards

Follow these conventions on every edit to keep the codebase consistent and reviewable.
For the canonical, detailed style guide, see also `docs/CODE_STYLE.md`.

### 1) Global standards
- Use UTF-8 encoding.
- Use Unix-style LF line endings.
- Keep lines <= 88 characters where possible.
- When applicable, write clear, concise commit messages with a one-line summary and optional description.
  
- Imports & modules
  - Avoid "reinventing the wheel" — prefer established libraries and patterns.
  - Imports should be placed at the top of the file, unless there is a specific reason to delay (e.g., avoid circular imports).
  - Avoid wildcard imports. Use explicit imports.
  - Order imports according to best practices for the language.
  - Add new helper functions in existing utilities modules (e.g., app/routes/utils.py) when they logically belong there.

- Naming symbols
  - Avoid using single-character names for variables, functions, classes, or other symbols.
  - Descriptive names (e.g. user_email, listing_price, create_thumbnail) make the code easier to read and maintain — this is especially helpful because most of the project will be edited by Copilot and reviewed by a non-expert.

  - Allowed exceptions:
    - Very-localized scopes such as simple loop indices (i, j, k) or short comprehensions where the intent is obvious.
    - Trivial throwaway variables (e.g., `_` for unused values).

  - Preferred style:
    - Use clear, concise names that describe purpose.
    - Follow usual practices regarding letter case for each language.

### 2) Python formatting and tooling
- Imports ordering: stdlib, third-party, local (use isort).
- Follow PEP 8. Use 4 spaces for indentation.
- Prefer Black for automatic formatting (line length 88) and isort for import ordering.
- Use descriptive names (snake_case for functions/variables, PascalCase for classes). Avoid single-letter names except for short loops.
- Prefer single quotes for Python strings where not conflicting with content; let Black / team tooling normalize quotes automatically.
- Add type hints for public functions where helpful.

### 3) Flask & SQLAlchemy patterns
- Follow existing blueprint patterns (bp = Blueprint(...)) and register in create_app().
- DB & fileflow: always follow the temp -> commit -> move pattern for uploaded files:
  1. Save uploads to current_app.config['TEMP_DIR']
  2. Create thumbnails in TEMP_DIR
  3. db.session.add(...); db.session.commit()
  4. If commit OK: move files to UPLOAD_DIR/THUMBNAIL_DIR
  5. On DB error: delete temp files and rollback
- Use current_app.config to read dirs and options. Do not hardcode paths.
- Wrap DB commits in try/except and ensure rollback on errors.

### 4) Jinja templates
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

### 5) JavaScript / CSS
- Place scripts in `{% block scripts %}`. Do not use inline scripts.
- Use modern JS (let/const) and avoid global variables.
- Avoid jQuery.
- Avoid "reinventing the wheel"; prefer established libraries for common tasks.
- Load external libraries via the project's pattern (CDN or local) consistent with existing templates.
- Keep CSS in `static/css/`; follow existing naming and structuring conventions.

## Quality assurance & testing
- There are no automated tests in-repo; run the dev server and exercise critical flows:
  - Create/edit listings (images + thumbnails)
  - Delete listings/images and confirm file cleanup
  - Admin actions (do not remove last admin)
- Include a short manual QA checklist in PRs when touching uploads or DB changes.

- Misc
  - When changing models, provide migration steps (flask db migrate/upgrade) or document why migrations are deferred.
  - Keep commits focused and include a brief rationale.
  - If unsure, keep changes small and ask for a quick review.

## Project-specific patterns and commands when making changes

- Project type: Flask (Python 3.10+), single WSGI app in `wsgi.py`. App factory: `app.create_app()` in `app/__init__.py`.
- DB: SQLAlchemy (Flask-SQLAlchemy) with **SQLite3 as the production database**. Migrations present (Alembic) under `migrations/` but app uses `db.create_all()` in the CLI `flask init` helper for quick local setup.
- **IMPORTANT: SQLite is used in production**, not just development. When writing migrations:
  - SQLite does NOT support `ALTER COLUMN` operations (changing nullable, type, etc.)
  - Use `server_default` when adding NOT NULL columns, then backfill data
  - Avoid `op.alter_column()` - it will fail on SQLite
  - For complex schema changes, use the "recreate table" pattern (create new, copy data, drop old, rename)
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
- `app/routes/*.py` — primary logic: `admin.py`, `auth.py`, `caregories.py`, `listings.py`, `users.py`, `utils.py`.

Conventions and gotchas to preserve:

- File-system atomicity: never write uploaded images directly into `UPLOAD_DIR` before DB commit. Follow the temp->commit->move pattern. Breaking this will leave orphaned files or inconsistent DB state.
- Thumbnail filenames are stored on ListingImage.thumbnail_filename; thumbnails are generated as `.jpg` regardless of original extension.
- Do not assume MAIL is configured; the app falls back to flashing reset links when MAIL_SERVER is not set. When adding email-related behavior, check for `current_app.config.get('MAIL_SERVER')`.
- Admin safety: admin removal/deletion checks prevent removing the last admin (see `admin.edit_user` and `admin.delete_user`). Keep those guards when modifying user admin flows.

Final notes

- Keep changes small and prefer code examples present in `app/routes/*` as a pattern source.
- If unsure about file paths, reference `app/__init__.py` where UPLOAD_DIR/TEMP_DIR/THUMBNAIL_DIR are resolved to absolute paths at runtime.

## Quick additions for safe edits

Below are focused items every automated editor should follow before committing changes.

### 1) Quality gates / quick checks
- Run a syntax/import smoke test to catch immediate errors after edits (scope to app code so venv/vendor files are ignored):

```bash
source venv/bin/activate
python -m pyflakes app migrations scripts wsgi.py || true  # optional lint scoped to project code
python -c "import importlib; importlib.import_module('app')"  # ensure app imports
```

- If `flake8` is available, run it; otherwise ensure no new syntax errors are introduced.

### 2) Required / optional env vars (reference)
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

### 3) Code-edit safety checklist (filesystem & DB edits)
- Contract for listing/image flows:
  - Inputs: uploaded files saved to `current_app.config['TEMP_DIR']` and DB records referencing final filenames.
  - Success: DB commit + files moved from TEMP_DIR -> UPLOAD_DIR and THUMBNAIL_DIR; ListingImage.filename and .thumbnail_filename set.
  - Failure: DB rollback and temp files removed or restored to original location.
- Edge cases to validate locally after edits:
  - `TEMP_DIR` missing -> code should fail gracefully (flash + no crash).
  - Thumbnail creation failure -> abort upload and clean temp files.
  - Deleting images/listings: if original file missing, handler should skip and not crash.

### 4) Migrations & model changes
- Project contains Alembic under `migrations/` and uses Flask-Migrate. If you change `models.py`, and the database schema requires alterations, create a new migration file.
  - Pay attention to Alembic's versioning.

- **SQLite limitations and migration patterns:**
  - SQLite does NOT support `ALTER COLUMN` to change nullable, type, default, etc.
  - **Use Alembic batch mode for all constraint/schema operations on SQLite:**
    ```python
    with op.batch_alter_table('table_name', schema=None) as batch_op:
        batch_op.add_column(sa.Column('new_col', sa.String(128), nullable=False, server_default='temp'))
        batch_op.create_unique_constraint('constraint_name', ['col1', 'col2'])
    ```
  - When adding NOT NULL columns: use `server_default='temp'`, backfill data in SQL, constraint operations inside batch mode
  - Never use `op.alter_column()` with `nullable=`, `type_=`, or other modifications outside batch mode - it will fail
  - For complex changes: batch mode handles the "recreate table" strategy automatically (create temp table, copy data, drop old, rename)

### 4b) SQLite Batch Mode Examples (copy-paste patterns)

**Example 1: Adding a NOT NULL column with unique constraint**
```python
def upgrade():
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('url_name', sa.String(128), nullable=False, server_default='temp', index=True)
        )
        batch_op.create_unique_constraint(
            'uk_category_url_name_parent',
            ['url_name', 'parent_id']
        )
    
    # After batch operations, backfill data
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE category 
        SET url_name = LOWER(REPLACE(REPLACE(TRIM(name), ' ', '_'), '-', '_'))
        WHERE url_name = 'temp'
    """))
    conn.commit()

def downgrade():
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_constraint('uk_category_url_name_parent', type_='unique')
        batch_op.drop_column('url_name')
```

**Example 2: Modifying column constraints (add NOT NULL)**
```python
def upgrade():
    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False, server_default='active')
    
    # Update existing NULLs
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE listing SET status = 'active' WHERE status IS NULL"))
    conn.commit()

def downgrade():
    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=True, server_default=None)
```

**Example 3: Adding multiple constraints in one migration**
```python
def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verified_email', sa.Boolean(), nullable=False, server_default=False))
        batch_op.create_index('ix_user_email_verified', ['email', 'verified_email'])
        batch_op.create_check_constraint('ck_user_email_notnull', 'email IS NOT NULL')
    conn = op.get_bind()
    conn.commit()

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('ck_user_email_notnull', type_='check')
        batch_op.drop_index('ix_user_email_verified')
        batch_op.drop_column('verified_email')
```

**Key rules:**
- ALL schema modifications (add column, drop column, add/drop constraints, alter_column) MUST go inside `with op.batch_alter_table():`
- `server_default` is required for NOT NULL columns being added; backfill the data AFTER batch operations
- Downgrade must also use batch mode for consistency
- For simple type-safe operations (e.g., adding nullable column), batch mode still works fine

### 4c) SQLite Migration Anti-Patterns (what NOT to do)

❌ **NEVER:** Use `op.alter_column()` outside of batch mode:
```python
# WRONG - This will fail on SQLite!
op.alter_column('user', 'email', nullable=False)
```
✅ **INSTEAD:** Use batch mode:
```python
# CORRECT
with op.batch_alter_table('user', schema=None) as batch_op:
    batch_op.alter_column('email', nullable=False, server_default='unknown')
```

❌ **NEVER:** Add a NOT NULL constraint without `server_default`:
```python
# WRONG - Alembic will fail when backfilling
batch_op.add_column(sa.Column('status', sa.String(50), nullable=False))
```
✅ **INSTEAD:** Include `server_default`, then backfill data:
```python
# CORRECT
batch_op.add_column(sa.Column('status', sa.String(50), nullable=False, server_default='active'))
# Then after batch context, update existing rows
conn = op.get_bind()
conn.execute(sa.text("UPDATE user SET status = 'active' WHERE status = 'active'"))
```

❌ **NEVER:** Use direct `op.drop_constraint()` or `op.create_constraint()` outside batch mode:
```python
# WRONG - Will fail on SQLite
op.drop_constraint('fk_listing_user_id', type_='foreignkey')
```
✅ **INSTEAD:** Use batch mode for constraint operations:
```python
# CORRECT
with op.batch_alter_table('listing', schema=None) as batch_op:
    batch_op.drop_constraint('fk_listing_user_id', type_='foreignkey')
```

❌ **NEVER:** Assume you can avoid batch mode for "simple" changes:
```python
# WRONG - Even adding an index might need batch mode for consistency
op.create_index('ix_new_index', 'table_name', ['column'])
```
✅ **CORRECT:** Use batch mode when adding columns or modifying existing constraints:
```python
# If adding a column or modifying schema, use batch mode consistently
with op.batch_alter_table('table_name', schema=None) as batch_op:
    batch_op.add_column(...)
    batch_op.create_index('ix_new_index', ['column'])
```

**Summary:** On SQLite, when in doubt, use `op.batch_alter_table()`. It's the safe default for all schema changes.

### 5) Manual QA checklist (no automated tests present)
- Create a new listing with 1+ images and confirm thumbnails are generated in `static/uploads/thumbnails`.
- Edit a listing and delete an image; ensure file is removed and DB updated.
- Admin: delete a listing with images; files should be moved to temp then removed on commit.
- Auth: test local registration/login and LDAP login (if LDAP vars set).

### 6) More copy-paste examples
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

### 7) "Do not" rules & risky places
- DO NOT write uploaded files directly to `UPLOAD_DIR` before DB commit.
- DO NOT remove or demote the last admin (see `admin.edit_user` / `admin.delete_user`).
- DO NOT assume `MAIL_SERVER` is configured — use the flash fallback in `auth.forgot_password`.
- Be cautious when changing `ListingImage.thumbnail_filename` behavior — thumbnails are always `.jpg`.

### 8) PR / commit guidance for automated editors
- Use focused commits with a one-line summary and a short description of why the change was made.
- If changing `models.py`, include migration files or a note explaining why migrations are deferred.
- When touching uploads/thumbnails logic, include a short QA checklist in the PR description referencing the manual QA steps above.
