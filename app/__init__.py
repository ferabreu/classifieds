from flask import Flask, g
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from .config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from .models import db, Category, Type, User, ListingImage
import os
import uuid

login_manager = LoginManager()
mail = Mail()

def create_app(config_class=None):
    if config_class is None:
        # Fallback: choose config based on FLASK_ENV
        env = os.getenv('FLASK_ENV', 'development').lower()
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
        instance_relative_config=True
    )
    
    app.config.from_object(config_class)
    # Always resolve to absolute paths, right after loading config
    app.config['UPLOAD_DIR'] = os.path.join(app.root_path, app.config['UPLOAD_DIR'])
    app.config['TEMP_DIR'] = os.path.join(app.root_path, app.config['TEMP_DIR'])
    app.config['THUMBNAIL_DIR'] = os.path.join(app.root_path, app.config['THUMBNAIL_DIR'])
    
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_navbar_data():
        types = Type.query.order_by(Type.name).all()
        good_type = next((t for t in types if t.name.lower() == "good"), None)
        service_type = next((t for t in types if t.name.lower() == "service"), None)
        goods_categories = good_type.categories if good_type else []
        goods_type_id = good_type.id if good_type else None
        services_categories = service_type.categories if service_type else []
        services_type_id = service_type.id if service_type else None
        return {
            "goods_categories": goods_categories,
            "goods_type_id": goods_type_id,
            "services_categories": services_categories,
            "services_type_id": services_type_id
        }

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.errors import errors_bp
    from .routes.listings import listings_bp
    from .routes.users import users_bp
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

        # Ensure thumbnails directory exists
        app.config['THUMBNAIL_DIR'] = os.path.join(app.root_path, app.config['THUMBNAIL_DIR'])
        if not os.path.exists(app.config['THUMBNAIL_DIR']):
            os.makedirs(app.config['THUMBNAIL_DIR'])
            print(f"Created thumbnails directory: {app.config['THUMBNAIL_DIR']}")
        else:
            print(f"Thumbnails directory already exists at {app.config['THUMBNAIL_DIR']}.")

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

    @app.cli.command("backfill-thumbnails")
    def backfill_thumbnails():
        """Generate thumbnails for existing images that don't have them."""
        from .routes.utils import create_thumbnail
        
        # Get all images without thumbnails
        images_without_thumbnails = ListingImage.query.filter(
            ListingImage.thumbnail_filename.is_(None)
        ).all()
        
        if not images_without_thumbnails:
            print("No images found that need thumbnail generation.")
            return
        
        print(f"Found {len(images_without_thumbnails)} images without thumbnails.")
        
        upload_dir = app.config['UPLOAD_DIR']
        thumbnail_dir = app.config['THUMBNAIL_DIR']
        
        success_count = 0
        error_count = 0
        
        for image in images_without_thumbnails:
            try:
                # Check if original image exists
                original_path = os.path.join(upload_dir, image.filename)
                if not os.path.exists(original_path):
                    print(f"Warning: Original image not found: {image.filename}")
                    error_count += 1
                    continue
                
                # Generate unique thumbnail filename
                import uuid
                thumbnail_filename = f"{uuid.uuid4().hex}.jpg"
                thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
                
                # Create thumbnail
                if create_thumbnail(original_path, thumbnail_path):
                    # Update database record
                    image.thumbnail_filename = thumbnail_filename
                    db.session.add(image)
                    success_count += 1
                    print(f"Generated thumbnail for {image.filename}")
                else:
                    print(f"Failed to generate thumbnail for {image.filename}")
                    error_count += 1
                    
            except Exception as e:
                print(f"Error processing {image.filename}: {e}")
                error_count += 1
        
        try:
            db.session.commit()
            print(f"\nThumbnail generation completed:")
            print(f"Successfully processed: {success_count}")
            print(f"Errors: {error_count}")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes to database: {e}")

    return app
