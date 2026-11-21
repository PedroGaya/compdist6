import { db } from "./db";

export class NotFound extends Error {}
export class Invalid extends Error {}

type Row = Record<string, any>;
type Table = "users" | "songs" | "playlists";

const COLS: Record<Table, string[]> = {
  users: ["name", "age"],
  songs: ["name", "artist"],
  playlists: ["name"],
};
const ne = (v: any) => typeof v === "string" && v.trim() !== "";
const CHECKS: Record<Table, (d: Row) => boolean> = {
  users: (d) =>
    ne(d.name) && Number.isInteger(d.age) && d.age >= 0 && d.age <= 150,
  songs: (d) => ne(d.name) && ne(d.artist),
  playlists: (d) => ne(d.name),
};

const page = (limit?: number, offset?: number): [number, number] => [
  Math.max(1, Math.min(Number(limit || 50), 200)),
  Math.max(0, Number(offset || 0)),
];

function get(table: Table, id: number): Row {
  const r = db.query(`SELECT * FROM ${table} WHERE id=?`).get(id);
  if (!r) throw new NotFound(`${table} ${id}`);
  return r as Row;
}

function create(table: Table, data: Row, extra: Row = {}): Row {
  if (!CHECKS[table](data)) throw new Invalid(table);
  const vals: Row = { ...extra };
  for (const c of COLS[table]) vals[c] = data[c];
  const keys = Object.keys(vals);
  const r = db
    .query(
      `INSERT INTO ${table}(${keys.join(", ")}) VALUES (${keys.map(() => "?").join(", ")})`,
    )
    .run(...(Object.values(vals) as any[]));
  return get(table, Number(r.lastInsertRowid));
}

function update(table: Table, id: number, data: Row): Row {
  if (!CHECKS[table](data)) throw new Invalid(table);
  const sets = COLS[table].map((c) => `${c}=?`).join(", ");
  const r = db
    .query(`UPDATE ${table} SET ${sets} WHERE id=?`)
    .run(...COLS[table].map((c) => data[c]), id);
  if (r.changes === 0) throw new NotFound(`${table} ${id}`);
  return get(table, id);
}

function remove(table: Table, id: number): void {
  if (db.query(`DELETE FROM ${table} WHERE id=?`).run(id).changes === 0)
    throw new NotFound(`${table} ${id}`);
}

function list(table: Table, limit?: number, offset?: number): Row[] {
  const [l, o] = page(limit, offset);
  return db
    .query(`SELECT * FROM ${table} ORDER BY id LIMIT ? OFFSET ?`)
    .all(l, o) as Row[];
}

// Users
export const createUser = (name: string, age: number) =>
  create("users", { name, age });
export const getUser = (id: number) => get("users", id);
export const listUsers = (limit?: number, offset?: number) =>
  list("users", limit, offset);
export const updateUser = (id: number, name: string, age: number) =>
  update("users", id, { name, age });
export const deleteUser = (id: number) => remove("users", id);

// Songs
export const createSong = (name: string, artist: string) =>
  create("songs", { name, artist });
export const getSong = (id: number) => get("songs", id);
export const listSongs = (limit?: number, offset?: number) =>
  list("songs", limit, offset);
export const updateSong = (id: number, name: string, artist: string) =>
  update("songs", id, { name, artist });
export const deleteSong = (id: number) => remove("songs", id);

// Playlists
export function createPlaylist(user_id: number, name: string) {
  get("users", user_id);
  return create("playlists", { name }, { user_id });
}
export const getPlaylist = (id: number) => get("playlists", id);
export function listPlaylists(
  user_id: number,
  limit?: number,
  offset?: number,
) {
  get("users", user_id);
  const [l, o] = page(limit, offset);
  return db
    .query(
      "SELECT * FROM playlists WHERE user_id=? ORDER BY id LIMIT ? OFFSET ?",
    )
    .all(user_id, l, o) as Row[];
}
export const updatePlaylist = (id: number, name: string) =>
  update("playlists", id, { name });
export const deletePlaylist = (id: number) => remove("playlists", id);

// Association
export function addSong(playlist_id: number, song_id: number) {
  get("playlists", playlist_id);
  get("songs", song_id);
  db.query(
    "INSERT OR IGNORE INTO playlist_songs(playlist_id, song_id) VALUES (?, ?)",
  ).run(playlist_id, song_id);
}
export function removeSong(playlist_id: number, song_id: number) {
  const r = db
    .query("DELETE FROM playlist_songs WHERE playlist_id=? AND song_id=?")
    .run(playlist_id, song_id);
  if (r.changes === 0) throw new NotFound("link");
}
export function listPlaylistSongs(
  playlist_id: number,
  limit?: number,
  offset?: number,
) {
  get("playlists", playlist_id);
  const [l, o] = page(limit, offset);
  return db
    .query(
      `SELECT s.* FROM songs s JOIN playlist_songs ps ON ps.song_id = s.id
            WHERE ps.playlist_id=? ORDER BY s.id LIMIT ? OFFSET ?`,
    )
    .all(playlist_id, l, o) as Row[];
}
