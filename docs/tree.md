```
app/
├── main/            # --- Logic for global pages (home, about, errors) ---
│   ├── __init__.py  # Initializes 'main' blueprint
│   └── routes.py    # Routes for global pages
├── templates/       # --- Shared template store ---
│   ├── admin/
│   │   └── dashboard.html  # Shared admin dashboard
│   ├── base.html           # Shared by ALL entities
│   ├── error.html          # Shared error page
│   ├── index.html          # The landing page
│   └── macros.html         # Shared UI components
├── auth/                    # --- Dedicated Auth Entity ---
│   ├── __init__.py          # Factory for the 'auth' blueprint
│   ├── forms.py             # Forms for authentication (WTForms)
│   ├── models.py            # Track external connections, permissions, sessions
│   ├── routes/
│   │   ├── local.py         # Standard username/password
│   │   ├── oauth.py         # Google, GitHub, etc. (callback logic)
│   │   └── active_dir.py    # LDAP/Active Directory logic
│   ├── services/
│   │   ├── oauth_client.py  # Wrapper for [Authlib](https://docs.authlib.org)
│   │   └── ad_validator.py  # Wrapper for [ldap3](https://ldap3.readthedocs.io)
│   └── templates/           # Auth-specific templates
│       └── auth/
│           ├── login.html
│           ├── register.html
│           ├── password_recover.html
│           └── password_reset.html
├── categories/          # --- Categories Entity ---
│   ├── __init__.py      # Initializes 'categories' blueprint
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
│           ├── admin.html
│           └── form.html
├── listings/            # --- Listings Entity ---
│   ├── __init__.py      # Initializes 'listings' blueprint
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
│           ├── admin.html
│           ├── detail.html
│           └── form.html
├── users/               # --- Users Entity ---
│   ├── __init__.py      # Initializes 'users' blueprint
│   ├── forms.py         # Forms for user operations
│   ├── models.py        # Data models for users
│   ├── services.py      # Business logic for users
│   ├── routes/
│   │   ├── __init__.py  # Initializes routes for users
│   │   ├── admin.py     # Admin operations for users
│   │   ├── helpers.py   # Utility functions for users
│   │   └── public.py    # Public-facing routes for users
│   └── templates/       # User-specific templates
│       └── users/
│           ├── admin.html
│           ├── detail.html
│           └── form.html
├── __init__.py  # Application Factory (registers blueprints)
├── config.py    # Configuration settings
└── extensions.py # Initialize Flask extensions (DB, Migrate, LoginManager, etc.)
```