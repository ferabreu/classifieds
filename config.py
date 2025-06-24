import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def get_db_uri(app):
        db_path = os.path.join(app.instance_path, "classifieds.db")
        return os.environ.get('DATABASE_URL', f"sqlite:///{db_path}")

    LDAP_SERVER = os.environ.get('LDAP_SERVER', '')
    LDAP_DOMAIN = os.environ.get('LDAP_DOMAIN', '')

    # Flask-Mail config (for password reset)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', '')  # CHANGED: default is blank
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['1', 'true', 'yes']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['1', 'true', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@classifieds.io')
    
    # File upload support
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}