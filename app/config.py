import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Use a relative path or env var for the DB
    DB_FILENAME = "classifieds.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # LDAP auth support
    LDAP_SERVER = os.environ.get("LDAP_SERVER", "")
    LDAP_DOMAIN = os.environ.get("LDAP_DOMAIN", "")

    # Flask-Mail config (for password reset)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
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


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL", "sqlite:///classifieds.db"
    )  #'sqlite:///dev.db'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False  # Usually disabled for tests


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///classifieds.db")
