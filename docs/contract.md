# Contract

IDs are integers. Updates are full replacements (all fields required).
Lists take `limit` (default 50, clamped to 1..200) and `offset` (default 0).

## Entities

- User: `id, name (non-empty), age (int 0..150)`
- Song: `id, name (non-empty), artist (non-empty)`
- Playlist: `id, name (non-empty), user_id`

## Operations

| Operation                      | REST                                           | gRPC / SOAP / GraphQL name                        |
| ------------------------------ | ---------------------------------------------- | ------------------------------------------------- |
| Create user                    | `POST /users` -> 201                           | `CreateUser` / `createUser`                       |
| Get user                       | `GET /users/{id}`                              | `GetUser`                                         |
| List users                     | `GET /users?limit&offset`                      | `ListUsers`                                       |
| Update user                    | `PUT /users/{id}`                              | `UpdateUser`                                      |
| Delete user                    | `DELETE /users/{id}` -> 204                    | `DeleteUser`                                      |
| Songs (5 ops)                  | same shape under `/songs`                      | `CreateSong` ... `DeleteSong`                     |
| Create playlist                | `POST /users/{userId}/playlists` -> 201        | `CreatePlaylist(user_id, name)`                   |
| List playlists of user         | `GET /users/{userId}/playlists`                | `ListPlaylists(user_id)`                          |
| Get / Update / Delete playlist | `GET/PUT/DELETE /playlists/{id}`               | `GetPlaylist`, `UpdatePlaylist`, `DeletePlaylist` |
| Add song to playlist           | `PUT /playlists/{id}/songs/{songId}` -> 204    | `AddSong`                                         |
| Remove song from playlist      | `DELETE /playlists/{id}/songs/{songId}` -> 204 | `RemoveSong`                                      |
| List songs of playlist         | `GET /playlists/{id}/songs`                    | `ListPlaylistSongs`                               |

18 operations in total.

## Semantics

- Deleting a user cascades to their playlists. Deleting a playlist or song cascades to the links.
- `AddSong` is idempotent (adding an existing link is not an error).
- `RemoveSong` on a missing link is NotFound.
- Creating or listing playlists for a missing user is NotFound.

## Errors

| Case          | REST | gRPC               | GraphQL `extensions.code` | SOAP Fault code   |
| ------------- | ---- | ------------------ | ------------------------- | ----------------- |
| NotFound      | 404  | `NOT_FOUND`        | `NOT_FOUND`               | `Client.NotFound` |
| Invalid input | 400  | `INVALID_ARGUMENT` | `BAD_USER_INPUT`          | `Client.Invalid`  |
