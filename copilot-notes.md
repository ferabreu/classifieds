# Copilot Project Notes

## Project Overview
This is a Flask-based classified ads application. The main goals are:
- User registration and authentication (with optional LDAP support)
- Posting, viewing, and managing classified ads (Goods and Services)
- Admin management for users, types, and categories
- Email notifications (Flask-Mail)
- Organized project structure with blueprints for routes

## Key Files and Structure
- `app.py`: Flask application factory. Handles app initialization, blueprint registration, CLI commands (including DB initialization), and sets up Flask-Login and Flask-Mail.
- `models.py`: SQLAlchemy models for `User`, `Type`, `Category`, and `Item`. Manages relationships and includes password hashing for users.
- `config.py`: Holds configuration (`Config` class) including database URI logic.
- `routes/`: Contains blueprints for authentication, items, users, and admin.
- `static/` and `templates/`: For static assets and HTML templates.

## What We’ve Done So Far
- [x] Defined all primary database models (`User`, `Type`, `Category`, `Item`) in `models.py` with proper relationships and constraints.
- [x] Set up `app.py` as the Flask application entry, using the application factory pattern and correct import order to avoid circular dependencies.
- [x] Registered blueprints for main routes under `routes/` (authentication, items, users, admin).
- [x] Integrated Flask-Login with a custom user loader and login view.
- [x] Added Flask-Mail setup for email notifications.
- [x] Implemented CLI command (`init-db`) for database initialization and creation of default admin/types/categories.
- [x] Used Flask's `before_request` to inject sidebar/type data into templates.
- [x] Implemented authentication and registration routes (login, logout, registration, forgot/reset password, LDAP support) in `routes/auth.py`.
- [x] Implemented item listing, creation, editing, and deletion in `routes/items.py`, with corresponding templates.
- [x] Implemented admin management views for users (list, edit, delete), types (full CRUD), and categories (full CRUD). Admins can also delete any item.
- [ ] Unit tests are not written.
- [x] Deployment scripts and instructions are complete. The repo includes a Dockerfile and docker-compose.yml for containerized deployment, with detailed usage instructions and environment variable documentation in the README. No systemd or NGINX configuration is provided at this stage, but can be added if needed later.

## Security Review Recommendations (2025-06-23)

### 1. CSRF Protection
- All forms should continue to inherit from `FlaskForm` to ensure CSRF protection.
- If adding custom POST endpoints or APIs that do not use `FlaskForm`, implement explicit CSRF protection (e.g., via Flask-WTF CSRF decorators).

### 2. Authentication and Authorization
- Ensure all routes that mutate user data use `@login_required`.
- Admin actions must always require both `@login_required` and the custom `@admin_required` decorator, which checks `current_user.is_admin`.
- For user self-edit routes, always confirm `current_user.id == user.id` or `current_user.is_admin` before allowing edits.

### 3. Session Security
- Never use the default `SECRET_KEY='dev'` in production. Always set a strong, unpredictable secret via environment/config.
- Always deploy with HTTPS in production to protect session cookies and CSRF tokens.

### 4. Password Handling
- Continue to use secure password hashing (`generate_password_hash` / `check_password_hash` from Werkzeug).
- Never store or log plaintext passwords.

### 5. Password Reset
- Ensure reset tokens are always generated and verified with `itsdangerous`, signed with `SECRET_KEY`, and expire after a reasonable time (currently 1 hour).
- Ensure password reset only works for local users, not LDAP users.
- In development, if reset links are flashed to the UI for testing, be cautious with screen sharing or demos to prevent account hijacking.

### 6. User/Item Ownership Checks
- Always check that users can only edit/delete their own resources, unless they are admin.
- Maintain the logic that prevents removing the last admin user from the system.

### 7. Miscellaneous
- Maintain unique constraint on the email field in the User model.
- Continue to check for existing emails at registration.
- Confirm that LDAP users cannot use password reset or local password authentication flows.
- Avoid trusting user-supplied IDs for sensitive actions—always verify permissions server-side.

### 8. Additional Recommendations
- Regularly audit for any new POST endpoints to ensure they are covered by authentication, authorization, and CSRF protection.
- Double-check error messages in registration and password reset flows to avoid leaking information about which accounts exist (to prevent user enumeration).
- Consider adding unit and integration tests for all authentication, authorization, and CSRF flows.
- Always use secure cookies and set proper cookie flags (`Secure`, `HttpOnly`, `SameSite`) in production.

---

For a deeper or more up-to-date review, search the full codebase for `csrf`, `user`, `session`, and `form`.  
See: https://github.com/ferabreu/classifieds/search?q=csrf+OR+user+OR+session+OR+form

## Open Questions / Next Steps
- What are the requirements for the user interface for searching and filtering classified ads?
- What should the user profile and dashboard pages include?
- What are the admin-specific features needed (e.g. managing categories/types/users)?
- Should ads support images or attachments?
- Which email features are essential (e.g., ad notifications, password reset)?
- What tests and deployment instructions are needed?

## Relevant Code Snippets

```python
# app.py: Import models at the top to avoid circular dependencies
from models import db, Type, User, Category
```

```python
# app.py: Flask application factory pattern
def create_app():
    app = Flask(...)
    ...
    db.init_app(app)
    login_manager.init_app(app)
    ...
    return app
```

```python
# models.py: User password hashing
class User(UserMixin, db.Model):
    ...
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

```python
# app.py: CLI command for initializing database with default admin, types, and categories
@app.cli.command("init-db")
def init_db():
    ...
```

```python
# routes/auth.py: Authentication and registration routes implemented
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    ...
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    ...
@auth_bp.route('/logout')
@login_required
def logout():
    ...
@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    ...
@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    ...
```

```python
# routes/items.py: Item creation, editing, and deletion routes implemented
@items_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_item():
    ...
@items_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    ...
@items_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    ...
```

## Last Copilot Chat Context
- Confirmed the proper way to import SQLAlchemy models to avoid circular imports.
- Provided and reviewed the full `app.py` and `models.py` files, ensuring best practices for app factory and blueprint organization.
- Discussed statelessness and session limitations in Copilot Chat.
- Shared strategies for maintaining project continuity over multi-day sessions.
- Reviewed `routes/auth.py` and confirmed authentication and registration routes are implemented.
- Reviewed `routes/items.py` and confirmed item creation, editing, and deletion routes are implemented.
- Updated project notes to accurately reflect completed features.

## TODO (Short-Term)
- Implement admin dashboard and management views.
- Add basic tests for models and routes.
- Write deployment scripts/instructions.

---
