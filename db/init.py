"""Usage: uv run --project python python db/init.py"""
import sqlite3, random
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "data" / "streaming.db"
for suffix in ("", "-wal", "-shm"):
    Path(str(path) + suffix).unlink(missing_ok=True)

conn = sqlite3.connect(path)
conn.executescript((root / "db" / "schema.sql").read_text())
conn.execute("PRAGMA journal_mode=WAL")
random.seed(42)  # same seed data every time
conn.executemany("INSERT INTO users(name, age) VALUES (?, ?)",
                 [(f"user{i}", random.randint(15, 80)) for i in range(100)])
conn.executemany("INSERT INTO songs(name, artist) VALUES (?, ?)",
                 [(f"song{i}", f"artist{i % 50}") for i in range(1000)])
conn.commit()
conn.close()
print(f"Created {path}")