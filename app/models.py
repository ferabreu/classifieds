# Created by GitHub Copilot for Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu)

"""
SQLAlchemy models for the classifieds Flask app.

Defines User, Category, Listing, and ListingImage entities.
Handles hierarchical categories, user accounts, and listing image management.
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
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
    parent = db.relationship("Category", remote_side=[id], backref="children")
    listings = db.relationship("Listing", backref="category", lazy=True)
    __table_args__ = (db.UniqueConstraint("name", "parent_id", name="_cat_parent_uc"),)

    def get_full_path(self):
        """
        Return the full hierarchical path for this category.

        Example:
            Electronics > Computers > Laptops
        """
        names = []
        node = self
        while node:
            names.append(node.name)
            node = node.parent
        return " > ".join(reversed(names))

    def get_descendant_ids(self):
        """
        Return a list of IDs for this category and all its descendants.

        Used for recursive category filtering.
        """
        ids = [self.id]
        for child in self.children:
            ids += child.get_descendant_ids()
        return ids


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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    images = db.relationship(
        "ListingImage", backref="listing", cascade="all, delete-orphan"
    )
    #user = db.relationship('User', backref='listings')


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
