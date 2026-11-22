import sys
import time
from pathlib import Path

import grpc.experimental.gevent as grpc_gevent
grpc_gevent.init_gevent()  # must run before any channel is created

import grpc
from locust import User, task
from locust.exception import RescheduleTask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python" / "pbuf"))
import streaming_pb2 as pb
import streaming_pb2_grpc as pb_grpc

from common import Client, read_mix, write_cycle


class GrpcClient(Client):
    def __init__(self, env, stub):
        self.env, self.stub = env, stub

    def _call(self, name, req):
        start, resp, exc = time.perf_counter(), None, None
        try:
            resp = getattr(self.stub, name)(req)
        except grpc.RpcError as e:
            exc = e
        self.env.events.request.fire(
            request_type="gRPC", name=name,
            response_time=(time.perf_counter() - start) * 1000,
            response_length=resp.ByteSize() if resp is not None else 0,
            exception=exc, context={},
        )
        return resp

    def _new_id(self, resp):
        if resp is None:
            raise RescheduleTask()  # failure already recorded
        return resp.id

    def create_user(self, name, age):
        return self._new_id(self._call("CreateUser", pb.User(name=name, age=age)))
    def get_user(self, id): self._call("GetUser", pb.Id(id=id))
    def list_users(self, limit, offset): self._call("ListUsers", pb.Page(limit=limit, offset=offset))
    def delete_user(self, id): self._call("DeleteUser", pb.Id(id=id))
    def get_song(self, id): self._call("GetSong", pb.Id(id=id))
    def list_songs(self, limit, offset): self._call("ListSongs", pb.Page(limit=limit, offset=offset))
    def create_playlist(self, user_id, name):
        return self._new_id(self._call("CreatePlaylist", pb.Playlist(user_id=user_id, name=name)))
    def update_playlist(self, id, name): self._call("UpdatePlaylist", pb.Playlist(id=id, name=name))
    def delete_playlist(self, id): self._call("DeletePlaylist", pb.Id(id=id))
    def add_song(self, playlist_id, song_id):
        self._call("AddSong", pb.PlaylistSong(playlist_id=playlist_id, song_id=song_id))
    def remove_song(self, playlist_id, song_id):
        self._call("RemoveSong", pb.PlaylistSong(playlist_id=playlist_id, song_id=song_id))
    def list_playlist_songs(self, playlist_id):
        self._call("ListPlaylistSongs", pb.ListPlaylistSongsRequest(playlist_id=playlist_id, limit=50))


class StreamingUser(User):
    def on_start(self):
        host = self.host.replace("http://", "")  # loadtest.bat passes http://localhost:PORT
        self.channel = grpc.insecure_channel(host)
        self.api = GrpcClient(self.environment, pb_grpc.StreamingStub(self.channel))

    def on_stop(self):
        self.channel.close()

    @task(8)
    def reads(self):
        read_mix(self.api)

    @task(2)
    def writes(self):
        write_cycle(self.api)