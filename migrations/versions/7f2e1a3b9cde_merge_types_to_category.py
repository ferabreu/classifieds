"""Merge Types into Category hierarchy and update Listings

Revision ID: 7f2e1a3b9cde
Revises: befe2371cacf
Create Date: 2025-08-04

"""
from alembic import op
import sqlalchemy as sa

revision = '7f2e1a3b9cde'
down_revision = 'befe2371cacf'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()

    # 1. Create top-level categories for each type
    type_rows = conn.execute(sa.text("SELECT id, name FROM type")).fetchall()
    type_id_to_cat_id = {}

    for type_row in type_rows:
        # Insert top-level category with type_id set (to satisfy NOT NULL constraint)
        conn.execute(
            sa.text("INSERT INTO category (name, parent_id, type_id) VALUES (:name, NULL, :type_id)"),
            {"name": type_row.name, "type_id": type_row.id}
        )
        top_cat_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()
        type_id_to_cat_id[type_row.id] = top_cat_id

    # 2. Move all categories under their new parent
    cat_rows = conn.execute(sa.text("SELECT id, type_id FROM category WHERE type_id IS NOT NULL")).fetchall()
    for cat_row in cat_rows:
        parent_id = type_id_to_cat_id.get(cat_row.type_id)
        if parent_id:
            conn.execute(
                sa.text("UPDATE category SET parent_id = :parent_id WHERE id = :id"),
                {"parent_id": parent_id, "id": cat_row.id}
            )

    # 3. Remove type_id from category and listing tables
    # SQLite requires table recreation for dropping columns
    # Alembic batch operations will handle this

    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_constraint('_cat_type_uc', type_='unique')
        batch_op.drop_column('type_id')

    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.drop_column('type_id')

    # 4. Drop the type table
    op.drop_table('type')

def downgrade():
    # Downgrade not implemented
    pass