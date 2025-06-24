# Flask-Migrate & Alembic: Best Practices

## 1. Always Track Migrations in Version Control
- Commit your entire `migrations/` directory (except `__pycache__` and cache files) to Git.
- Never modify or delete migration scripts once applied to production.

## 2. Never Edit Existing Migrations
- If you need to change your models, create a new migration with `flask db migrate`.
- Only edit migration scripts **before** they are applied to any database.

## 3. Keep `alembic_version` Table and Migrations in Sync
- The `alembic_version` table tells Alembic what migration your DB is at.
- If you delete or reset migrations, also reset the `alembic_version` table.

## 4. Use `flask db stamp head` To Realign
- If you manually align your DB schema with your models (for instance, after recreating migrations), run:
  ```
  flask db stamp head
  ```
  This marks the DB as up-to-date without running any migrations.

## 5. Backup Before Migrating
- Always back up your database before running migrations, especially in production.

## 6. Use Separate Databases for Dev & Prod
- Never run test migrations against your production database.
- Use a local/test DB to experiment with migrations.

## 7. Review Auto-Generated Migrations
- Alembic can’t always detect every change (e.g., column type changes).
- Always inspect generated migration scripts and adjust as needed.

## 8. Handle Legacy or Out-of-Sync Databases Carefully
- If the DB and models are out of sync:
  1. Align schema with models manually.
  2. Generate a new baseline migration.
  3. Use `flask db stamp head`.

## 9. Use Meaningful Migration Messages
- When running `flask db migrate -m "message"`, use clear, descriptive messages.

## 10. Never Delete the Migrations Directory in Production
- Deleting `migrations/` is only safe in development. In production, this will break your ability to migrate.

---

### Useful Commands

- **Generate migration:**  
  `flask db migrate -m "describe your change"`
- **Apply migration:**  
  `flask db upgrade`
- **Downgrade:**  
  `flask db downgrade`
- **Show migration history:**  
  `flask db history`
- **Show current revision:**  
  `flask db current`
- **Stamp database with latest revision (no schema change):**  
  `flask db stamp head`

---

### Troubleshooting Tips

- **Migration not detected:** Check if you made changes to the models and that Alembic can auto-detect them.
- **"Can't locate revision" error:** The `alembic_version` table references a missing file. Use `flask db stamp` or manually update the table.
- **Database out of sync:** Align schema, generate a new migration, and stamp the DB.
- **Lost migration scripts:** Restore from version control or align schema and recreate the baseline.

---

Keep this cheat sheet handy and migration pains will be rare!