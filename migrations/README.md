# Database Migrations

This directory contains SQL migration files for schema changes. These are required for production deployments using Supabase or external PostgreSQL databases.

## How to Apply Migrations

### Option 1: Supabase Dashboard SQL Editor

1. Log in to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy the contents of the migration file(s) you want to apply
5. Paste into the editor and click **Run**
6. Verify the table was created successfully

### Option 2: psql Command Line

If you have `psql` installed and direct database access:

```bash
psql -h YOUR_SUPABASE_HOST -U postgres -d postgres -f migrations/001_create_pickup_stations_table.sql
```

Replace `YOUR_SUPABASE_HOST` with your Supabase database host (e.g., `db.ubtxyzabc.supabase.co`).

### Option 3: Python Script

```python
import psycopg2

# Connect to Supabase
conn = psycopg2.connect(
    host="YOUR_SUPABASE_HOST",
    database="postgres",
    user="postgres",
    password="YOUR_SUPABASE_PASSWORD"
)
cursor = conn.cursor()

# Read and execute migration
with open('migrations/001_create_pickup_stations_table.sql', 'r') as f:
    cursor.execute(f.read())

conn.commit()
cursor.close()
conn.close()

print("Migration applied successfully!")
```

## Migration File Naming

Use sequential prefixes with descriptive names:
- `001_create_pickup_stations_table.sql`
- `002_add_some_column.sql`
- `003_create_index.sql`

## Important Notes

- For production, **always backup your database** before applying migrations
- In `render.yaml`, ensure `AUTO_CREATE_TABLES=false` so schema is managed externally
- New SQLAlchemy models require corresponding migration files before deployment
- The app's `db.create_all()` is **disabled in production** (checked by `_should_auto_create_tables()`)

## Rollback

If a migration fails or needs to be reverted, no automatic rollback is provided. You must:
1. Write a corresponding rollback SQL script (e.g., `DROP TABLE pickup_stations;`)
2. Test it in a staging environment
3. Apply it manually to production

Alternatively, use a migration tool like Alembic for automatic rollback support.
