import strawberry
from fastapi import FastAPI
from graphql import GraphQLError
from strawberry.fastapi import GraphQLRouter

from common import repo


@strawberry.type
class User:
    id: int
    name: str
    age: int


@strawberry.type
class Song:
    id: int
    name: str
    artist: str


@strawberry.type
class Playlist:
    id: int
    name: str
    user_id: int  # exposed as userId (Strawberry camelCases automatically)


def run(fn, *args):
    try:
        return fn(*args)
    except repo.NotFound as e:
        raise GraphQLError(str(e), extensions={"code": "NOT_FOUND"})
    except repo.Invalid as e:
        raise GraphQLError(str(e), extensions={"code": "BAD_USER_INPUT"})


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: int) -> User:
        return User(**run(repo.get_user, id))

    @strawberry.field
    def users(self, limit: int = 50, offset: int = 0) -> list[User]:
        return [User(**r) for r in run(repo.list_users, limit, offset)]

    @strawberry.field
    def song(self, id: int) -> Song:
        return Song(**run(repo.get_song, id))

    @strawberry.field
    def songs(self, limit: int = 50, offset: int = 0) -> list[Song]:
        return [Song(**r) for r in run(repo.list_songs, limit, offset)]

    @strawberry.field
    def playlist(self, id: int) -> Playlist:
        return Playlist(**run(repo.get_playlist, id))

    @strawberry.field
    def playlists(self, user_id: int, limit: int = 50, offset: int = 0) -> list[Playlist]:
        return [Playlist(**r) for r in run(repo.list_playlists, user_id, limit, offset)]

    @strawberry.field
    def playlist_songs(self, playlist_id: int, limit: int = 50, offset: int = 0) -> list[Song]:
        return [Song(**r) for r in run(repo.list_playlist_songs, playlist_id, limit, offset)]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str, age: int) -> User:
        return User(**run(repo.create_user, name, age))

    @strawberry.mutation
    def update_user(self, id: int, name: str, age: int) -> User:
        return User(**run(repo.update_user, id, name, age))

    @strawberry.mutation
    def delete_user(self, id: int) -> bool:
        run(repo.delete_user, id)
        return True

    @strawberry.mutation
    def create_song(self, name: str, artist: str) -> Song:
        return Song(**run(repo.create_song, name, artist))

    @strawberry.mutation
    def update_song(self, id: int, name: str, artist: str) -> Song:
        return Song(**run(repo.update_song, id, name, artist))

    @strawberry.mutation
    def delete_song(self, id: int) -> bool:
        run(repo.delete_song, id)
        return True

    @strawberry.mutation
    def create_playlist(self, user_id: int, name: str) -> Playlist:
        return Playlist(**run(repo.create_playlist, user_id, name))

    @strawberry.mutation
    def update_playlist(self, id: int, name: str) -> Playlist:
        return Playlist(**run(repo.update_playlist, id, name))

    @strawberry.mutation
    def delete_playlist(self, id: int) -> bool:
        run(repo.delete_playlist, id)
        return True

    @strawberry.mutation
    def add_song(self, playlist_id: int, song_id: int) -> bool:
        run(repo.add_song, playlist_id, song_id)
        return True

    @strawberry.mutation
    def remove_song(self, playlist_id: int, song_id: int) -> bool:
        run(repo.remove_song, playlist_id, song_id)
        return True


schema = strawberry.Schema(Query, Mutation)
app = FastAPI()
app.include_router(GraphQLRouter(schema), prefix="/graphql")