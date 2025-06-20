# Classifieds App

A modern, production-quality Flask web application for posting and managing classified ads (goods & services) with admin tools, user authentication (local/LDAP), password reset, and a sidebar for navigation by type and category.

---

## Purpose

This application allows users to post, browse, and manage classified ads for goods and services. Key features include:

- User registration & authentication (local and optional LDAP)
- Posting, editing, and deleting ads (items)
- Browsing by type (Good or Service) and by category
- Admin dashboard for managing users, types, categories, and items
- Password reset via email link (for non-LDAP users)
- Clean, responsive UI with sidebar navigation

---

## Features Overview

- **Users:** Register, login, edit profile, reset password
- **Items:** Create, edit, delete, view details
- **Types & Categories:** Admin-defined; organize items for easy browsing
- **Admin:** Full CRUD for users, types, categories, and items
- **LDAP Authentication:** Optional, fallback to local, creates users on first LDAP login
- **Password Reset:** Secure, token-based, for local accounts
- **Sidebar Navigation:** Types and categories always visible for quick filtering

---

## Project Structure

```
classifieds/
├── app.py
├── config.py
├── forms.py
├── ldap_auth.py
├── models.py
├── requirements.txt
├── wsgi.py
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── README.md
├── static/
│   └── styles.css
├── instance/
│   └── classifieds.db         # Created after first run
├── routes/
│   ├── __init__.py
│   ├── admin.py
│   ├── auth.py
│   ├── items.py
│   └── users.py
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── forgot_password.html
    ├── reset_password.html
    ├── item_detail.html
    ├── item_form.html
    ├── admin_dashboard.html
    ├── admin_users.html
    ├── admin_types.html
    ├── admin_type_form.html
    ├── admin_categories.html
    ├── admin_category_form.html
    ├── admin_items.html
    ├── user_profile.html
    └── user_edit.html
```

---

## How It Works

### Authentication

- Local users: register, login, password stored securely (hashed)
- LDAP users: login via LDAP if enabled; first login creates user entry
- Password reset: local users can request a reset link (sent by email if mail is configured, otherwise shown in flash for demo)

### Admin

- Visit `/admin/dashboard` as an admin user
- Manage users (edit, promote/demote admin, delete, except must always have at least one admin)
- Manage types and categories (CRUD)
- Manage all items (delete any item)

### Classifieds

- Any user can create, edit, or delete their own items
- Admins can edit/delete any item
- Browse by type/category via sidebar

---

## Initial Setup

### Requirements

- Python 3.10+
- pip (Python package manager)

### 1. Clone and set up venv

```bash
git clone <your-repo-url> classifieds
cd classifieds
python -m venv venv

# IMPORTANT: Activate the venv BEFORE installing requirements!
source venv/bin/activate

pip install -r requirements.txt

# RECOMMENDED: Reactivate the venv after installing dependencies
# (This ensures the correct 'flask' command is used and $PATH is updated.)
deactivate
source venv/bin/activate

# (Optional, but recommended) Check that you're using the venv's Python and Flask:
which python
which flask
# Both should point to the venv's bin directory (e.g., .../classifieds/venv/bin/python)
```

---

### 2. Configure Environment

Copy `.env.example` to `.env` and edit as needed:

```bash
cp .env.example .env
```

By default, Flask will auto-load `.env` for `flask run` or for `flask` commands.  
For Gunicorn (production), you must export these variables in your shell, use a process manager (e.g., systemd), or pass them with Docker (see below).

---

### 3. Initialize the database

```bash
flask --app app.py init-db
```

This creates:
- `instance/classifieds.db` (SQLite)
- Default admin: `admin@classifieds.io` / password: `admin`
- Types: Good, Service. Each gets a "General" category.

---

### 4. Run the app

#### Development

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```
Visit [http://localhost:5000](http://localhost:5000)

#### Production (Gunicorn)

From the **project root**:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```
(Adjust workers/port as needed.)

---

## LDAP Authentication (Optional)

Set environment variables for LDAP:

```bash
export LDAP_SERVER="ldap://<your-ldap-server>"
export LDAP_DOMAIN="YOURDOMAIN"
```

- If set, users can login with their LDAP credentials.
- On first LDAP login, a user record is created.

---

## Password Reset

- For demo, password reset link is flashed (not emailed).
- For production, with email configured (see below), users will receive a reset link by email.

---

## Email Configuration for Password Reset

To enable password reset emails, you must configure Flask-Mail via environment variables or your `.env` file:

```
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your_smtp_username
MAIL_PASSWORD=your_smtp_password
MAIL_DEFAULT_SENDER=no-reply@classifieds.io
```

For local testing, you can use a tool like [MailHog](https://github.com/mailhog/MailHog) or [smtp4dev](https://github.com/rnwood/smtp4dev), setting `MAIL_SERVER=localhost` and `MAIL_PORT=1025`.

---

## Docker Deployment

### Build the image

```bash
docker build -t classifieds-app .
```

### Run the container

```bash
docker run -d \
  -e SECRET_KEY=your-secret-key \
  -e MAIL_SERVER=smtp.example.com \
  -e MAIL_PORT=587 \
  -e MAIL_USE_TLS=true \
  -e MAIL_USERNAME=youruser \
  -e MAIL_PASSWORD=yourpass \
  -e MAIL_DEFAULT_SENDER=no-reply@classifieds.io \
  -p 8000:8000 \
  -v classifieds_instance:/app/instance \
  classifieds-app
```

### Or use docker-compose

```bash
docker-compose up --build
```

### Initialize the DB in Docker

```bash
docker exec -it <container_id_or_name> flask --app app.py init-db
```

- The `instance/` directory is persisted as a named Docker volume for your database.
- All environment variables can be set via `docker run -e ...` or in `docker-compose.yml`.

---

## .env and .env.example

### Usage

- The `.env` file holds environment variables for local development.
- Flask will automatically read `.env` when using `flask run` or `flask` commands.
- When using Gunicorn, Docker, or systemd for production, ensure these variables are exported in your environment, passed via a process manager, or via Docker Compose.

#### Sample `.env.example` file:

```env name=.env.example
SECRET_KEY=dev-secret-key

MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_USE_SSL=false
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=no-reply@classifieds.io

LDAP_SERVER=
LDAP_DOMAIN=
```

---

## Troubleshooting

- **ModuleNotFoundError**: Ensure you activate your venv: `source venv/bin/activate`
- **Database not found**: Run `flask --app app.py init-db`
- **Gunicorn import errors**: Always run from the project root (where `wsgi.py` is) and use `gunicorn wsgi:app`
- **Environment variables not loaded:** For Gunicorn or Docker, ensure you export variables or use a `.env` loader compatible with your process manager.
- **Using the wrong Flask/Python**: Run `which python` and `which flask` to confirm you're using the venv.
- **After installing requirements, reactivate your venv:** Sometimes after installing requirements, your shell may still use the global Flask. Run:
  ```bash
  deactivate
  source venv/bin/activate
  ```

---

## Security Notes

- Change the default admin password after first login!
- Use a strong `SECRET_KEY` in production (`export SECRET_KEY="your-secret-key"`).
- For production, use a real mail server for password reset.
- Use HTTPS and a proper WSGI server (like Gunicorn or uWSGI) with a reverse proxy.

---

## License

MIT or your choice.

---

## Author

Created by GitHub Copilot for Fernando Mees Abreu ([https://github.com/ferabreu](https://github.com/ferabreu))

---
