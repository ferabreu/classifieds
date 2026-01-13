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

## Code style
This project maintains a short, canonical style guide: docs/CODE_STYLE.md — please read it before contributing.
The repository also includes machine-oriented guidance for automated editors in .github/copilot-instructions.md.

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

## Initial Setup (uv)

### Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (fast package manager) — install once:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 1. Clone and install dependencies

```bash
git clone <your-repo-url> classifieds
cd classifieds
curl -LsSf https://astral.sh/uv/install.sh | sh  # if not installed already
uv sync
```

uv creates and manages the virtual environment automatically; you do not need `.venv`.

### 2. Configure environment

- Recommended: create a `.env` file in the project root (Flask auto-loads it).
  - Copy from example file `resources/.env.example` and edit values as needed:
    ```
    FLASK_APP=app
    FLASK_ENV=development
    (...)
    ```

- Or, export them in your shell:
  ```bash
  export FLASK_APP=app
  export FLASK_ENV=development
  ```

- Or prefix the variables to the command line:
```bash
FLASK_APP=app FLASK_ENV=development uv run (...)
```

### 3. Initialize the app (database and uploads directory)

```bash
FLASK_APP=app uv run flask init
```

This creates:
- `instance/classifieds.db` (SQLite)
- `app/static/uploads` (uploaded images)
- `app/static/uploads/thumbnails` (224x224 thumbnails)
- `app/static/temp` (temp folder for ACIDized transactions)
- Default admin: `admin@classifieds.io` / password: `admin`

### 3.1. Generate thumbnails for existing images (optional)

```bash
FLASK_APP=app uv run flask backfill-thumbnails
```

This will generate thumbnails for all existing images that don't have them.

---

### 4. Run the app

#### Development

```bash
FLASK_APP=app FLASK_ENV=development uv run flask run --debug
```
Visit [http://localhost:5000](http://localhost:5000)

#### Production (Gunicorn)

From the **project root**:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```
(Adjust workers/port as needed.)

## Testing

Run the pytest suite (uses in-memory SQLite and TestingConfig):

```bash
uv run pytest
```

If imports fail after pulling changes, run `uv sync` to refresh the environment. The `.venv` directory is not needed with uv and can be deleted unless used by other tools.

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

## Running the Application

This project uses [uv](https://docs.astral.sh/uv/) for dependency management (no pip/venv required).

### 1. Install uv (if needed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Sync dependencies
```bash
uv sync
```

### 3. Set environment variables
- Recommended: create a `.env` file in the project root:
  ```
  FLASK_APP=app
  FLASK_ENV=development
  ```
- Or, export them in your shell:
  ```bash
  export FLASK_APP=app
  export FLASK_ENV=development
  ```

### 4. Run the Flask app
```bash
# Prepend the variables, if not previously exported
# FLASK_APP=app FLASK_ENV=development uv run flask run --debug
uv run flask run --debug
```

### 5. Run CLI commands
```bash
uv run flask init
uv run flask backfill-thumbnails
```

**Note:**
- Do NOT prefix commands with env vars (e.g., `uv run FLASK_APP=app flask run`)—this will fail. You may, however, prefix uv with vars (`FLASK_APP=app FLASK_ENV=development uv run flask ...`)
- If you see `ModuleNotFoundError`, run `uv sync` to ensure all dependencies are installed.
- The `.venv` directory is not needed with uv and can be deleted unless used for other tools.

---

## Troubleshooting

- **ModuleNotFoundError**: run `uv sync` to ensure all dependencies are installed.
- **Database not found**: Run `flask --app app.py init`
- **Gunicorn import errors**: Always run from the project root (where `wsgi.py` is) and use `gunicorn wsgi:app`
- **Environment variables not loaded:** For Gunicorn or Docker, ensure you export variables or use a `.env` loader compatible with your process manager.

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

Code created by GitHub Copilot based on specs by Fernando Mees Abreu ([https://github.com/ferabreu](https://github.com/ferabreu))

---
