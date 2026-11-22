import * as grpc from "@grpc/grpc-js";
import * as loader from "@grpc/proto-loader";
import { join } from "node:path";
import * as repo from "../common/repo";

const PORT = Number(process.env.PORT ?? 8014);

const here = (import.meta as any).dir ?? (import.meta as any).dirname;
const def = loader.loadSync(join(here, "../../proto/streaming.proto"), {
  keepCase: true, // keep user_id, playlist_id as written in the .proto
  defaults: true, // omitted fields arrive as 0 / "" like in Python
});
const pkg = grpc.loadPackageDefinition(def) as any;

// Wrap a repo call: translate domain errors into gRPC status codes.
const h = (fn: (r: any) => any) => (call: any, cb: any) => {
  try {
    cb(null, fn(call.request));
  } catch (e) {
    if (e instanceof repo.NotFound)
      cb({ code: grpc.status.NOT_FOUND, message: e.message });
    else if (e instanceof repo.Invalid)
      cb({ code: grpc.status.INVALID_ARGUMENT, message: e.message });
    else {
      console.error(e);
      cb({ code: grpc.status.INTERNAL, message: "internal error" });
    }
  }
};
const done = (fn: () => void) => (fn(), {});
const items = (rows: any[]) => ({ items: rows });

const handlers = {
  CreateUser: h((r) => repo.createUser(r.name, r.age)),
  GetUser: h((r) => repo.getUser(r.id)),
  ListUsers: h((r) => items(repo.listUsers(r.limit, r.offset))),
  UpdateUser: h((r) => repo.updateUser(r.id, r.name, r.age)),
  DeleteUser: h((r) => done(() => repo.deleteUser(r.id))),

  CreateSong: h((r) => repo.createSong(r.name, r.artist)),
  GetSong: h((r) => repo.getSong(r.id)),
  ListSongs: h((r) => items(repo.listSongs(r.limit, r.offset))),
  UpdateSong: h((r) => repo.updateSong(r.id, r.name, r.artist)),
  DeleteSong: h((r) => done(() => repo.deleteSong(r.id))),

  CreatePlaylist: h((r) => repo.createPlaylist(r.user_id, r.name)),
  GetPlaylist: h((r) => repo.getPlaylist(r.id)),
  ListPlaylists: h((r) =>
    items(repo.listPlaylists(r.user_id, r.limit, r.offset)),
  ),
  UpdatePlaylist: h((r) => repo.updatePlaylist(r.id, r.name)),
  DeletePlaylist: h((r) => done(() => repo.deletePlaylist(r.id))),

  AddSong: h((r) => done(() => repo.addSong(r.playlist_id, r.song_id))),
  RemoveSong: h((r) => done(() => repo.removeSong(r.playlist_id, r.song_id))),
  ListPlaylistSongs: h((r) =>
    items(repo.listPlaylistSongs(r.playlist_id, r.limit, r.offset)),
  ),
};

const server = new grpc.Server();
server.addService(pkg.streaming.Streaming.service, handlers);
server.bindAsync(
  `0.0.0.0:${PORT}`,
  grpc.ServerCredentials.createInsecure(),
  (err) => {
    if (err) throw err;
    console.log(`Bun gRPC listening on :${PORT}`);
  },
);
