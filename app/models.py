# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot
at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

SQLAlchemy models for the classifieds Flask app.

Defines User, Category, Listing, and ListingImage entities.
Handles hierarchical categories, user accounts, and listing image management.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from slugify import slugify
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Category(db.Model):
    """
    Category model for hierarchical organization of listings.

    Supports parent-child relationships for multi-level categories.
    The url_name field stores URL-safe category names for clean hierarchical paths.
    """

    __allow_unmapped__ = True

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    url_name = db.Column(db.String(128), nullable=False, index=True)
    # Recursive fields for multi-level categories
    parent_id: InstrumentedAttribute[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("category.id"), nullable=True
    )
    parent = db.relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )  # type: ignore[assignment]
    children = db.relationship(
        "Category",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )  # type: ignore[assignment]
    listings = db.relationship("Listing", backref="category", lazy=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (
        db.UniqueConstraint("name", "parent_id", name="_cat_parent_uc"),
        db.UniqueConstraint("url_name", "parent_id", name="_cat_url_name_parent_uc"),
    )

    def __init__(
        self,
        name: str,
        parent_id: Optional[int] = None,
        url_name: Optional[str] = None,
    ):
        self.name = name
        self.parent_id = parent_id
        # Auto-generate url_name if not provided
        self.url_name = url_name or generate_url_name(name)

    @property
    def breadcrumb(self):
        """
        Returns a list of categories from root to self for breadcrumb
        navigation.

        Protects against cycles by tracking visited category ids and
        stopping if a loop is detected.
        """
        node = self
        nodes = []
        visited = set()
        while node:
            if node.id in visited:
                # cycle detected; stop traversal to avoid infinite loop
                break
            visited.add(node.id)
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

    @property
    def url_path(self):
        """
        Return the URL-safe hierarchical path for this category.

        Example:
            electronics/computers/laptops
        """
        return "/".join([cat.url_name for cat in self.breadcrumb])

    # Small serializer used by routes and APIs
    def to_dict(self):
        """
        Serialize minimal category info for API responses.
        """
        return {"id": self.id, "name": self.name}

    def get_descendant_ids(self):
        """
        Return a list of IDs for this category and all its descendants.

        Protect against cycles using a visited set.
        """

        def _collect(node, visited):
            if node.id in visited:
                return []
            visited.add(node.id)
            ids = [node.id]
            for child in node.children:  # type: ignore
                ids.extend(_collect(child, visited))
            return ids

        return _collect(self, set())

    def is_ancestor_of(self, other: "Category") -> bool:
        """
        Return True if this category is an ancestor of `other`.
        Safe against cycles.
        """
        if other is None:
            return False
        # walk up from other checking if we hit self (use visited set to avoid loops)
        node = other
        visited = set()
        while node:
            if node.id in visited:
                break
            if node.id == self.id:
                return True
            visited.add(node.id)
            node = node.parent
        return False

    def is_url_name_reserved(self) -> bool:
        """
        Return True if this category's url_name is a reserved route name.
        """
        return self.url_name.lower() in RESERVED_CATEGORY_NAMES

    @classmethod
    def get_children(cls, parent_id: Optional[int]):
        """
        Return immediate children for parent_id.
        parent_id == 0 -> return root categories (parent_id IS NULL).
        """
        if parent_id == 0 or parent_id is None:
            return cls.query.filter(cls.parent_id.is_(None)).order_by(cls.name).all()
        return cls.query.filter_by(parent_id=parent_id).order_by(cls.name).all()

    def would_create_cycle(
        self, new_parent_id: Optional[int], session: Session
    ) -> bool:
        """
        Return True if setting parent_id=new_parent_id would create a cycle.

        Uses the given SQLAlchemy session to traverse parent links safely.
        Works for both persisted and new Category instances (self.id may be None).
        """
        if not new_parent_id:
            return False
        # Quick self-check (handles persisted objects)
        if self.id is not None and new_parent_id == self.id:
            return True

        visited = set()
        current_parent_id = new_parent_id
        depth = 0
        max_depth = 500  # extremely high guard to avoid pathological loops

        while current_parent_id:
            if current_parent_id in visited:
                # encountered a loop while walking the chain => cycle
                return True
            visited.add(current_parent_id)
            # If we hit the current category id,
            # setting this parent would create a cycle
            if self.id is not None and current_parent_id == self.id:
                return True
            # fetch parent row
            parent = session.get(Category, current_parent_id)
            if parent is None:
                break
            current_parent_id = parent.parent_id
            depth += 1
            if depth > max_depth:
                # defensive: treat excessive depth as a cycle to be safe
                return True
        return False

    @classmethod
    def from_path(cls, path_string: str) -> Optional["Category"]:
        """
        Resolve a hierarchical category path to a Category object.

        Traverses the category hierarchy starting from root, matching each path
        segment against the url_name of categories at each level.

        Args:
            path_string: A slash-separated path like "vehicles/motorcycles"

        Returns:
            The Category object at the end of the path, or None if path is invalid

        Example:
            Category.from_path("vehicles/motorcycles")
            → Category(id=5, name="Motorcycles")
        """
        if not path_string or path_string == "/":
            return None

        # Parse the path into segments
        segments = [segment for segment in path_string.split("/") if segment]
        if not segments:
            return None

        # Load all categories once and build an in-memory lookup
        # keyed by (parent_id, url_name)
        all_categories = cls.query.all()
        lookup: dict[tuple[Optional[int], str], "Category"] = {
            (category.parent_id, category.url_name): category
            for category in all_categories
        }

        current_category: Optional["Category"] = None
        parent_id: Optional[int] = None

        for segment in segments:
            current_category = lookup.get((parent_id, segment))
            if current_category is None:
                # Path segment not found
                return None
            parent_id = current_category.id
        return current_category


@dataclass
class CategoryView:
    """
    Lightweight view model for category display.

    Used when we need a category-like object without database overhead
    (e.g., "Other Category" pseudo-categories in showcases).

    This is immutable and can safely be used in templates expecting
    a category-like interface with id, name, and url_path attributes.
    """

    id: int
    name: str
    url_path: str

    @classmethod
    def from_category(cls, category: Category, name_override: Optional[str] = None) -> 'CategoryView':
        """
        Create a CategoryView from a Category model instance.

        Args:
            category: The Category model to base the view on.
            name_override: Optional custom name (e.g., "Other Electronics").

        Returns:
            A CategoryView instance with the specified attributes.
        """
        return cls(
            id=category.id,
            name=name_override or category.name,
            url_path=category.url_path,
        )


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
        self.email = email.strip()
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
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
    # The listing attribute on ListingImage will be available automatically
    # due to the backref in Listing

    def __init__(
        self,
        filename: str,
        listing_id: int,
        thumbnail_filename: Optional[str] = None,
    ):
        self.filename = filename
        self.listing_id = listing_id
        self.thumbnail_filename = thumbnail_filename


@event.listens_for(Session, "before_flush")
def _prevent_category_cycle(session, flush_context, instances):
    """
    Abort flush if a Category's parent would create a cycle.
    Uses Category.would_create_cycle(session=...) for a DB-backed check.
    """
    for obj in list(session.new) + list(session.dirty):
        if isinstance(obj, Category):
            # Use the effective parent_id value intended to be persisted.
            # For new/dirty objects SQLAlchemy will have obj.parent_id
            # set appropriately.
            parent_id = getattr(obj, "parent_id", None)
            if not parent_id:
                continue
            # Use helper that walks the chain via this session
            # (avoids multiple queries outside session)
            if obj.would_create_cycle(parent_id, session):
                raise ValueError("Cannot set parent: would create a category cycle.")


# Reserved route names that cannot be used as category url_name
RESERVED_CATEGORY_NAMES = {
    "admin",
    "auth",
    "profile",
    "listing",
    "api",
    "static",
    "new",
    "edit",
    "delete",
    "utils",
    "categories",
    "users",
    "listings",
    "dashboard",
}


def generate_url_name(name: str) -> str:
    """
    Generate an ASCII-only, URL-safe slug from a display name using python-slugify.

    Behavior:
    - Lowercases
    - Transliterates Unicode to ASCII (e.g., "ação" -> "acao")
    - Replaces separators with hyphens
    - Strips leading/trailing separators
    - Returns an empty string if the input contains no slug-worthy characters
    """

    return slugify(name or "", separator="-")
