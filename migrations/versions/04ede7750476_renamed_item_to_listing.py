# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This migration was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Rename item/item_image to listing/listing_image, including FKs (SQLite-safe)

Revision ID: 04ede7750476
Revises: 
Create Date: 2025-06-28 23:07:59.025515

"""
from alembic import op


revision = '04ede7750476'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Rename table 'item' to 'listing'
    op.rename_table('item', 'listing')

    # 2. Rebuild 'item_image' as 'listing_image' with renamed FK column
    with op.batch_alter_table('item_image', schema=None) as batch_op:
        batch_op.alter_column('item_id', new_column_name='listing_id')
    
    op.rename_table('item_image', 'listing_image')

    # SQLite batch_alter_table automatically recreates FKs

def downgrade():
    # 1. Rename table 'listing' back to 'item'
    op.rename_table('listing', 'item')
    
    # 2. Rebuild 'listing_image' as 'item_image' with FK column renamed back
    op.rename_table('listing_image', 'item_image')
    with op.batch_alter_table('item_image', schema=None) as batch_op:
        batch_op.alter_column('listing_id', new_column_name='item_id')