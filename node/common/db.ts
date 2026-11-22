import { join } from "node:path";

const dir = (import.meta as any).dir ?? (import.meta as any).dirname;
const path = process.env.DB_PATH ?? join(dir, "../../data/streaming.db");
const PRAGMAS = `
  PRAGMA journal_mode=WAL;
  PRAGMA synchronous=NORMAL;
  PRAGMA foreign_keys=ON;
  PRAGMA busy_timeout=5000;
`;

let impl: { query(sql: string): any };

if (typeof (globalThis as any).Bun !== "undefined") {
  const { Database } = await import("bun:sqlite");
  const d = new Database(path);
  d.exec(PRAGMAS);
  impl = d;
} else {
  const { DatabaseSync } = await import("node:sqlite");
  const d = new DatabaseSync(path);
  d.exec(PRAGMAS);
  const cache = new Map<string, any>();
  impl = {
    query(sql: string) {
      let s = cache.get(sql);
      if (!s) cache.set(sql, (s = d.prepare(sql)));
      return {
        get: (...a: any[]) => s.get(...a) ?? null,
        all: (...a: any[]) => s.all(...a),
        run: (...a: any[]) => s.run(...a), // { changes, lastInsertRowid }
      };
    },
  };
}

export const db = impl;
