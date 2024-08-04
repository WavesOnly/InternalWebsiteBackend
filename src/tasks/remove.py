from src.database.mongo import mongo
from src.utils.spotify.client import spotify
from src.utils.spotify.data import SpotifyApiData
from datetime import datetime, timezone
from pprint import pprint


class RemoveOutdatedSongs:
    def __init__(self):
        self.mongo = mongo
        self.api = SpotifyApiData(token=spotify.token)

    def run(self):
        self._remove()

    def _remove(self):
        today = datetime.now(timezone.utc)
        query = {"dateRemoval": {"$lt": datetime.combine(today, datetime.max.time())}, "playlist.removed": False}
        songs = self.mongo.all(collection="history", query=query, serialize=False)
        for song in songs:
            try:
                self.api.remove(id=song["playlist"]["id"], uri=f"spotify:track:{song['song']['id']}")
                self.mongo.update(
                    collection="history",
                    id={"_id": song["_id"]},
                    query={"$set": {"playlist.removed": True}},
                    upsert=False,
                )
            except:
                continue
