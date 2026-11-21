import os, sqlite3, threading
from pathlib import Path

DB_PATH = os.environ.get(
    "DB_PATH", str(Path(__file__).resolve().parents[2] / "data" / "streaming.db"))
_local = threading.local()

def get_conn() -> sqlite3.Connection:
    """One connection per thread."""
    if not hasattr(_local, "conn"):
        c = sqlite3.connect(DB_PATH, timeout=5, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA foreign_keys=ON;
            PRAGMA busy_timeout=5000;
        """)
        _local.conn = c
    return _local.conn