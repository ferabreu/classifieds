# Classifieds App

A modern, production-quality Flask web application for posting and managing classified ads (goods & services) with admin tools, user authentication (local/LDAP), password reset, and a sidebar for navigation by type and category.

---

## Purpose

This application allows users to post, browse, and manage classified ads for goods and services. Key features include:

- User registration & authentication (local and optional LDAP)
- Posting, editing, and deleting ads (listings)
- Browsing by type (Good or Service) and by category
- Admin dashboard for managing users, types, categories, and listings
- Password reset via email link (for non-LDAP users)
- Clean, responsive UI with sidebar navigation

---

## Features Overview

- **Users:** Register, login, edit profile, reset password
- **Listings:** Create, edit, delete, view details with image thumbnails
- **Image Thumbnails:** Automatic 224x224 thumbnail generation for fast loading
- **Types & Categories:** Admin-defined; organize listings for easy browsing
- **Admin:** Full CRUD for users, types, categories, and listings
- **LDAP Authentication:** Optional, fallback to local, creates users on first LDAP login
- **Password Reset:** Secure, token-based, for local accounts
- **Sidebar Navigation:** Types and categories always visible for quick filtering

---

## Project Structure

```text
classifieds/
├── Dockerfile
├── LICENSE
├── README.md
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── forms.py
│   ├── ldap_auth.py
│   ├── models.py
│   ├── routes
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── errors.py
│   │   ├── listings.py
│   │   └── users.py
│   └── static
├── classifieds.service
├── docker-compose.yml
├── docs
│   ├── README.md
│   └── copilot-notes
│       ├── copilot-internationalization-guidance.md
│       ├── copilot-migrations-best-practices.md
│       ├── copilot-notes.md
│       ├── copilot-retailing-gold-standard.md
│       └── copilot-security-review-recomendations.md
├── migrations
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 04ede7750476_renamed_item_to_listing.py
├── requirements.txt
├── resources
│   └── populate_items_with_files.sql
└── wsgi.py
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
- Manage all listings (delete any listing)

### Images and Thumbnails

- Images are uploaded to `app/static/uploads/`
- Thumbnails are automatically generated at 224x224 pixels and stored in `app/static/uploads/thumbnails/`
- Thumbnails maintain aspect ratio and are centered on a white background
- Supported formats: JPG, JPEG, PNG, GIF (thumbnails are saved as JPEG)
- Use the `flask backfill-thumbnails` command to generate thumbnails for existing images

### Classifieds

- Any user can create, edit, or delete their own listings
- Admins can edit/delete any listing
- Browse by type/category via sidebar
- Listings are displayed in a card-based layout with thumbnail previews

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

### 3. Initialize the app (database and uploads directory)

```bash
FLASK_APP=app flask init
```

This creates:
- `instance/classifieds.db` (SQLite)
- `app/static/uploads` (uploaded images)
- `app/static/uploads/thumbnails` (224x224 thumbnails)
- `app/static/temp` (temp folder for ACIDized transactions when CRUDing listings)
- Default admin: `admin@classifieds.io` / password: `admin`

### 3.1. Generate thumbnails for existing images (optional)

If you have existing images from before thumbnail generation was implemented, run:

```bash
FLASK_APP=app flask backfill-thumbnails
```

This will generate thumbnails for all existing images that don't have them.

---

### 4. Run the app

#### Development

In development, you'll probably want to `source venv/bin/activate` first.

```bash
FLASK_APP=app FLASK_ENV=development flask run --debug
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

```env
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

GPLv2.

---

## Author

Created by GitHub Copilot for Fernando Mees Abreu ([https://github.com/ferabreu](https://github.com/ferabreu))

---
