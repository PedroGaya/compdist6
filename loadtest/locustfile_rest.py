from locust import HttpUser, task

from common import Client, read_mix, write_cycle


class RestClient(Client):
    def __init__(self, http):
        self.http = http
    
    def create_user(self, name, age):
        return self.http.post("/users", json={"name": name, "age": age},
                              name="POST /users").json()["id"]

    def get_user(self, id):
        self.http.get(f"/users/{id}", name="GET /users/{id}")

    def list_users(self, limit, offset):
        self.http.get("/users", params={"limit": limit, "offset": offset},
                      name="GET /users")

    def delete_user(self, id):
        self.http.delete(f"/users/{id}", name="DELETE /users/{id}")

    def get_song(self, id):
        self.http.get(f"/songs/{id}", name="GET /songs/{id}")

    def list_songs(self, limit, offset):
        self.http.get("/songs", params={"limit": limit, "offset": offset},
                      name="GET /songs")

    def create_playlist(self, user_id, name):
        return self.http.post(f"/users/{user_id}/playlists", json={"name": name},
                              name="POST /users/{id}/playlists").json()["id"]

    def update_playlist(self, id, name):
        self.http.put(f"/playlists/{id}", json={"name": name},
                      name="PUT /playlists/{id}")

    def delete_playlist(self, id):
        self.http.delete(f"/playlists/{id}", name="DELETE /playlists/{id}")

    def add_song(self, playlist_id, song_id):
        self.http.put(f"/playlists/{playlist_id}/songs/{song_id}",
                      name="PUT /playlists/{id}/songs/{id}")

    def remove_song(self, playlist_id, song_id):
        self.http.delete(f"/playlists/{playlist_id}/songs/{song_id}",
                         name="DELETE /playlists/{id}/songs/{id}")

    def list_playlist_songs(self, playlist_id):
        self.http.get(f"/playlists/{playlist_id}/songs",
                      name="GET /playlists/{id}/songs")


class StreamingUser(HttpUser):
    def on_start(self):
        self.api = RestClient(self.client)

    @task(8)
    def reads(self):
        read_mix(self.api)

    @task(2)
    def writes(self):
        write_cycle(self.api)