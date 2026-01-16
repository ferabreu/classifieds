---
description: 'SQLite migration patterns with batch mode and NOT NULL backfilling'
applyTo: '**/migrations/versions/*.py'
---

# Alembic Database Migrations for SQLite

## ⚠️ CRITICAL: SQLite Limitations

**SQLite does NOT support `ALTER COLUMN` operations**. Always use batch mode for ALL schema changes.

---

## Batch Mode Pattern (REQUIRED)

```python
# ✅ CORRECT - Batch mode for ALL schema changes
def upgrade():
    with op.batch_alter_table('table_name', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('new_col', sa.String(128), nullable=False, server_default='temp')
        )
        batch_op.create_unique_constraint('uk_name', ['col1', 'col2'])
    
    # Backfill after batch operations
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE table_name SET new_col = 'value' WHERE new_col = 'temp'"))
    conn.commit()

# ❌ WRONG - Will fail on SQLite
def upgrade():
    op.alter_column('table_name', 'column', nullable=False)  # FAILS!
    op.create_unique_constraint('uk_name', 'table_name', ['col'])  # FAILS!
```

---

## Migration Rules

1. **ALL** schema operations go inside `with op.batch_alter_table():`
2. Use `server_default='temp'` for NOT NULL columns, then backfill
3. Downgrade must also use batch mode
4. When in doubt, use batch mode

---

## Common Patterns

### Adding NOT NULL Column with Unique Constraint

```python
def upgrade():
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('url_name', sa.String(128), nullable=False, 
                     server_default='temp', index=True)
        )
        batch_op.create_unique_constraint(
            'uk_category_url_name_parent',
            ['url_name', 'parent_id']
        )
    
    # Backfill data after batch operations
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE category 
        SET url_name = LOWER(REPLACE(REPLACE(TRIM(name), ' ', '_'), '-', '_'))
        WHERE url_name = 'temp'
    """))
    conn.commit()

def downgrade():
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_constraint('uk_category_url_name_parent', type_='unique')
        batch_op.drop_column('url_name')
```

### Modifying Column Constraints

```python
def upgrade():
    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False, server_default='active')
    
    # Update existing NULLs
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE listing SET status = 'active' WHERE status IS NULL"))
    conn.commit()

def downgrade():
    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=True, server_default=None)
```

### Adding Multiple Constraints

```python
def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('verified_email', sa.Boolean(), nullable=False, server_default='0')
        )
        batch_op.create_index('ix_user_email_verified', ['email', 'verified_email'])
        batch_op.create_check_constraint('ck_user_email_notnull', 'email IS NOT NULL')
    
    conn = op.get_bind()
    conn.commit()

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('ck_user_email_notnull', type_='check')
        batch_op.drop_index('ix_user_email_verified')
        batch_op.drop_column('verified_email')
```

---

## Anti-Patterns (NEVER DO THIS)

### ❌ Never: Direct ALTER COLUMN
```python
# WRONG - Will fail on SQLite!
op.alter_column('user', 'email', nullable=False)
```

### ❌ Never: Constraints Outside Batch Mode
```python
# WRONG - Will fail on SQLite!
op.create_unique_constraint('uk_name', 'table_name', ['col'])
op.drop_constraint('fk_listing_user_id', type_='foreignkey')
```

### ❌ Never: Add NOT NULL Without server_default
```python
# WRONG - Alembic will fail when backfilling
batch_op.add_column(sa.Column('status', sa.String(50), nullable=False))
```

---

## Documentation Standards

### Migration Comments
Document complex migrations with clear explanations:

```python
"""Add URL-safe slugs to categories for cleaner URLs.

Revision ID: 4f8a9b2c3d1e
Revises: 48e4d4abe479
Create Date: 2025-01-15 10:30:00.000000
"""

def upgrade():
    # Add url_name column with temporary default
    # Will backfill with slugified category names
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('url_name', sa.String(128), nullable=False, 
                     server_default='temp', index=True)
        )
    
    # Transform existing names to URL-safe slugs
    # Example: "Home & Garden" -> "home_garden"
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE category 
        SET url_name = LOWER(REPLACE(REPLACE(TRIM(name), ' ', '_'), '-', '_'))
        WHERE url_name = 'temp'
    """))
    conn.commit()
```

### Edge Case Handling
Account for edge cases in data migrations:

```python
def upgrade():
    # Handle potential NULL values before adding NOT NULL constraint
    conn = op.get_bind()
    
    # Set default for existing NULL values
    conn.execute(sa.text("UPDATE listing SET status = 'active' WHERE status IS NULL"))
    
    # Handle empty strings
    conn.execute(sa.text("UPDATE listing SET status = 'active' WHERE status = ''"))
    
    conn.commit()
    
    # Now safe to add NOT NULL constraint
    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False, server_default='active')
```

---

## Error Handling

### Verify Data Before Constraints

```python
def upgrade():
    # Before adding unique constraint, check for duplicates
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT url_name, COUNT(*) as count 
        FROM category 
        GROUP BY url_name 
        HAVING count > 1
    """))
    
    duplicates = result.fetchall()
    if duplicates:
        # Handle duplicates by appending incremental suffix
        for url_name, count in duplicates:
            conn.execute(sa.text("""
                UPDATE category 
                SET url_name = url_name || '_' || id 
                WHERE url_name = :url_name
            """), {'url_name': url_name})
        conn.commit()
    
    # Now safe to add unique constraint
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.create_unique_constraint('uk_category_url_name', ['url_name'])
```

---

## Workflow Checklist

1. ✅ Wrap ALL schema changes in `op.batch_alter_table()`
2. ✅ Use `server_default` for NOT NULL columns
3. ✅ Backfill data AFTER batch context closes
4. ✅ Handle edge cases (NULLs, empty strings, duplicates)
5. ✅ Include corresponding `downgrade()` in batch mode
6. ✅ Add comments explaining complex transformations
7. ✅ Test migration: `uv run flask db upgrade` and `uv run flask db downgrade`

---

## Testing Migrations

```bash
# Create migration
uv run flask db migrate -m "description"

# Review generated file - check for batch mode usage

# Apply migration
uv run flask db upgrade

# Test rollback
uv run flask db downgrade

# Verify database state after both operations
```

### Test Edge Cases
- Empty database (no existing rows)
- Database with NULL values in affected columns
- Database with duplicate values before unique constraints
- Large datasets (performance testing)
