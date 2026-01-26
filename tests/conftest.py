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


@pytest.fixture()
def showcase_categories(app, user):
    """
    Create categories with varied characteristics for showcase testing.

    Returns 4 categories:
    - Electronics: Root category with many listings (12 listings)
    - Books: Root category with few listings (3 listings)
    - Furniture: Root category with no direct listings (0 listings)
    - Sports: Root category with moderate listings (6 listings)
    """
    with app.app_context():
        # Create categories
        electronics = Category(name="Electronics", url_name="electronics")
        books = Category(name="Books", url_name="books")
        furniture = Category(name="Furniture", url_name="furniture")
        sports = Category(name="Sports", url_name="sports")

        db.session.add_all([electronics, books, furniture, sports])
        db.session.commit()

        # Create listings for Electronics (12 listings)
        for i in range(12):
            listing = Listing(
                title=f"Electronics Item {i+1}",
                description=f"Description for electronics item {i+1}",
                price=10.0 + i,
                user_id=user["id"],
                category_id=electronics.id,
            )
            db.session.add(listing)

        # Create listings for Books (3 listings)
        for i in range(3):
            listing = Listing(
                title=f"Book {i+1}",
                description=f"Description for book {i+1}",
                price=5.0 + i,
                user_id=user["id"],
                category_id=books.id,
            )
            db.session.add(listing)

        # Create listings for Sports (6 listings)
        for i in range(6):
            listing = Listing(
                title=f"Sports Item {i+1}",
                description=f"Description for sports item {i+1}",
                price=15.0 + i,
                user_id=user["id"],
                category_id=sports.id,
            )
            db.session.add(listing)

        db.session.commit()

        return {
            "electronics": {"id": electronics.id, "url_name": electronics.url_name},
            "books": {"id": books.id, "url_name": books.url_name},
            "furniture": {"id": furniture.id, "url_name": furniture.url_name},
            "sports": {"id": sports.id, "url_name": sports.url_name},
        }


@pytest.fixture()
def category_with_children(app, user):
    """
    Create a parent category with child categories for descendant fallback testing.

    Structure:
    - Goods (parent, 2 direct listings)
      - Musical Instruments (child, 5 listings)
      - Home Appliances (child, 0 listings but inherits from parent via fallback)
    """
    with app.app_context():
        # Create parent and child categories
        goods = Category(name="Goods", url_name="goods")
        db.session.add(goods)
        db.session.commit()

        musical = Category(
            name="Musical Instruments",
            url_name="musical-instruments",
            parent_id=goods.id,
        )
        appliances = Category(
            name="Home Appliances",
            url_name="home-appliances",
            parent_id=goods.id,
        )
        db.session.add_all([musical, appliances])
        db.session.commit()

        # Add 2 listings directly to parent (Goods)
        for i in range(2):
            listing = Listing(
                title=f"General Good {i+1}",
                description=f"Description for general good {i+1}",
                price=20.0 + i,
                user_id=user["id"],
                category_id=goods.id,
            )
            db.session.add(listing)

        # Add 5 listings to Musical Instruments
        for i in range(5):
            listing = Listing(
                title=f"Musical Instrument {i+1}",
                description=f"Description for instrument {i+1}",
                price=100.0 + i * 10,
                user_id=user["id"],
                category_id=musical.id,
            )
            db.session.add(listing)

        # Home Appliances has no listings (will need descendant fallback)

        db.session.commit()

        return {
            "parent": {"id": goods.id, "url_name": goods.url_name, "name": goods.name},
            "musical": {"id": musical.id, "url_name": musical.url_name},
            "appliances": {"id": appliances.id, "url_name": appliances.url_name},
        }
