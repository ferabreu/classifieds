from flask import Flask, g
from config import Config
from models import db, Type, User, Category
from flask_login import LoginManager
from flask_mail import Mail
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
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.get_db_uri(app)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def inject_sidebar_data():
        g.types = Type.query.order_by(Type.name).all()

    from routes.auth import auth_bp
    from routes.items import items_bp
    from routes.users import users_bp
    from routes.admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(items_bp, url_prefix='/')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.cli.command("init-db")
    def init_db():
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
