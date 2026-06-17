import os
import logging

logger = logging.getLogger(__name__)


def _is_production_env() -> bool:
    return os.getenv("FLASK_ENV", "").strip().lower() == "production"


def _resolve_secret_key() -> str:
    configured = os.environ.get("SECRET_KEY", "").strip()
    if not configured:
        if _is_production_env():
            raise RuntimeError("SECRET_KEY is required and must be set in environment variables.")

        logger.warning("SECRET_KEY is not set; using a local development fallback.")
        return "dev-local-secret-key"
    return configured


SECRET_KEY = _resolve_secret_key()