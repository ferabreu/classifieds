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

## TODO (Short-Term)

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
- [x] Add support for images or attachments in items.
- [ ] Add a "Select All" checkbox to:
  - [x] admin items
  - [ ] admin users?
  - [ ] admin other stuff?
- [ ] Add form validation for items:
  - [ ] Title: at least 1 word.
  - [ ] Description: at least one sentence.
- [ ] schedule a cron job or background task to periodically clean up orphaned files in TEMP_DIR (in case something ever goes wrong mid-operation).
- [ ] Add basic tests for models and routes.
- [ ] Add unit tests.
- [x] Ensure consistent HTML indentation (2 vs 4 spaces)
- [x] Rename "items" to "ads".
- [ ] Unify management of types and categories in the same screen.

## Open Questions / Next Steps

- [ ] What are the requirements for the user interface for searching and filtering classified ads?
- [ ] What should the user profile and dashboard pages include?
- [x] What are the admin-specific features needed (e.g. managing categories/types/users)?
- [ ] Which email features are essential (e.g., ad notifications, password reset)?
- [ ] What tests and deployment instructions are needed?
- [ ] How to make the error messages more user friendly?

## TODO Fun List :-)
- [x] Investigate backend and frontend mapping of first/last name columns
- [x] Understand why "Edit" is a link but "Delete" is a form button
- [x] Compare the best approach: vanilla JS vs jQuery for UI scripting
- [x] Implement "Select All" with jQuery in admin_items.html
- [x] Sync "Select All" checkbox state with row selections
- [x] Debug and fix checkbox syncing logic
- [x] Celebrate a perfect working solution! 🎉

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-Login](https://flask-login.readthedocs.io/en/latest/)
- [Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)