import multiprocessing
import os


def _coerce_port(raw_port, default="10000"):
    """Return a valid TCP port string from common platform PORT formats."""
    raw_port = (raw_port or "").strip()
    if ":" in raw_port:
        raw_port = raw_port.rsplit(":", 1)[-1].strip()
    if raw_port.isdigit() and 1 <= int(raw_port) <= 65535:
        return raw_port
    return default


port = _coerce_port(os.getenv("PORT"))
bind = f"0.0.0.0:{port}"

# Ensure availability even when one request (for example /health/db) is waiting on DB.
default_workers = max(2, (multiprocessing.cpu_count() * 2) + 1)
workers = int(os.getenv("WEB_CONCURRENCY", str(default_workers)))
threads = int(os.getenv("GUNICORN_THREADS", "2"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")

# Keep requests from hanging forever at the worker level.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "90"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Log to stdout/stderr for Render log collection.
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
