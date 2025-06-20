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
- [x] Defined all database models (`User`, `Type`, `Category`, `Item`) with proper relationships and constraints.
- [x] Set up `app.py` with correct model imports at the top, eliminating circular imports.
- [x] Implemented the application factory pattern (`create_app` function).
- [x] Registered blueprints for routes: `auth`, `items`, `users`, `admin`.
- [x] Set up Flask-Login with user loader and login view.
- [x] Set up Flask-Mail.
- [x] Added CLI command `init-db` to initialize the database and create default admin, types, and categories.
- [x] Ensured sidebar data (types) is injected via `before_request`.
- [x] Implemented authentication and registration routes (`routes/auth.py`), including login, logout, registration, forgot password, reset password, and LDAP support.
- [x] Implemented item creation, editing, and deletion routes (`routes/items.py`), including UI logic for creating new classified ads.
- [ ] Implemented admin management views.
- [ ] Wrote unit tests.
- [ ] Wrote deployment scripts/instructions.

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