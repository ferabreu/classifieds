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

## Completed Features

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
- [x] Deployment scripts and instructions are complete. The repo includes a Dockerfile and docker-compose.yml for containerized deployment, with detailed usage instructions and environment variable documentation in the README. No systemd or NGINX configuration is provided at this stage, but can be added if needed later.
- [x] Implement admin dashboard and management views.

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

For a deeper or more up-to-date review, search the full codebase for `csrf`, `user`, `session`, and `form`.  
See: https://github.com/ferabreu/classifieds/search?q=csrf+OR+user+OR+session+OR+form

## Open Questions / Next Steps

- What are the requirements for the user interface for searching and filtering classified ads?
- What should the user profile and dashboard pages include?
- What are the admin-specific features needed (e.g. managing categories/types/users)?
- Which email features are essential (e.g., ad notifications, password reset)?
- What tests and deployment instructions are needed?

## TODO (Short-Term)

- Add support for images or attachments in items.
- Add basic tests for models and routes.
- Add unit tests.

## Internationalization (i18n) Guidance

To prepare the application for multilingual support, consider the following steps:

### 1. Use Flask-Babel for i18n

- Install Flask-Babel:
  ```
  pip install Flask-Babel
  ```
- Initialize Babel in your application:
  ```python
  from flask_babel import Babel

  app = Flask(__name__)
  babel = Babel(app)
  app.config['BABEL_DEFAULT_LOCALE'] = 'en'
  app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
  ```

### 2. Mark Strings for Translation

- In Python:
  ```python
  from flask_babel import _
  flash(_("Your item has been created!"), "success")
  ```
- In templates:
  ```jinja
  {{ _("Welcome to Classifieds!") }}
  ```

### 3. Extract and Manage Translations

- Extract messages:
  ```
  pybabel extract -F babel.cfg -o messages.pot .
  ```
- Initialize a new language:
  ```
  pybabel init -i messages.pot -d translations -l pt_BR
  ```
- Update and compile translations:
  ```
  pybabel update -i messages.pot -d translations
  pybabel compile -d translations
  ```

### 4. Language Selection

- Babel can auto-detect user locale or you can offer a language switcher.
  ```python
  @babel.localeselector
  def get_locale():
      # Use user preference, browser, or default
      return request.accept_languages.best_match(['en', 'pt_BR'])
  ```

### 5. Dates, Times, and Numbers

- Use Babel’s formatting tools for locale-aware output:
  ```python
  from flask_babel import format_datetime
  format_datetime(datetime.utcnow())
  ```

### 6. UI and Content

- Wrap all user-facing strings in `_()` for translation.
- Translate static content (emails, error messages, etc.).
- Render form and validation messages via translation.

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-Babel Documentation](https://pythonhosted.org/Flask-Babel/)
- [Babel User Guide](https://babel.pocoo.org/en/latest/user/index.html)
- [Flask-Login](https://flask-login.readthedocs.io/en/latest/)
- [Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)