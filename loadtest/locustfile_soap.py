import re

from locust import HttpUser, task
from locust.exception import RescheduleTask

from common import Client, read_mix, write_cycle

NS = "streaming.soap"
HEADERS = {"Content-Type": "text/xml; charset=utf-8"}
ID_RE = re.compile(r"<(?:\w+:)?id>(\d+)</")


def envelope(op, **params):
    body = "".join(f"<s:{k}>{v}</s:{k}>" for k, v in params.items())
    return (
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        f'xmlns:s="{NS}"><soapenv:Body><s:{op}>{body}</s:{op}></soapenv:Body>'
        "</soapenv:Envelope>"
    )


class SoapClient(Client):
    def __init__(self, http):
        self.http = http

    def _call(self, op, **params):
        with self.http.post("/", data=envelope(op, **params), headers=HEADERS,
                            name=f"SOAP {op}", catch_response=True) as r:
            if r.status_code != 200:
                m = re.search(r"<faultstring>(.*?)</faultstring>", r.text, re.S)
                r.failure(f"{r.status_code}: {m.group(1)[:120] if m else r.text[:120]}")
            return r

    def _new_id(self, r):
        m = ID_RE.search(r.text)
        if not m:
            raise RescheduleTask()  # the call already failed and was recorded
        return int(m.group(1))

    def create_user(self, name, age):
        return self._new_id(self._call("CreateUser", name=name, age=age))

    def get_user(self, id):
        self._call("GetUser", id=id)

    def list_users(self, limit, offset):
        self._call("ListUsers", limit=limit, offset=offset)

    def delete_user(self, id):
        self._call("DeleteUser", id=id)

    def get_song(self, id):
        self._call("GetSong", id=id)

    def list_songs(self, limit, offset):
        self._call("ListSongs", limit=limit, offset=offset)

    def create_playlist(self, user_id, name):
        return self._new_id(self._call("CreatePlaylist", user_id=user_id, name=name))

    def update_playlist(self, id, name):
        self._call("UpdatePlaylist", id=id, name=name)

    def delete_playlist(self, id):
        self._call("DeletePlaylist", id=id)

    def add_song(self, playlist_id, song_id):
        self._call("AddSong", playlist_id=playlist_id, song_id=song_id)

    def remove_song(self, playlist_id, song_id):
        self._call("RemoveSong", playlist_id=playlist_id, song_id=song_id)

    def list_playlist_songs(self, playlist_id):
        self._call("ListPlaylistSongs", playlist_id=playlist_id, limit=50, offset=0)


class StreamingUser(HttpUser):
    def on_start(self):
        self.api = SoapClient(self.client)

    @task(8)
    def reads(self):
        read_mix(self.api)

    @task(2)
    def writes(self):
        write_cycle(self.api)