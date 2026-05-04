#!/usr/bin/env python3
"""
Ensure the `consignment` table has the columns expected by the current model.

Usage:
  DATABASE_URL="postgresql://user:pass@host:5432/dbname" python scripts/ensure_consignment_columns.py

The script is idempotent and uses `ADD COLUMN IF NOT EXISTS` so it is safe
to run multiple times. It connects using the `DATABASE_URL` env var.
"""
import os
import sys
import psycopg2
from psycopg2 import sql


ALTER_STATEMENTS = [
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS pickup_address TEXT",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS drop_address TEXT",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS pickup_lat DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS pickup_lng DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS drop_lat DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS drop_lng DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS eta VARCHAR(100)",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS eta_debug_json TEXT",
]


def main():
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        print("ERROR: DATABASE_URL environment variable is not set.")
        sys.exit(2)

    try:
        conn = psycopg2.connect(dsn)
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(3)

    try:
        with conn:
            with conn.cursor() as cur:
                for stmt in ALTER_STATEMENTS:
                    print(f"Applying: {stmt}")
                    cur.execute(sql.SQL(stmt))
        print("Schema ensure complete.")
    except Exception as e:
        print(f"ERROR: Failed to apply schema changes: {e}")
        sys.exit(4)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
