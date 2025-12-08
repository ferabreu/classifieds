"""
Add url_name field to Category for URL-safe hierarchical paths.

Revision ID: 4f8a9b2c3d1e
Revises: a1b2c3d4e5f6
Create Date: 2025-12-04

SQLite-compatible migration using batch mode for constraint operations.
"""

import sqlalchemy as sa
from alembic import op
from slugify import slugify

revision = '4f8a9b2c3d1e'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add column as nullable first to avoid constraint violation on default value
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('url_name', sa.String(128), nullable=True))

    # 2. Backfill data
    conn = op.get_bind()
    res = conn.execute(sa.text("SELECT id, name FROM category"))
    results = res.fetchall()

    for cat_id, name in results:
        # Use slugify for proper Unicode handling
        slug = slugify(name, max_length=128, word_boundary=True, separator='-')

        conn.execute(
            sa.text("UPDATE category SET url_name = :slug WHERE id = :id"),
            {"slug": slug, "id": cat_id},
        )

    # 3. Apply constraints (NOT NULL and UNIQUE)
    # If duplicate names or url_names exist within the same parent, this step will fail with IntegrityError.
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.alter_column('url_name', nullable=False, existing_type=sa.String(128))
        # Sibling uniqueness: category names must be unique within the same parent
        batch_op.create_unique_constraint(
            'uk_category_name_parent', ['name', 'parent_id']
        )
        # Sibling uniqueness: url_names must also be unique within the same parent
        batch_op.create_unique_constraint(
            'uk_category_url_name_parent', ['url_name', 'parent_id']
        )


def downgrade():
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_constraint('uk_category_url_name_parent', type_='unique')
        batch_op.drop_constraint('uk_category_name_parent', type_='unique')
        batch_op.drop_column('url_name')
