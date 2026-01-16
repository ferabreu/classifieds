---
description: 'Flask and SQLAlchemy 2.0 patterns, code standards, and helper functions'
applyTo: '**/*.py'
---

# Python Flask Development Standards

## Code Style & Formatting

- **Formatter**: Black (line length 88, single quotes preferred)
- **Import sorter**: isort (profile="black")
- **Linter**: Ruff
- **Indentation**: 4 spaces (per PEP 8)
- **Line length**: 88 characters (Black default)
- **Type hints**: Add for public functions where helpful

### Naming Conventions
- **Functions/variables**: `snake_case` (descriptive names)
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- ❌ **NEVER use single-character names** except loop indices (i, j, k) or throwaway variables (`_`)

### Import Organization (use isort)
```python
# 1. Standard library
import os
from typing import Optional

# 2. Third-party packages
from flask import Flask
from sqlalchemy import select

# 3. Local application imports
from app.models import User
```

---

## Documentation Standards

### Docstrings (PEP 257)
Write clear docstrings for all public functions and classes:

```python
def create_thumbnail(source_path: str, dest_path: str, size: tuple = (224, 224)) -> None:
    """
    Generate a JPEG thumbnail with white background from an image file.
    
    Args:
        source_path: Path to the source image file
        dest_path: Path where thumbnail will be saved
        size: Thumbnail dimensions as (width, height). Defaults to (224, 224)
    
    Raises:
        IOError: If source file cannot be read or destination cannot be written
    """
    # Implementation
```

### Type Hints
Use the `typing` module for complex types:

```python
from typing import Optional, List, Dict

def get_user_listings(user_id: int, active_only: bool = True) -> List[Listing]:
    """Retrieve listings for a specific user."""
    # Implementation

def build_category_tree() -> Dict[str, List[Dict]]:
    """Build nested category structure for navigation."""
    # Implementation
```

### Comments
- Write comments for **why**, not **what** - code should be self-explanatory
- Document complex algorithms or business logic
- Explain non-obvious design decisions
- Document external dependencies and their purpose

```python
# ✅ GOOD - Explains why
# Use LDAP first, then fall back to local auth for offline scenarios
if ldap_server:
    user = authenticate_ldap(email, password)

# ❌ BAD - Explains what (code already shows this)
# Check if ldap_server exists
if ldap_server:
```

---

## Code Quality Principles

### Readability & Maintainability
- **Prioritize clarity over cleverness** - code is read more than written
- **Break down complex functions** - extract to smaller, focused helpers
- **Use descriptive names** - `calculate_total_price()` not `calc()`
- **Limit function length** - if it doesn't fit on one screen, consider splitting

### Exception Handling
Write clear exception handling with specific error types:

```python
# ✅ GOOD - Specific exceptions, clear handling
try:
    listing = db.get_or_404(Listing, listing_id)
    process_images(listing)
except IOError as e:
    flash(f"Image processing failed: {e}", "danger")
    db.session.rollback()
except Exception as e:
    current_app.logger.error(f"Unexpected error: {e}")
    flash("An unexpected error occurred", "danger")
    db.session.rollback()

# ❌ BAD - Bare except, no context
try:
    # operations
except:
    pass
```

### Edge Case Handling
Account for common edge cases:

```python
def delete_listing_images(listing: Listing) -> None:
    """Delete all images associated with a listing."""
    if not listing.images:
        return  # No images to delete
    
    for image in listing.images:
        # Handle case where file might already be deleted
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        else:
            current_app.logger.warning(f"File not found: {image.file_path}")
        
        # Handle thumbnail
        if image.thumbnail_path and os.path.exists(image.thumbnail_path):
            os.remove(image.thumbnail_path)
```

---

## Flask Blueprints

- Group routes by feature under `app/routes/`
- Register in `create_app()` in `app/__init__.py`

```python
from flask import Blueprint

my_bp = Blueprint('myfeature', __name__)

@my_bp.route('/endpoint')
def my_view():
    pass
```

---

## SQLAlchemy 2.0 Query Patterns (CRITICAL)

**Always use `select()` API - NEVER use deprecated `.query` attribute:**

```python
# ✅ CORRECT - SQLAlchemy 2.0 style
from sqlalchemy import select

user = db.session.execute(
    select(User).where(User.email == email)
).scalar_one_or_none()

users = db.session.execute(
    select(User).order_by(User.name)
).scalars().all()

# ❌ WRONG - Deprecated pattern
user = User.query.filter_by(email=email).first()  # DO NOT USE
```

### Flask-SQLAlchemy 3.1+ Convenience Methods
```python
# Simple primary key lookup
user = db.get_or_404(User, user_id)

# Query expecting exactly one result
user = db.one_or_404(select(User).where(User.email == email))

# Query expecting first result
user = db.first_or_404(select(User).where(User.active == True))
```

### Database Transaction Pattern
**Always wrap commits in try/except with rollback:**

```python
try:
    db.session.add(new_object)
    db.session.commit()
    # Success: proceed with file operations
except Exception as e:
    db.session.rollback()
    # Handle error, cleanup temp files
    flash(f"Database error: {e}", "danger")
    return redirect(...)
```

---

## Helper Functions & Utilities

### Reuse These Instead of Reinventing
- `app/routes/utils.create_thumbnail(src, dst)` - Thumbnail generation (224x224 JPEG, white background)
- `app/models.generate_url_name(name)` - Convert name to URL-safe slug
- `app/ldap_auth.authenticate_with_ldap(email, password)` - LDAP authentication (if configured)

### When to Create New Helpers
- Logic used by 2+ functions → extract to helper
- Complex operation that obscures main flow → extract
- Place in `app/routes/utils.py` or create new utility module

---

## Configuration Access

- **NEVER** hardcode paths - use `current_app.config['DIR_NAME']`
- Check configuration before using optional services:
  ```python
  if current_app.config.get('MAIL_SERVER'):
      # Send email
  else:
      # Fallback behavior (e.g., flash message)
  ```

---

## Key Reference Files

### Always Check These When Editing
- `app/__init__.py` - App factory, CLI commands, configuration resolution
- `app/config.py` - Environment config (UPLOAD_DIR, TEMP_DIR, etc.)
- `app/models.py` - Domain models and relationships
- `app/forms.py` - WTForms validators and form definitions
- `app/routes/*.py` - Route blueprints and business logic

### Useful Patterns Source
- `listings.py` - File upload/delete patterns
- `admin.py` - Admin safety checks
- `auth.py` - Authentication flows
- `users.py` - Complex queries with subqueries and joins

---

## Quality Checks

```bash
# Syntax & Import Check
python -m pyflakes app migrations scripts wsgi.py
python -c "import importlib; importlib.import_module('app')"

# Formatter & Linter
uv run black app/
uv run isort app/
uv run ruff check app/
```
