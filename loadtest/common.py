import random

N_USERS, N_SONGS = 100, 1000   # must match db/init.py

class Client:
    """Implemented once per protocol. create_* return the new id."""
    def create_user(self, name, age): raise NotImplementedError
    def get_user(self, id): raise NotImplementedError
    def list_users(self, limit, offset): raise NotImplementedError
    def delete_user(self, id): raise NotImplementedError
    def get_song(self, id): raise NotImplementedError
    def list_songs(self, limit, offset): raise NotImplementedError
    def create_playlist(self, user_id, name): raise NotImplementedError
    def update_playlist(self, id, name): raise NotImplementedError
    def delete_playlist(self, id): raise NotImplementedError
    def add_song(self, playlist_id, song_id): raise NotImplementedError
    def remove_song(self, playlist_id, song_id): raise NotImplementedError
    def list_playlist_songs(self, playlist_id): raise NotImplementedError

def read_mix(c: Client):
    c.get_user(random.randint(1, N_USERS))
    c.get_song(random.randint(1, N_SONGS))
    c.list_songs(20, random.randint(0, N_SONGS - 20))
    c.list_users(20, 0)

def write_cycle(c: Client):
    uid = c.create_user(f"u{random.getrandbits(32)}", random.randint(15, 80))
    pid = c.create_playlist(uid, "mix")
    songs = random.sample(range(1, N_SONGS + 1), 3)
    for s in songs:
        c.add_song(pid, s)
    c.list_playlist_songs(pid)
    c.update_playlist(pid, "mix v2")
    c.remove_song(pid, songs[0])
    c.delete_playlist(pid)
    c.delete_user(uid)

# Task weights used by every locustfile: read_mix x8, write_cycle x2