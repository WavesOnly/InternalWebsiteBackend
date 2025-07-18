from src.database.mongo import mongo
from src.utils.spotify.data import SpotifyApiData
from datetime import datetime, timezone
from src.models.user import User


class RemoveOutdatedSongs:
    def __init__(self, user: User):
        self.mongo = mongo
        self.user = user
        self.api = SpotifyApiData(user=user)

    def run(self):
        self._remove()

    def _remove(self):
        today = datetime.now(timezone.utc)
        query = {"dateRemoval": {"$lt": datetime.combine(today, datetime.max.time())}, "playlist.removed": False, "spotifyUserId": self.user.spotifyUserId}
        songs = self.mongo.all(collection="history", query=query, serialize=False)
        for song in songs:
            try:
                self.api.remove(id=song["playlist"]["id"], uri=f"spotify:track:{song['song']['id']}")
                self.mongo.update(
                    collection="history",
                    id={"_id": song["_id"], "spotifyUserId": self.user.spotifyUserId},
                    query={"$set": {"playlist.removed": True}},
                )
            except:
                continue
