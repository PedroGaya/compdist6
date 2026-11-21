import { Database } from "bun:sqlite";
import { join } from "path";

const path =
  process.env.DB_PATH ?? join(import.meta.dir, "../../data/streaming.db");

export const db = new Database(path);
db.exec(`
  PRAGMA journal_mode=WAL;
  PRAGMA synchronous=NORMAL;
  PRAGMA foreign_keys=ON;
  PRAGMA busy_timeout=5000;
`);
