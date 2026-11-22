import os
import sys
from concurrent import futures
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))        # generated stubs use absolute imports
sys.path.insert(0, str(HERE.parent)) # python/ for `common`

import grpc
import streaming_pb2 as pb
import streaming_pb2_grpc as pb_grpc

from common import repo

PORT = int(os.environ.get("PORT", 8004))


def guarded(fn):
    def wrapper(self, req, ctx):
        try:
            return fn(self, req, ctx)
        except repo.NotFound as e:
            ctx.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except repo.Invalid as e:
            ctx.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
    return wrapper


def user(r): return pb.User(**r)
def song(r): return pb.Song(**r)
def playlist(r): return pb.Playlist(**r)


class Service(pb_grpc.StreamingServicer):
    @guarded
    def CreateUser(self, r, ctx): return user(repo.create_user(r.name, r.age))
    @guarded
    def GetUser(self, r, ctx): return user(repo.get_user(r.id))
    @guarded
    def ListUsers(self, r, ctx):
        return pb.UserList(items=[user(x) for x in repo.list_users(r.limit, r.offset)])
    @guarded
    def UpdateUser(self, r, ctx): return user(repo.update_user(r.id, r.name, r.age))
    @guarded
    def DeleteUser(self, r, ctx):
        repo.delete_user(r.id); return pb.Empty()

    @guarded
    def CreateSong(self, r, ctx): return song(repo.create_song(r.name, r.artist))
    @guarded
    def GetSong(self, r, ctx): return song(repo.get_song(r.id))
    @guarded
    def ListSongs(self, r, ctx):
        return pb.SongList(items=[song(x) for x in repo.list_songs(r.limit, r.offset)])
    @guarded
    def UpdateSong(self, r, ctx): return song(repo.update_song(r.id, r.name, r.artist))
    @guarded
    def DeleteSong(self, r, ctx):
        repo.delete_song(r.id); return pb.Empty()

    @guarded
    def CreatePlaylist(self, r, ctx): return playlist(repo.create_playlist(r.user_id, r.name))
    @guarded
    def GetPlaylist(self, r, ctx): return playlist(repo.get_playlist(r.id))
    @guarded
    def ListPlaylists(self, r, ctx):
        rows = repo.list_playlists(r.user_id, r.limit, r.offset)
        return pb.PlaylistList(items=[playlist(x) for x in rows])
    @guarded
    def UpdatePlaylist(self, r, ctx): return playlist(repo.update_playlist(r.id, r.name))
    @guarded
    def DeletePlaylist(self, r, ctx):
        repo.delete_playlist(r.id); return pb.Empty()

    @guarded
    def AddSong(self, r, ctx):
        repo.add_song(r.playlist_id, r.song_id); return pb.Empty()
    @guarded
    def RemoveSong(self, r, ctx):
        repo.remove_song(r.playlist_id, r.song_id); return pb.Empty()
    @guarded
    def ListPlaylistSongs(self, r, ctx):
        rows = repo.list_playlist_songs(r.playlist_id, r.limit, r.offset)
        return pb.SongList(items=[song(x) for x in rows])


server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
pb_grpc.add_StreamingServicer_to_server(Service(), server)
server.add_insecure_port(f"0.0.0.0:{PORT}")
server.start()
print(f"Python gRPC listening on :{PORT}")
server.wait_for_termination()