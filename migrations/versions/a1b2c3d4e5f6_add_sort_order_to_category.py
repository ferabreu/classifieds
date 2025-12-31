# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This migration was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Add sort_order field to Category and initialize values for existing categories.

Revision ID: a1b2c3d4e5f6
Revises: 7f2e1a3b9cde
Create Date: 2025-09-26
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '7f2e1a3b9cde'
branch_labels = None
depends_on = None

def upgrade():
    # Add the sort_order column, default to 0
    op.add_column('category', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))

    # Fill sort_order for existing categories by alphabetical order within each parent
    conn = op.get_bind()
    categories = conn.execute(sa.text('SELECT id, parent_id FROM category ORDER BY parent_id, name')).fetchall()
    parent_map = {}
    for cat in categories:
        parent_map.setdefault(cat.parent_id, []).append(cat.id)
    updates = []
    for parent_id, ids in parent_map.items():
        for order, cat_id in enumerate(ids, start=1):
            updates.append({'id': cat_id, 'sort_order': order})
    for upd in updates:
        conn.execute(sa.text('UPDATE category SET sort_order = :sort_order WHERE id = :id'), upd)
    # Note: SQLite does not support altering column defaults after creation.
    # The default will remain as 0, which is safe for SQLite in production.

def downgrade():
    op.drop_column('category', 'sort_order')
