import logging

import psycopg2


logger = logging.getLogger(__name__)


CONSIGNMENT_ALTER_STATEMENTS = [
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS pickup_address TEXT",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS drop_address TEXT",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS pickup_lat DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS pickup_lng DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS drop_lat DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS drop_lng DOUBLE PRECISION",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS eta VARCHAR(100)",
    "ALTER TABLE consignment ADD COLUMN IF NOT EXISTS eta_debug_json TEXT",
]


def ensure_consignment_columns(dsn, log=None):
    """Add any missing consignment columns in a PostgreSQL database.

    This is intentionally idempotent and safe to call on every app startup.
    """
    if not dsn:
        raise ValueError("A PostgreSQL DSN is required to ensure consignment columns.")

    active_logger = log or logger

    conn = psycopg2.connect(dsn)
    try:
        with conn:
            with conn.cursor() as cur:
                for statement in CONSIGNMENT_ALTER_STATEMENTS:
                    active_logger.info("Ensuring schema: %s", statement)
                    cur.execute(statement)
        active_logger.info("Consignment schema check complete.")
    finally:
        conn.close()
