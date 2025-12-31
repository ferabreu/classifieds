# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This migration was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Add single-column index on Category.url_name to match model definition.

Revision ID: c2b7f4d1a9e0
Revises: 4f8a9b2c3d1e
Create Date: 2025-12-22

This migration is SQLite-friendly and safely checks for existing index
before creating it, to accommodate environments where the index may
already exist.
"""

import sqlalchemy as sa
from alembic import op


revision = "c2b7f4d1a9e0"
down_revision = "4f8a9b2c3d1e"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = [ix["name"] for ix in inspector.get_indexes("category")]

    if "ix_category_url_name" not in existing_indexes:
        # Create single-column index on url_name to align with models.py (index=True)
        op.create_index("ix_category_url_name", "category", ["url_name"])  # noqa: ALEMBIC001


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = [ix["name"] for ix in inspector.get_indexes("category")]

    if "ix_category_url_name" in existing_indexes:
        op.drop_index("ix_category_url_name", table_name="category")  # noqa: ALEMBIC001
