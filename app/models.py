# Created by GitHub Copilot for Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu)

"""
SQLAlchemy models for the classifieds Flask app.

Defines User, Category, Listing, and ListingImage entities.
Handles hierarchical categories, user accounts, and listing image management.
"""

from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import InstrumentedAttribute
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Category(db.Model):

    """
    Category model for hierarchical organization of listings.

    Supports parent-child relationships for multi-level categories.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    # Recursive fields for multi-level categories
    parent_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    parent_id: InstrumentedAttribute[Optional[int]]
    parent = db.relationship("Category", remote_side=[id], backref="children")
    listings = db.relationship("Listing", backref="category", lazy=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (db.UniqueConstraint("name", "parent_id", name="_cat_parent_uc"),)

    def __init__(
        self,
        name: str,
        parent_id: Optional[int] = None,
    ):
        self.name = name
        self.parent_id = parent_id

    @property
    def breadcrumb(self):
        """
        Returns a list of categories from root to self for breadcrumb navigation.
        """
        node = self
        nodes = []
        while node:
            # insert at front to build root -> ... -> self order
            nodes.insert(0, node)
            node = node.parent
        return nodes

    def get_full_path(self):
        """
        Return the full hierarchical path for this category.

        Example:
            Electronics > Computers > Laptops
        """
        # reuse breadcrumb to avoid duplicate traversal logic
        return " > ".join([cat.name for cat in self.breadcrumb])

    # Small serializer used by routes and APIs
    def to_dict(self):
        """
        Serialize minimal category info for API responses.
        """
        return {"id": self.id, "name": self.name}

    def get_descendant_ids(self):
        """
        Return a list of IDs for this category and all its descendants.

        Used for recursive category filtering.
        """
        ids = [self.id]
        for child in self.children:  # type: ignore # created dynamically by SQLAlchemy
            ids += child.get_descendant_ids()
        return ids
    
    @classmethod
    def get_children(cls, parent_id: Optional[int]):
        """
        Return immediate children for parent_id.
        parent_id == 0 -> return root categories (parent_id IS NULL).
        """
        if parent_id == 0 or parent_id is None:
            return cls.query.filter(cls.parent_id.is_(None)).order_by(cls.name).all()
        return cls.query.filter_by(parent_id=parent_id).order_by(cls.name).all()


class User(UserMixin, db.Model):
    """
    User model for account management.

    Stores authentication details and user profile info.
    """

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    is_ldap_user = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    listings = db.relationship("Listing", backref="owner", lazy=True)

    def __init__(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: Optional[str] = None,
        is_ldap_user: bool = False,
        is_admin: bool = False,
    ):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_ldap_user = is_ldap_user
        self.is_admin = is_admin
        if password:
            self.set_password(password)

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)


class Listing(db.Model):
    """
    Listing model for items posted in classifieds.

    Includes metadata, relationship to user, category, and associated images.
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    category_id: InstrumentedAttribute[int]
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    images = db.relationship(
        "ListingImage", backref="listing", cascade="all, delete-orphan"
    )
    # user = db.relationship('User', backref='listings')

    def __init__(
        self,
        title: str,
        description: str,
        price: float,
        user_id: int,
        category_id: int,
    ):
        self.title = title
        self.description = description
        self.price = price
        self.user_id = user_id
        self.category_id = category_id


class ListingImage(db.Model):
    """
    ListingImage model for storing image filenames and thumbnails for listings.

    Supports cascade deletion alongside listings.
    """

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    thumbnail_filename = db.Column(db.String(256), nullable=True)
    listing_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "listing.id", name="fk_listingimage_listing_id", ondelete="CASCADE"
        ),
        nullable=False,
    )
    # The listing attribute on ListingImage will be available automatically due to the backref in Listing

    def __init__(
        self,
        filename: str,
        listing_id: int,
        thumbnail_filename: Optional[str] = None,
    ):
        self.filename = filename
        self.listing_id = listing_id
        self.thumbnail_filename = thumbnail_filename
