import * as repo from "../common/repo";

const PORT = Number(process.env.PORT ?? 8011);

const json = (data: unknown, status = 200) => Response.json(data, { status });
const noContent = () => new Response(null, { status: 204 });

async function body(req: Request): Promise<Record<string, any>> {
  try {
    const b = await req.json();
    return b && typeof b === "object" ? b : {};
  } catch {
    return {};
  }
}

// Strict integer parsing: "abc" -> Invalid (400), same as FastAPI's validation.
function int(s: string): number {
  if (!/^-?\d+$/.test(s)) throw new repo.Invalid("bad integer");
  return Number(s);
}

function paging(url: URL): [number, number] {
  const l = url.searchParams.get("limit");
  const o = url.searchParams.get("offset");
  return [l === null ? 50 : int(l), o === null ? 0 : int(o)];
}

type Handler = (
  m: string[],
  req: Request,
  url: URL,
) => Response | Promise<Response>;
const routes: [string, RegExp, Handler][] = [];
const route = (method: string, path: string, h: Handler) =>
  routes.push([
    method,
    new RegExp("^" + path.replace(/:\w+/g, "(\\d+|[^/]+)") + "$"),
    h,
  ]);

// Users
route("POST", "/users", async (_, req) => {
  const b = await body(req);
  return json(repo.createUser(b.name, b.age), 201);
});
route("GET", "/users", (_, __, url) => json(repo.listUsers(...paging(url))));
route("GET", "/users/:id", (m) => json(repo.getUser(int(m[1]))));
route("PUT", "/users/:id", async (m, req) => {
  const b = await body(req);
  return json(repo.updateUser(int(m[1]), b.name, b.age));
});
route("DELETE", "/users/:id", (m) => (repo.deleteUser(int(m[1])), noContent()));

// Songs
route("POST", "/songs", async (_, req) => {
  const b = await body(req);
  return json(repo.createSong(b.name, b.artist), 201);
});
route("GET", "/songs", (_, __, url) => json(repo.listSongs(...paging(url))));
route("GET", "/songs/:id", (m) => json(repo.getSong(int(m[1]))));
route("PUT", "/songs/:id", async (m, req) => {
  const b = await body(req);
  return json(repo.updateSong(int(m[1]), b.name, b.artist));
});
route("DELETE", "/songs/:id", (m) => (repo.deleteSong(int(m[1])), noContent()));

// Playlists
route("POST", "/users/:id/playlists", async (m, req) => {
  const b = await body(req);
  return json(repo.createPlaylist(int(m[1]), b.name), 201);
});
route("GET", "/users/:id/playlists", (m, _, url) =>
  json(repo.listPlaylists(int(m[1]), ...paging(url))),
);
route("GET", "/playlists/:id", (m) => json(repo.getPlaylist(int(m[1]))));
route("PUT", "/playlists/:id", async (m, req) => {
  const b = await body(req);
  return json(repo.updatePlaylist(int(m[1]), b.name));
});
route(
  "DELETE",
  "/playlists/:id",
  (m) => (repo.deletePlaylist(int(m[1])), noContent()),
);

// Association
route(
  "PUT",
  "/playlists/:id/songs/:sid",
  (m) => (repo.addSong(int(m[1]), int(m[2])), noContent()),
);
route(
  "DELETE",
  "/playlists/:id/songs/:sid",
  (m) => (repo.removeSong(int(m[1]), int(m[2])), noContent()),
);
route("GET", "/playlists/:id/songs", (m, _, url) =>
  json(repo.listPlaylistSongs(int(m[1]), ...paging(url))),
);

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    let pathMatched = false;
    try {
      for (const [method, re, h] of routes) {
        const m = url.pathname.match(re);
        if (!m) continue;
        pathMatched = true;
        if (method === req.method) return await h(m, req, url);
      }
      return json(
        { error: pathMatched ? "method not allowed" : "not found" },
        pathMatched ? 405 : 404,
      );
    } catch (e) {
      if (e instanceof repo.NotFound) return json({ error: e.message }, 404);
      if (e instanceof repo.Invalid) return json({ error: e.message }, 400);
      console.error(e);
      return json({ error: "internal error" }, 500);
    }
  },
});

console.log(`Bun REST listening on :${PORT}`);
