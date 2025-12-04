"""
Add url_name field to Category for URL-safe hierarchical paths.

Revision ID: abc123def456
Revises: a1b2c3d4e5f6
Create Date: 2025-12-04

SQLite-compatible migration using batch mode for constraint operations.
"""
import re
from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def generate_url_name(name):
    """
    Generate a URL-safe name from a display name.
    
    Converts to lowercase, replaces spaces and special characters with hyphens,
    and strips leading/trailing hyphens.
    """
    # Convert to lowercase
    url_name = name.lower()
    # Replace spaces and special characters with hyphens
    url_name = re.sub(r"[^\w-]", "-", url_name)
    # Replace multiple consecutive hyphens with a single hyphen
    url_name = re.sub(r"-+", "-", url_name)
    # Strip leading and trailing hyphens
    url_name = url_name.strip("-")
    return url_name


def upgrade():
    # SQLite requires batch mode for adding constraints.
    # We use the copy-and-move strategy: create a new table, copy data, drop old, rename.
    
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('url_name', sa.String(128), nullable=False, server_default='temp', index=True)
        )
        # Add unique constraint within the batch operation
        batch_op.create_unique_constraint(
            '_cat_url_name_parent_uc',
            ['url_name', 'parent_id']
        )
    
    # Backfill url_name for all existing categories
    conn = op.get_bind()
    categories = conn.execute(sa.text('SELECT id, name FROM category ORDER BY id')).fetchall()
    
    for cat_id, name in categories:
        if name:
            url_name = generate_url_name(name)
            conn.execute(
                sa.text('UPDATE category SET url_name = :url_name WHERE id = :id'),
                {'url_name': url_name, 'id': cat_id}
            )


def downgrade():
    # Use batch mode for downgrade as well
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_constraint('_cat_url_name_parent_uc', type_='unique')
        batch_op.drop_column('url_name')
