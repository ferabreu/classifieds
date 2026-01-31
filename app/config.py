# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot
at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Flask application configuration classes.

Defines environment-specific settings for development, testing,
and production deployments.
Includes database, mail, LDAP, upload directories, and feature toggles.
"""

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Use a relative path or env var for the DB
    DB_FILENAME = "classifieds.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # LDAP auth support
    LDAP_SERVER = os.environ.get("LDAP_SERVER") or None
    LDAP_DOMAIN = os.environ.get("LDAP_DOMAIN") or None

    # Flask-Mail config (for password reset)
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or None
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 25))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() in [
        "1",
        "true",
        "yes",
    ]
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in [
        "1",
        "true",
        "yes",
    ]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", None)
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", None)
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "no-reply@classifieds.io"
    )

    # File upload support
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
    UPLOAD_DIR = os.path.join("static", "uploads")
    TEMP_DIR = os.path.join("static", "temp")
    THUMBNAIL_DIR = os.path.join("static", "uploads", "thumbnails")
    THUMBNAIL_SIZE = (224, 224)

    # Index page showcase configuration
    # Number of showcase listings on index page (4-12 recommended, 20 max)
    INDEX_SHOWCASE_COUNT = 6
    # Number of listings per category in showcase (5 recommended)
    INDEX_SHOWCASE_ITEMS_PER_CATEGORY = 5

    # INDEX_SHOWCASE_CATEGORIES: list of category IDs to display,
    # or None for auto-selection
    # Example: [1, 3, 5] to show specific categories;
    # None to auto-select from top 2N
    INDEX_SHOWCASE_CATEGORIES = None

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT", "true").lower() in [
        "1",
        "true",
        "yes",
    ]
    # If not logging to stdout, write here (under instance path)
    LOG_FILE = os.environ.get("LOG_FILE", "logs/classifieds.log")


class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL", "sqlite:///classifieds.db"
    )  # 'sqlite:///dev.db'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False  # Usually disabled for tests


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///classifieds.db")
