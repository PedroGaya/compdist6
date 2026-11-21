from .db import get_conn

class NotFound(Exception): pass
class Invalid(Exception): pass

COLS = {"users": ("name", "age"), "songs": ("name", "artist"), "playlists": ("name",)}
_ne = lambda v: isinstance(v, str) and v.strip() != ""
CHECKS = {
    "users": lambda d: _ne(d.get("name")) and isinstance(d.get("age"), int)
                       and 0 <= d["age"] <= 150,
    "songs": lambda d: _ne(d.get("name")) and _ne(d.get("artist")),
    "playlists": lambda d: _ne(d.get("name")),
}

def _page(limit, offset):
    return max(1, min(int(limit or 50), 200)), max(0, int(offset or 0))

def _get(table, id):
    r = get_conn().execute(f"SELECT * FROM {table} WHERE id=?", (id,)).fetchone()
    if r is None: raise NotFound(f"{table} {id}")
    return dict(r)

def _create(table, data, extra=None):
    if not CHECKS[table](data): raise Invalid(table)
    vals = dict(extra or {})
    vals.update({c: data[c] for c in COLS[table]})
    q = ", ".join("?" for _ in vals)
    cur = get_conn().execute(
        f"INSERT INTO {table}({', '.join(vals)}) VALUES ({q})", tuple(vals.values()))
    return _get(table, cur.lastrowid)

def _update(table, id, data):
    if not CHECKS[table](data): raise Invalid(table)
    sets = ", ".join(f"{c}=?" for c in COLS[table])
    cur = get_conn().execute(
        f"UPDATE {table} SET {sets} WHERE id=?", (*[data[c] for c in COLS[table]], id))
    if cur.rowcount == 0: raise NotFound(f"{table} {id}")
    return _get(table, id)

def _delete(table, id):
    if get_conn().execute(f"DELETE FROM {table} WHERE id=?", (id,)).rowcount == 0:
        raise NotFound(f"{table} {id}")

def _list(table, limit, offset):
    l, o = _page(limit, offset)
    rows = get_conn().execute(
        f"SELECT * FROM {table} ORDER BY id LIMIT ? OFFSET ?", (l, o)).fetchall()
    return [dict(r) for r in rows]

# Users
def create_user(name, age): return _create("users", {"name": name, "age": age})
def get_user(id): return _get("users", id)
def list_users(limit=50, offset=0): return _list("users", limit, offset)
def update_user(id, name, age): return _update("users", id, {"name": name, "age": age})
def delete_user(id): _delete("users", id)

# Songs
def create_song(name, artist): return _create("songs", {"name": name, "artist": artist})
def get_song(id): return _get("songs", id)
def list_songs(limit=50, offset=0): return _list("songs", limit, offset)
def update_song(id, name, artist): return _update("songs", id, {"name": name, "artist": artist})
def delete_song(id): _delete("songs", id)

# Playlists
def create_playlist(user_id, name):
    _get("users", user_id)
    return _create("playlists", {"name": name}, {"user_id": user_id})
def get_playlist(id): return _get("playlists", id)
def list_playlists(user_id, limit=50, offset=0):
    _get("users", user_id)
    l, o = _page(limit, offset)
    rows = get_conn().execute(
        "SELECT * FROM playlists WHERE user_id=? ORDER BY id LIMIT ? OFFSET ?",
        (user_id, l, o)).fetchall()
    return [dict(r) for r in rows]
def update_playlist(id, name): return _update("playlists", id, {"name": name})
def delete_playlist(id): _delete("playlists", id)

# Association
def add_song(playlist_id, song_id):
    _get("playlists", playlist_id); _get("songs", song_id)
    get_conn().execute(
        "INSERT OR IGNORE INTO playlist_songs(playlist_id, song_id) VALUES (?, ?)",
        (playlist_id, song_id))
def remove_song(playlist_id, song_id):
    cur = get_conn().execute(
        "DELETE FROM playlist_songs WHERE playlist_id=? AND song_id=?",
        (playlist_id, song_id))
    if cur.rowcount == 0: raise NotFound("link")
def list_playlist_songs(playlist_id, limit=50, offset=0):
    _get("playlists", playlist_id)
    l, o = _page(limit, offset)
    rows = get_conn().execute(
        """SELECT s.* FROM songs s JOIN playlist_songs ps ON ps.song_id = s.id
           WHERE ps.playlist_id=? ORDER BY s.id LIMIT ? OFFSET ?""",
        (playlist_id, l, o)).fetchall()
    return [dict(r) for r in rows]