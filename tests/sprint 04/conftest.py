import pytest

from app import create_app, db
from app.config import TestingConfig
from app.models import Category, Listing, User


class _TestingConfig(TestingConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False


@pytest.fixture()
def app():
    app = create_app(_TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user(app):
    with app.app_context():
        user = User(
            email="user@classifieds.io",
            first_name="Test",
            last_name="User",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "email": user.email, "password": "password123"}


@pytest.fixture()
def admin_user(app):
    with app.app_context():
        admin = User(
            email="admin@classifieds.io",
            first_name="Admin",
            last_name="User",
            is_admin=True,
        )
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "email": admin.email, "password": "adminpass"}


@pytest.fixture()
def category(app):
    with app.app_context():
        cat = Category(name="Electronics")
        db.session.add(cat)
        db.session.commit()
        return {"id": cat.id, "url_name": cat.url_name}


@pytest.fixture()
def listing(app, user, category):
    with app.app_context():
        listing = Listing(
            title="Test Listing",
            description="A test listing with enough words.",
            price=9.99,
            user_id=user["id"],
            category_id=category["id"],
        )
        db.session.add(listing)
        db.session.commit()
        return {"id": listing.id, "title": listing.title, "category_id": category["id"]}
