from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from common import repo

app = FastAPI()

@app.exception_handler(repo.NotFound)
def _nf(_: Request, e: repo.NotFound):
    return JSONResponse({"error": str(e)}, status_code=404)


@app.exception_handler(repo.Invalid)
def _inv(_: Request, e: repo.Invalid):
    return JSONResponse({"error": str(e)}, status_code=400)


@app.exception_handler(RequestValidationError)
def _val(_: Request, e: RequestValidationError):
    return JSONResponse({"error": "invalid input"}, status_code=400)

# Users
@app.post("/users", status_code=201)
def create_user(b: dict):
    return repo.create_user(b.get("name"), b.get("age"))

@app.get("/users")
def list_users(limit: int = 50, offset: int = 0):
    return repo.list_users(limit, offset)

@app.get("/users/{id}")
def get_user(id: int):
    return repo.get_user(id)

@app.put("/users/{id}")
def update_user(id: int, b: dict):
    return repo.update_user(id, b.get("name"), b.get("age"))

@app.delete("/users/{id}", status_code=204)
def delete_user(id: int):
    repo.delete_user(id)
    return Response(status_code=204)


# Songs
@app.post("/songs", status_code=201)
def create_song(b: dict):
    return repo.create_song(b.get("name"), b.get("artist"))

@app.get("/songs")
def list_songs(limit: int = 50, offset: int = 0):
    return repo.list_songs(limit, offset)

@app.get("/songs/{id}")
def get_song(id: int):
    return repo.get_song(id)

@app.put("/songs/{id}")
def update_song(id: int, b: dict):
    return repo.update_song(id, b.get("name"), b.get("artist"))

@app.delete("/songs/{id}", status_code=204)
def delete_song(id: int):
    repo.delete_song(id)
    return Response(status_code=204)


# Playlists
@app.post("/users/{user_id}/playlists", status_code=201)
def create_playlist(user_id: int, b: dict):
    return repo.create_playlist(user_id, b.get("name"))

@app.get("/users/{user_id}/playlists")
def list_playlists(user_id: int, limit: int = 50, offset: int = 0):
    return repo.list_playlists(user_id, limit, offset)

@app.get("/playlists/{id}")
def get_playlist(id: int):
    return repo.get_playlist(id)

@app.put("/playlists/{id}")
def update_playlist(id: int, b: dict):
    return repo.update_playlist(id, b.get("name"))

@app.delete("/playlists/{id}", status_code=204)
def delete_playlist(id: int):
    repo.delete_playlist(id)
    return Response(status_code=204)


# Association
@app.put("/playlists/{id}/songs/{song_id}", status_code=204)
def add_song(id: int, song_id: int):
    repo.add_song(id, song_id)
    return Response(status_code=204)

@app.delete("/playlists/{id}/songs/{song_id}", status_code=204)
def remove_song(id: int, song_id: int):
    repo.remove_song(id, song_id)
    return Response(status_code=204)

@app.get("/playlists/{id}/songs")
def list_playlist_songs(id: int, limit: int = 50, offset: int = 0):
    return repo.list_playlist_songs(id, limit, offset)