from locust import HttpUser, task
from locust.exception import RescheduleTask

from common import Client, read_mix, write_cycle

Q = {
    "createUser": "mutation($name:String!,$age:Int!){createUser(name:$name,age:$age){id name age}}",
    "getUser": "query($id:Int!){user(id:$id){id name age}}",
    "listUsers": "query($limit:Int,$offset:Int){users(limit:$limit,offset:$offset){id name age}}",
    "deleteUser": "mutation($id:Int!){deleteUser(id:$id)}",
    "getSong": "query($id:Int!){song(id:$id){id name artist}}",
    "listSongs": "query($limit:Int,$offset:Int){songs(limit:$limit,offset:$offset){id name artist}}",
    "createPlaylist": "mutation($userId:Int!,$name:String!){createPlaylist(userId:$userId,name:$name){id name userId}}",
    "updatePlaylist": "mutation($id:Int!,$name:String!){updatePlaylist(id:$id,name:$name){id name userId}}",
    "deletePlaylist": "mutation($id:Int!){deletePlaylist(id:$id)}",
    "addSong": "mutation($playlistId:Int!,$songId:Int!){addSong(playlistId:$playlistId,songId:$songId)}",
    "removeSong": "mutation($playlistId:Int!,$songId:Int!){removeSong(playlistId:$playlistId,songId:$songId)}",
    "listPlaylistSongs": "query($playlistId:Int!,$limit:Int,$offset:Int){playlistSongs(playlistId:$playlistId,limit:$limit,offset:$offset){id name artist}}",
}


class GqlClient(Client):
    def __init__(self, http):
        self.http = http

    def _call(self, op, **variables):
        with self.http.post("/graphql", json={"query": Q[op], "variables": variables},
                            name=f"GQL {op}", catch_response=True) as r:
            try:
                body = r.json()
            except Exception:
                r.failure(f"{r.status_code}: not JSON")
                return None
            if r.status_code != 200 or body.get("errors"):
                err = (body.get("errors") or [{}])[0]
                r.failure(f"{r.status_code}: {str(err.get('message'))[:120]}")
                return None
            return body["data"]

    def _id(self, data, field):
        if data is None:
            raise RescheduleTask()  # failure already recorded
        return data[field]["id"]

    def create_user(self, name, age):
        return self._id(self._call("createUser", name=name, age=age), "createUser")

    def get_user(self, id): self._call("getUser", id=id)
    def list_users(self, limit, offset): self._call("listUsers", limit=limit, offset=offset)
    def delete_user(self, id): self._call("deleteUser", id=id)
    def get_song(self, id): self._call("getSong", id=id)
    def list_songs(self, limit, offset): self._call("listSongs", limit=limit, offset=offset)

    def create_playlist(self, user_id, name):
        return self._id(self._call("createPlaylist", userId=user_id, name=name), "createPlaylist")

    def update_playlist(self, id, name): self._call("updatePlaylist", id=id, name=name)
    def delete_playlist(self, id): self._call("deletePlaylist", id=id)
    def add_song(self, playlist_id, song_id):
        self._call("addSong", playlistId=playlist_id, songId=song_id)
    def remove_song(self, playlist_id, song_id):
        self._call("removeSong", playlistId=playlist_id, songId=song_id)
    def list_playlist_songs(self, playlist_id):
        self._call("listPlaylistSongs", playlistId=playlist_id, limit=50, offset=0)


class StreamingUser(HttpUser):
    def on_start(self):
        self.api = GqlClient(self.client)

    @task(8)
    def reads(self):
        read_mix(self.api)

    @task(2)
    def writes(self):
        write_cycle(self.api)