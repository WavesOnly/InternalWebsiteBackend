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
            document = self.mongo.one(collection="spotifyPlaylists", query={"playlistId": playlist["id"]})
            growth = self._average(history=document["followerHistory"])
            self.mongo.update(
                collection="spotifyPlaylists",
                id={"playlistId": playlist["id"]},
                query={
                    "$set": {"averageGrowth": growth},
                },
                upsert=False,
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

    def _average(self, history: list[dict]) -> int:
        if not history or len(history) < 2:
            return 0.0
        counts = [item["followers"] for item in history]
        changes = [counts[i] - counts[i - 1] for i in range(1, len(counts))]
        return sum(changes) / len(changes)
