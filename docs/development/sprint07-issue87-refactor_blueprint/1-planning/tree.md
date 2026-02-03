```
app/
├── __init__.py          # Application Factory (registers blueprints in critical order)
├── config.py            # Configuration settings for different environments
├── extensions.py        # Initialize Flask extensions
├── shared/              # --- Shared utilities across entities ---
│   ├── __init__.py
│   ├── decorators.py    # Route decorators
│   └── utils.py         # File operations (thumbnails, commits, rollbacks, cleanup)
├── main/                # --- Global pages (home, errors, admin dashboard) ---
│   ├── __init__.py      # Initializes 'main' blueprint
│   └── routes.py        # Index route (reuses listings' services), error handlers, admin dashboard
├── templates/           # --- Shared template store ---
│   ├── admin/
│   │   └── dashboard.html  # Shared admin dashboard
│   ├── macros/
│   │   └── *.html       # Reusable UI components (forms, pagination, etc.)
│   ├── base.html        # Base template for ALL pages
│   ├── error.html       # Generic error page
│   └── index.html       # Landing page (showcase)
├── auth/                # --- Authentication Entity ---
│   ├── __init__.py      # Factory for 'auth' blueprint
│   ├── forms.py         # Forms for login, registration, password recovery
│   ├── models.py        # Placeholder for future OAuth/session tracking models
│   ├── services.py      # send password reset email, fallback logic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ad_validator.py  # LDAP/Active Directory authentication (moved from ldap_auth.py)
│   │   └── oauth.py         # Placeholder for future callback logic (Google, GitHub, etc.)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── local.py     # Login, register, logout routes
│   │   └── password.py  # Forgot password, reset password routes
│   └── templates/
│       └── auth/
│           ├── login.html
│           ├── register.html
│           ├── password_recover.html (moved from forgot_password.html)
│           └── password_reset.html (moved from reset_password.html)
├── categories/          # --- Categories Entity ---
│   ├── __init__.py      # Factory for 'categories' blueprint
│   ├── forms.py         # Forms for category operations
│   ├── models.py        # Data models for categories
│   ├── services.py      # Business logic for categories
│   ├── routes/
│   │   ├── __init__.py  # Initializes routes for categories
│   │   ├── admin.py     # Admin operations for categories
│   │   ├── helpers.py   # Utility functions for categories
│   │   └── public.py    # Public-facing routes for categories
│   └── templates/       # Category-specific templates
│       └── categories/
│           ├── admin.html (moved from admin_categories.html)
│           └── form.html (moved from category_form.html)
├── listings/            # --- Listings Entity ---
│   ├── __init__.py      # Factory for  'listings' blueprint
│   ├── forms.py         # Forms for listing operations
│   ├── models.py        # Data models for listings
│   ├── services.py      # Business logic for listings
│   ├── routes/
│   │   ├── __init__.py  # Initializes routes for listings
│   │   ├── admin.py     # Admin operations for listings
│   │   ├── helpers.py   # Utility functions for listings
│   │   └── public.py    # Public-facing routes for listings
│   └── templates/       # Listing-specific templates
│       └── listings/
│           ├── admin.html (moved from admin_listings.html)
│           ├── listing.html (moved from listing_detail.html)
│           └── form.html (moved from listing_form.html)
└── users/               # --- Users Entity ---
    ├── __init__.py      # Factory for 'users' blueprint
    ├── forms.py         # Forms for user operations
    ├── models.py        # Data models for users
    ├── services.py      # Business logic for users
    ├── routes/
    │   ├── __init__.py  # Initializes routes for users
    │   ├── admin.py     # Admin operations for users
    │   ├── helpers.py   # Utility functions for users
    │   └── public.py    # Public-facing routes for users
    └── templates/       # User-specific templates
        └── users/
            ├── admin.html (moved from admin_users.html)
            ├── form.html (moved from user_form.html)
            └── profile.html (moved from user_profile.html)
```

## Key Architecture Notes

### Blueprint Registration Order (CRITICAL)
Blueprints MUST be registered in this order in `app/__init__.py`:
1. `main_bp` (handles index and errors)
2. `auth_bp`, `categories_bp`, `users_bp` (specific prefixes)
3. **`listings_bp` LAST** (catch-all `/<path:category_path>` would shadow other routes)

### Service Layer Pattern
- **Models** (`models.py`): Data definitions only (SQLAlchemy models with `Mapped[]` types)
- **Services** (`services.py`): Business logic, orchestration, returns dictionaries
- **Routes** (`routes/*.py`): Thin HTTP handlers calling services
- **Helpers** (`routes/helpers.py`): Technical utilities only (create only if needed)

### String References for Relationships
All cross-entity relationships use string references to prevent circular imports:
```python
# In Listing model
category: Mapped["Category"] = relationship("Category", back_populates="listings")
owner: Mapped["User"] = relationship("User", back_populates="listings")

# In Category model (reciprocal)
listings: Mapped[List["Listing"]] = relationship("Listing", back_populates="category")

# In User model (reciprocal)
listings: Mapped[List["Listing"]] = relationship("Listing", back_populates="owner")
```

### Template Organization
- **Shared templates**: Stay in `app/templates/` (base.html, error.html, index.html, macros/)
- **Entity templates**: Live in `app/entity/templates/entity/` (configured with `template_folder='templates'`)
- **Render calls**: Use prefixed paths like `"auth/login.html"`, `"listings/detail.html"`

### Service Reuse Pattern
Services can be imported and reused across entities:
```python
# In app/main/routes.py
from app.listings.services import get_showcase_data

@main_bp.route('/')
def index():
    data = get_showcase_data()
    return render_template('index.html', **data)
```