from soap import compat  # noqa: F401
from spyne import Application, ServiceBase, rpc, Fault
from spyne.model.complex import ComplexModel, Array
from spyne.model.primitive import Integer32, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from common import repo

NS = "streaming.soap"


class User(ComplexModel): # type: ignore
    __namespace__ = NS
    id = Integer32
    name = Unicode
    age = Integer32


class Song(ComplexModel): # type: ignore
    __namespace__ = NS
    id = Integer32
    name = Unicode
    artist = Unicode


class Playlist(ComplexModel): # type: ignore
    __namespace__ = NS
    id = Integer32
    name = Unicode
    user_id = Integer32


def call(fn, *args):
    """Run a repo function, translating domain errors into SOAP faults."""
    try:
        return fn(*args)
    except repo.NotFound as e:
        raise Fault(faultcode="Client.NotFound", faultstring=str(e))
    except repo.Invalid as e:
        raise Fault(faultcode="Client.Invalid", faultstring=str(e))


class StreamingService(ServiceBase):
    # Users
    @rpc(Unicode, Integer32, _returns=User)
    def CreateUser(ctx, name, age):
        return User(**call(repo.create_user, name, age))

    @rpc(Integer32, _returns=User)
    def GetUser(ctx, id):
        return User(**call(repo.get_user, id))

    @rpc(Integer32(default=50), Integer32(default=0), _returns=Array(User))
    def ListUsers(ctx, limit, offset):
        return [User(**r) for r in call(repo.list_users, limit, offset)]

    @rpc(Integer32, Unicode, Integer32, _returns=User)
    def UpdateUser(ctx, id, name, age):
        return User(**call(repo.update_user, id, name, age))

    @rpc(Integer32)
    def DeleteUser(ctx, id):
        call(repo.delete_user, id)

    # Songs
    @rpc(Unicode, Unicode, _returns=Song)
    def CreateSong(ctx, name, artist):
        return Song(**call(repo.create_song, name, artist))

    @rpc(Integer32, _returns=Song)
    def GetSong(ctx, id):
        return Song(**call(repo.get_song, id))

    @rpc(Integer32(default=50), Integer32(default=0), _returns=Array(Song))
    def ListSongs(ctx, limit, offset):
        return [Song(**r) for r in call(repo.list_songs, limit, offset)]

    @rpc(Integer32, Unicode, Unicode, _returns=Song)
    def UpdateSong(ctx, id, name, artist):
        return Song(**call(repo.update_song, id, name, artist))

    @rpc(Integer32)
    def DeleteSong(ctx, id):
        call(repo.delete_song, id)

    # Playlists
    @rpc(Integer32, Unicode, _returns=Playlist)
    def CreatePlaylist(ctx, user_id, name):
        return Playlist(**call(repo.create_playlist, user_id, name))

    @rpc(Integer32, _returns=Playlist)
    def GetPlaylist(ctx, id):
        return Playlist(**call(repo.get_playlist, id))

    @rpc(Integer32, Integer32(default=50), Integer32(default=0), _returns=Array(Playlist))
    def ListPlaylists(ctx, user_id, limit, offset):
        return [Playlist(**r) for r in call(repo.list_playlists, user_id, limit, offset)]

    @rpc(Integer32, Unicode, _returns=Playlist)
    def UpdatePlaylist(ctx, id, name):
        return Playlist(**call(repo.update_playlist, id, name))

    @rpc(Integer32)
    def DeletePlaylist(ctx, id):
        call(repo.delete_playlist, id)

    # Association
    @rpc(Integer32, Integer32)
    def AddSong(ctx, playlist_id, song_id):
        call(repo.add_song, playlist_id, song_id)

    @rpc(Integer32, Integer32)
    def RemoveSong(ctx, playlist_id, song_id):
        call(repo.remove_song, playlist_id, song_id)

    @rpc(Integer32, Integer32(default=50), Integer32(default=0), _returns=Array(Song))
    def ListPlaylistSongs(ctx, playlist_id, limit, offset):
        return [Song(**r) for r in call(repo.list_playlist_songs, playlist_id, limit, offset)]


soap_app = Application(
    [StreamingService],
    tns=NS,
    name="Streaming",
    in_protocol=Soap11(),
    out_protocol=Soap11(),
)

app = WsgiApplication(soap_app) # type: ignore