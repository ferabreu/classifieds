"""
Tests for category cycle protection.

Tests cover:
- Form-level validation (prevents invalid parent assignment via form)
- Database-level validation (prevents cycles at commit time)
- Integration: end-to-end cycle prevention during edit operations
"""

import pytest

from app import db
from app.forms import CategoryForm
from app.models import Category


@pytest.fixture()
def categories_hierarchy(app):
    """Create a category hierarchy: Root -> Parent -> Child -> Grandchild
    Returns IDs instead of objects to avoid session detachment issues.
    """
    with app.app_context():
        root = Category(name="Root", url_name="root")
        parent = Category(name="Parent", url_name="parent", parent_id=None)
        child = Category(name="Child", url_name="child")
        grandchild = Category(name="Grandchild", url_name="grandchild")

        db.session.add_all([root, parent, child, grandchild])
        db.session.flush()

        # Build hierarchy: parent -> child -> grandchild
        child.parent_id = parent.id
        grandchild.parent_id = child.id
        db.session.commit()

        return {
            "root_id": root.id,
            "parent_id": parent.id,
            "child_id": child.id,
            "grandchild_id": grandchild.id,
        }


class TestFormValidationStringToIntConversion:
    """Test that form validator properly converts SelectField string to int"""

    def test_validate_parent_id_converts_string_to_int(self, app, categories_hierarchy):
        """Validator should convert SelectField string to int for comparison"""
        with app.app_context():
            child = db.session.get(Category, categories_hierarchy["child_id"])
            form = CategoryForm(obj=child)

            # Manually set _obj which WTForms would normally do
            form._obj = child

            # SelectField returns string; test that convert to int works
            form.parent_id.data = str(child.id)

            # Before fix: comparison would be "3" == 3 (False, validation skipped)
            # After fix: comparison should be 3 == 3 (True, raises ValidationError)
            from wtforms.validators import ValidationError

            try:
                form.validate_parent_id(form.parent_id)
                pytest.fail("Expected ValidationError for self-parent assignment")
            except ValidationError as e:
                assert "own parent" in str(e)

    def test_validate_parent_id_handles_none_string(self, app, categories_hierarchy):
        """Validator should handle '0' or empty string (no parent)"""
        with app.app_context():
            child = db.session.get(Category, categories_hierarchy["child_id"])
            form = CategoryForm(obj=child)
            form._obj = child

            # Test "0" (no parent) doesn't raise
            form.parent_id.data = "0"
            form.validate_parent_id(form.parent_id)  # Should not raise

            # Test empty string doesn't raise
            form.parent_id.data = ""
            form.validate_parent_id(form.parent_id)  # Should not raise

    def test_validate_parent_id_allows_valid_parent(self, app, categories_hierarchy):
        """Validator should allow valid parent assignments"""
        with app.app_context():
            grandchild = db.session.get(Category, categories_hierarchy["grandchild_id"])
            root = db.session.get(Category, categories_hierarchy["root_id"])

            form = CategoryForm(obj=grandchild)
            form._obj = grandchild

            # Set valid unrelated category as parent
            form.parent_id.data = str(root.id)
            form.validate_parent_id(form.parent_id)  # Should not raise


class TestDatabaseLevelCycleProtection:
    """Test database-level cycle protection via before_flush listener"""

    def test_database_prevents_self_parent_cycle(self, app, categories_hierarchy):
        """Database should prevent committing a category as its own parent"""
        with app.app_context():
            child = db.session.get(Category, categories_hierarchy["child_id"])
            original_parent_id = child.parent_id

            # Try to set category as its own parent
            child.parent_id = child.id

            # Flush should fail due to cycle detection listener
            from sqlalchemy.exc import IntegrityError

            try:
                db.session.flush()
                db.session.rollback()
                pytest.fail("Database should have prevented self-parent cycle at flush")
            except (IntegrityError, Exception):
                # Expected: cycle detection should prevent flush
                db.session.rollback()

            # Verify the change was rolled back
            child = db.session.get(Category, categories_hierarchy["child_id"])
            assert child.parent_id == original_parent_id


class TestIntegrationCycleProtection:
    """Integration tests for cycle protection in edit operations"""

    def test_edit_category_with_valid_parent(self, app, categories_hierarchy):
        """Editing category with valid parent should succeed"""
        with app.app_context():
            grandchild = db.session.get(Category, categories_hierarchy["grandchild_id"])
            root = db.session.get(Category, categories_hierarchy["root_id"])
            original_count = db.session.query(Category).count()

            # Edit grandchild to have root as parent
            grandchild.parent_id = root.id
            db.session.commit()

            # Verify change was applied
            grandchild = db.session.get(Category, categories_hierarchy["grandchild_id"])
            assert grandchild.parent_id == root.id
            assert db.session.query(Category).count() == original_count
