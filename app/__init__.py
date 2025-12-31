# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Flask application factory and initialization.

Creates and configures the Flask app instance with database, authentication, migrations,
CLI commands, and blueprint registration.
"""

import os

from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

from .config import DevelopmentConfig, ProductionConfig, TestingConfig
from .models import Category, User, db

login_manager = LoginManager()
mail = Mail()


def create_app(config_class=None):
    if config_class is None:
        # Fallback: choose config based on FLASK_ENV
        env = os.getenv("FLASK_ENV", "development").lower()
        config_map = {
            "development": DevelopmentConfig,
            "testing": TestingConfig,
            "production": ProductionConfig,
        }
        config_class = config_map.get(env, DevelopmentConfig)

    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
        instance_relative_config=True,
    )

    app.config.from_object(config_class)
    # Always resolve to absolute paths, right after loading config
    app.config["UPLOAD_DIR"] = os.path.join(app.root_path, app.config["UPLOAD_DIR"])
    app.config["TEMP_DIR"] = os.path.join(app.root_path, app.config["TEMP_DIR"])
    app.config["THUMBNAIL_DIR"] = os.path.join(
        app.root_path, app.config["THUMBNAIL_DIR"]
    )

    # Configure logging early
    _configure_logging(app)

    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_navbar_data():
        categories = (
            Category.query.filter_by(parent_id=None).order_by(Category.name).all()
        )
        return {"categories": categories}

    @app.context_processor
    def inject_title_separator():
        return dict(title_separator=" | ")

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.categories import categories_bp
    from .routes.errors import errors_bp
    from .routes.listings import listings_bp
    from .routes.users import users_bp
    from .routes.utils import utils_bp

    # Blueprint registration order matters: more specific first, catch-all last.
    # listings_bp has /<path:category_path>path:category_path;
    #  keep it after admin/auth/categories/users/utils/error blueprints.
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(
        categories_bp
    )  # No prefix - handles /admin/categories/* and /api/categories/*
    app.register_blueprint(errors_bp)
    app.register_blueprint(
        users_bp
    )  # No prefix - handles /profile, /profile/edit, and /admin/users/*
    app.register_blueprint(utils_bp, url_prefix="/utils")
    app.register_blueprint(listings_bp, url_prefix="/")

    @app.cli.command("init")
    def init():
        # Ensure static/uploads directory exists
        app.config["UPLOAD_DIR"] = os.path.join(app.root_path, app.config["UPLOAD_DIR"])
        if not os.path.exists(app.config["UPLOAD_DIR"]):
            os.makedirs(app.config["UPLOAD_DIR"])
            print(f"Created uploads directory: {app.config['UPLOAD_DIR']}")
        else:
            print(f"Uploads directory already exists at {app.config['UPLOAD_DIR']}.")

        # Ensure thumbnails directory exists
        app.config["THUMBNAIL_DIR"] = os.path.join(
            app.root_path, app.config["THUMBNAIL_DIR"]
        )
        if not os.path.exists(app.config["THUMBNAIL_DIR"]):
            os.makedirs(app.config["THUMBNAIL_DIR"])
            print(f"Created thumbnails directory: {app.config['THUMBNAIL_DIR']}")
        else:
            print(
                f"Thumbnails directory already exists at {app.config['THUMBNAIL_DIR']}."
            )

        # Ensure temp directory exists
        app.config["TEMP_DIR"] = os.path.join(app.root_path, app.config["TEMP_DIR"])
        if not os.path.exists(app.config["TEMP_DIR"]):
            os.makedirs(app.config["TEMP_DIR"])
            print(f"Created temp directory: {app.config['TEMP_DIR']}")
        else:
            print(f"Temp directory already exists at {app.config['TEMP_DIR']}.")

        # Check for existing database (assuming SQLite)
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///"):
            db_path = db_uri.replace("sqlite:///", "")
            if os.path.exists(db_path):
                print(
                    f"Database already exists at {db_path}.\nDatabase initialization skipped to avoid overwriting existing data."
                )
                return

        # Ensure instance directory exists
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path)
            print(f"Created instance directory: {app.instance_path}")

        db.create_all()

        admin = User.query.filter_by(email="admin@classifieds.io").first()
        if not admin:
            admin = User(
                email="admin@classifieds.io",
                first_name="Admin",
                last_name="User",
                is_admin=True,
                is_ldap_user=False,
            )
            admin.set_password("admin")
            db.session.add(admin)

        db.session.commit()
        print("Database initialized with default admin user.")
        print(
            "No default categories created. Please create categories via the admin dashboard as needed."
        )

    # Import CLI commands from separate modules based on environment
    if os.environ.get("FLASK_ENV") == "development":
        from app.cli.maintenance import backfill_thumbnails

        app.cli.add_command(backfill_thumbnails)
        from app.cli.demo import demo_data

        app.cli.add_command(demo_data)

    return app


def _configure_logging(app: Flask) -> None:
    """Configure application logging.

    - Uses LOG_LEVEL from config
    - Logs to stdout if LOG_TO_STDOUT is true (default)
    - Otherwise logs to a rotating file under instance/LOG_FILE
    """
    # Avoid duplicate handlers on reloader
    if app.logger.handlers:
        return

    level_name = app.config.get("LOG_LEVEL", "INFO")
    try:
        level = getattr(logging, level_name, logging.INFO)
    except Exception:
        level = logging.INFO

    app.logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if app.config.get("LOG_TO_STDOUT", True):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        app.logger.addHandler(stream_handler)
    else:
        # Ensure instance/logs directory exists
        relative_log = app.config.get("LOG_FILE", "logs/classifieds.log")
        log_path = os.path.join(app.instance_path, relative_log)
        logs_dir = os.path.dirname(log_path)
        try:
            os.makedirs(logs_dir, exist_ok=True)
        except Exception:
            # Fallback to stdout if directory creation fails
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            app.logger.addHandler(stream_handler)
            return

        file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
