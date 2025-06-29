from flask import Flask, g
from config import Config
from models import db, Type, User, Category
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
import os

login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
        instance_relative_config=True
    )
    
    app.config.from_object(Config)
    
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        db_path = os.path.join(app.instance_path, Config.DB_FILENAME)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def inject_sidebar_data():
        g.types = Type.query.order_by(Type.name).all()

    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.errors import errors_bp
    from routes.listings import listings_bp
    from routes.users import users_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(errors_bp)
    app.register_blueprint(listings_bp, url_prefix='/')
    app.register_blueprint(users_bp, url_prefix='/users')

    @app.cli.command("init")
    def init():
        # Ensure static/uploads directory exists
        app.config['UPLOAD_DIR'] = os.path.join(app.root_path, app.config['UPLOAD_DIR'])
        if not os.path.exists(app.config['UPLOAD_DIR']):
            os.makedirs(app.config['UPLOAD_DIR'])
            print(f"Created uploads directory: {app.config['UPLOAD_DIR']}")
        else:
            print(f"Uploads directory already exists at {app.config['UPLOAD_DIR']}.")

        # Ensure temp directory exists
        app.config['TEMP_DIR'] = os.path.join(app.root_path, app.config['TEMP_DIR'])
        if not os.path.exists(app.config['TEMP_DIR']):
            os.makedirs(app.config['TEMP_DIR'])
            print(f"Created temp directory: {app.config['TEMP_DIR']}")
        else:
            print(f"Temp directory already exists at {app.config['TEMP_DIR']}.")

        # Check for existing database (assuming SQLite)
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///"):
            db_path = db_uri.replace("sqlite:///", "")
            if os.path.exists(db_path):
                print(f"Database already exists at {db_path}.\nDatabase initialization skipped to avoid overwriting existing data.")
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
                is_ldap_user=False
            )
            admin.set_password("admin")
            db.session.add(admin)

        # Types
        for type_name in ["Good", "Service"]:
            t = Type.query.filter_by(name=type_name).first()
            if not t:
                t = Type(name=type_name)
                db.session.add(t)
                db.session.flush()
            # Category "General" for each type
            c = Category.query.filter_by(name="General", type_id=t.id).first()
            if not c:
                c = Category(name="General", type_id=t.id)
                db.session.add(c)
        db.session.commit()
        print("Database initialized with default admin, types, and categories.")

    return app
