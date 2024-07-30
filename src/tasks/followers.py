from src.database.mongo import mongo
from src.utils.spotify.client import spotify
from src.utils.spotify.data import SpotifyApiData
from datetime import datetime, timezone


class UpdateSpotifyData:
    def __init__(self):
        self.mongo = mongo
        self.api = SpotifyApiData(token=spotify.token)

    def run(self):
        self._playlists()
        self._account()

    def _playlists(self):
        playlists = self.api.playlists()["items"]
        playlists = [{"id": playlist["id"]} for playlist in playlists if playlist["owner"]["id"] == "w5sxze6rmcbs22r6w22ks8zme"]
        for playlist in playlists:
            data = self.api.playlist(id=playlist["id"])
            followers = data["followers"]["total"]
            date = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
            self.mongo.update(
                collection="spotifyPlaylists",
                id={"playlistId": playlist["id"]},
                query={
                    "$set": {"followers": followers},
                    "$push": {"followerHistory": {"date": date, "followers": followers}},
                },
                upsert=True,
            )

    def _account(self):
        user = self.api.user()
        followers = user["followers"]["total"]
        date = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
        self.mongo.update(
            collection="spotifyAccount",
            id={"userId": user["id"]},
            query={
                "$set": {"followers": followers},
                "$push": {"followerHistory": {"date": date, "followers": followers}},
            },
            upsert=True,
        )
