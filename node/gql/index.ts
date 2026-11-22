import { readFileSync } from "node:fs";
import { join } from "node:path";
import { buildSchema, graphql, GraphQLError } from "graphql";
import * as repo from "../common/repo";

const PORT = Number(process.env.PORT ?? 8013);
const schema = buildSchema(
  readFileSync(join(import.meta.dir, "../../schemas/schema.graphql"), "utf8"),
);

function run<T>(fn: () => T): T {
  try {
    return fn();
  } catch (e) {
    if (e instanceof repo.NotFound)
      throw new GraphQLError(e.message, { extensions: { code: "NOT_FOUND" } });
    if (e instanceof repo.Invalid)
      throw new GraphQLError(e.message, {
        extensions: { code: "BAD_USER_INPUT" },
      });
    throw e;
  }
}

const pl = (p: any) => ({ ...p, userId: p.user_id });
const ok = (fn: () => void) => (run(fn), true);

const rootValue = {
  user: (a: any) => run(() => repo.getUser(a.id)),
  users: (a: any) => run(() => repo.listUsers(a.limit, a.offset)),
  song: (a: any) => run(() => repo.getSong(a.id)),
  songs: (a: any) => run(() => repo.listSongs(a.limit, a.offset)),
  playlist: (a: any) => pl(run(() => repo.getPlaylist(a.id))),
  playlists: (a: any) =>
    run(() => repo.listPlaylists(a.userId, a.limit, a.offset)).map(pl),
  playlistSongs: (a: any) =>
    run(() => repo.listPlaylistSongs(a.playlistId, a.limit, a.offset)),

  createUser: (a: any) => run(() => repo.createUser(a.name, a.age)),
  updateUser: (a: any) => run(() => repo.updateUser(a.id, a.name, a.age)),
  deleteUser: (a: any) => ok(() => repo.deleteUser(a.id)),
  createSong: (a: any) => run(() => repo.createSong(a.name, a.artist)),
  updateSong: (a: any) => run(() => repo.updateSong(a.id, a.name, a.artist)),
  deleteSong: (a: any) => ok(() => repo.deleteSong(a.id)),
  createPlaylist: (a: any) =>
    pl(run(() => repo.createPlaylist(a.userId, a.name))),
  updatePlaylist: (a: any) => pl(run(() => repo.updatePlaylist(a.id, a.name))),
  deletePlaylist: (a: any) => ok(() => repo.deletePlaylist(a.id)),
  addSong: (a: any) => ok(() => repo.addSong(a.playlistId, a.songId)),
  removeSong: (a: any) => ok(() => repo.removeSong(a.playlistId, a.songId)),
};

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname !== "/graphql" || req.method !== "POST")
      return new Response("not found", { status: 404 });
    let b: any;
    try {
      b = await req.json();
    } catch {
      return Response.json(
        { errors: [{ message: "invalid JSON" }] },
        { status: 400 },
      );
    }
    const result = await graphql({
      schema,
      source: b.query,
      rootValue,
      variableValues: b.variables,
      operationName: b.operationName,
    });
    return Response.json(result);
  },
});

console.log(`Bun GraphQL listening on :${PORT}/graphql`);
