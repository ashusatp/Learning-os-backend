# Alembic Migration Guide

## What is Alembic?

Alembic is a database migration tool for SQLAlchemy. It tracks changes to your database schema over time, letting you upgrade (apply changes) and downgrade (undo changes) safely.

## Workflow: After Changing Models

Whenever you modify a SQLAlchemy model (add/remove/change columns, tables, etc.), follow these two steps:

### Step 1: Generate the migration

```bash
alembic revision --autogenerate -m "describe what changed"
```

- Compares your Python models against the current database schema
- Creates a new migration file in `alembic/versions/`
- The file contains `upgrade()` and `downgrade()` functions
- Does NOT touch the database yet
- Always review the generated file before applying

### Step 2: Apply the migration

```bash
alembic upgrade head
```

- Runs the `upgrade()` function against your database
- Actually modifies the database schema
- `head` means "apply all pending migrations"

## Example

Say you add a `phone` column to the User model:

```python
# 1. Edit app/models/user.py
phone = Column(String, nullable=True)
```

```bash
# 2. Generate migration
alembic revision --autogenerate -m "add phone to users"
# Creates: alembic/versions/abc123_add_phone_to_users.py

# 3. Review the generated file (always check it!)

# 4. Apply it
alembic upgrade head
```

## Common Commands

| Command                                          | What it does                          |
| ------------------------------------------------ | ------------------------------------- |
| `alembic revision --autogenerate -m "message"`   | Generate migration from model changes |
| `alembic upgrade head`                           | Apply all pending migrations          |
| `alembic downgrade -1`                           | Undo the last migration               |
| `alembic current`                                | Show which migration the DB is at     |
| `alembic history`                                | List all migrations                   |
| `alembic heads`                                  | Show the latest migration file        |
| `alembic upgrade +1`                             | Apply only the next migration         |
| `alembic downgrade base`                         | Undo ALL migrations (reset DB)        |

## Important Notes

- Always run `alembic revision --autogenerate` from the `backend/` directory
- Always review auto-generated migrations before applying -- autogenerate is not perfect
- Make sure all models are imported in `app/models/__init__.py` so Alembic can detect them
- The migration uses a sync connection (psycopg2), not async (asyncpg)
- Never manually edit the `alembic_version` table in the database

## Key Rule

**Model change -> `revision --autogenerate` -> review the file -> `upgrade head`**

uvicorn app.main:app --reload 