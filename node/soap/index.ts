import http from "node:http";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import * as soap from "soap";
import * as repo from "../common/repo";

const PORT = Number(process.env.PORT ?? 8012);
const xml = readFileSync(
  join(import.meta.dir, "../../schemas/streaming.wsdl"),
  "utf8",
);

// Service/port names come from the WSDL, so we don't hardcode Spyne's naming.
const svcName = xml.match(/<(?:\w+:)?service\s+name="([^"]+)"/)![1];
const portName = xml.match(/<(?:\w+:)?port\s+name="([^"]+)"/)![1];

// Args arrive as strings (or undefined for omitted optional elements).
const n = (v: any) =>
  v === undefined || v === null || v === "" ? undefined : Number(v);
const s = (v: any) => (v === undefined || v === null ? undefined : String(v));

// Run a repo call, translating domain errors into SOAP faults (same codes as Spyne).
function call<T>(fn: () => T): T {
  try {
    return fn();
  } catch (e) {
    if (e instanceof repo.NotFound)
      throw {
        Fault: {
          faultcode: "Client.NotFound",
          faultstring: e.message,
          statusCode: 500,
        },
      };
    if (e instanceof repo.Invalid)
      throw {
        Fault: {
          faultcode: "Client.Invalid",
          faultstring: e.message,
          statusCode: 500,
        },
      };
    throw e;
  }
}

const ops = {
  // Users
  CreateUser: (a: any) => ({
    CreateUserResult: call(() => repo.createUser(s(a.name)!, n(a.age)!)),
  }),
  GetUser: (a: any) => ({ GetUserResult: call(() => repo.getUser(n(a.id)!)) }),
  ListUsers: (a: any) => ({
    ListUsersResult: {
      User: call(() => repo.listUsers(n(a.limit), n(a.offset))),
    },
  }),
  UpdateUser: (a: any) => ({
    UpdateUserResult: call(() =>
      repo.updateUser(n(a.id)!, s(a.name)!, n(a.age)!),
    ),
  }),
  DeleteUser: (a: any) => (call(() => repo.deleteUser(n(a.id)!)), {}),

  // Songs
  CreateSong: (a: any) => ({
    CreateSongResult: call(() => repo.createSong(s(a.name)!, s(a.artist)!)),
  }),
  GetSong: (a: any) => ({ GetSongResult: call(() => repo.getSong(n(a.id)!)) }),
  ListSongs: (a: any) => ({
    ListSongsResult: {
      Song: call(() => repo.listSongs(n(a.limit), n(a.offset))),
    },
  }),
  UpdateSong: (a: any) => ({
    UpdateSongResult: call(() =>
      repo.updateSong(n(a.id)!, s(a.name)!, s(a.artist)!),
    ),
  }),
  DeleteSong: (a: any) => (call(() => repo.deleteSong(n(a.id)!)), {}),

  // Playlists
  CreatePlaylist: (a: any) => ({
    CreatePlaylistResult: call(() =>
      repo.createPlaylist(n(a.user_id)!, s(a.name)!),
    ),
  }),
  GetPlaylist: (a: any) => ({
    GetPlaylistResult: call(() => repo.getPlaylist(n(a.id)!)),
  }),
  ListPlaylists: (a: any) => ({
    ListPlaylistsResult: {
      Playlist: call(() =>
        repo.listPlaylists(n(a.user_id)!, n(a.limit), n(a.offset)),
      ),
    },
  }),
  UpdatePlaylist: (a: any) => ({
    UpdatePlaylistResult: call(() => repo.updatePlaylist(n(a.id)!, s(a.name)!)),
  }),
  DeletePlaylist: (a: any) => (call(() => repo.deletePlaylist(n(a.id)!)), {}),

  // Association
  AddSong: (a: any) => (
    call(() => repo.addSong(n(a.playlist_id)!, n(a.song_id)!)),
    {}
  ),
  RemoveSong: (a: any) => (
    call(() => repo.removeSong(n(a.playlist_id)!, n(a.song_id)!)),
    {}
  ),
  ListPlaylistSongs: (a: any) => ({
    ListPlaylistSongsResult: {
      Song: call(() =>
        repo.listPlaylistSongs(n(a.playlist_id)!, n(a.limit), n(a.offset)),
      ),
    },
  }),
};

const server = http.createServer((_, res) => res.writeHead(404).end());
soap.listen(server, {
  path: "/",
  services: { [svcName]: { [portName]: ops } },
  xml,
});
server.listen(PORT, () =>
  console.log(`Bun SOAP (${svcName}/${portName}) listening on :${PORT}`),
);
