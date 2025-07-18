from src.database.mongo import mongo
from src.utils.spotify.data import SpotifyApiData
from datetime import datetime, timezone
from src.models.user import User


class UpdateSpotifyData:
    def __init__(self, user: User):
        self.mongo = mongo
        self.user = user
        self.api = SpotifyApiData(user=user)

    def run(self):
        self._account()
        self._playlists()

    def _playlists(self):
        playlists = self.api.playlists(user_id=self.user.spotifyUserId)["items"]
        playlists = [{"id": playlist["id"]} for playlist in playlists if (playlist["owner"]["id"] == self.user.spotifyUserId and playlist["public"] == True)]
        for playlist in playlists:
            data = self.api.playlist(id=playlist["id"])
            followers = data["followers"]["total"]
            date = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
            exists = self.mongo.one(collection="spotifyPlaylists", query={"playlistId": playlist["id"], "spotifyUserId": self.user.spotifyUserId, "followerHistory.date": date})
            if exists:
                self.mongo.update(
                    collection="spotifyPlaylists", 
                    id={"playlistId": playlist["id"], "spotifyUserId": self.user.spotifyUserId},
                    query={"$set": {"followers": followers}}
                )
                self.mongo.update(
                    collection="spotifyPlaylists", 
                    id={"playlistId": playlist["id"], "spotifyUserId": self.user.spotifyUserId, "followerHistory.date": date},
                    query={"$set": {"followerHistory.$.followers": followers}}
                )
            else:
                self.mongo.update(
                    collection="spotifyPlaylists",
                    id={"playlistId": playlist["id"], "spotifyUserId": self.user.spotifyUserId},
                    query={
                        "$set": {"followers": followers},
                        "$push": {"followerHistory": {"date": date, "followers": followers}},
                    },
                    upsert=True,
                )
            document = self.mongo.one(collection="spotifyPlaylists", query={"playlistId": playlist["id"]})
            growth = self._average(history=document["followerHistory"])
            items = self.api.items(id=playlist["id"])
            for item in items["items"]:
                item["added_at"] = datetime.strptime(item["added_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            updated = max(items["items"], key=lambda x: x["added_at"])["added_at"]
            self.mongo.update(
                collection="spotifyPlaylists",
                id={"playlistId": playlist["id"], "spotifyUserId": self.user.spotifyUserId},
                query={"$set": {"averageGrowth": growth, "lastUpdated": updated}},
            )

    def _account(self):
        user = self.api.user(id=self.user.spotifyUserId)
        followers = user["followers"]["total"]
        date = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
        exists = self.mongo.one(collection="users", query={"spotifyUserId": self.user.spotifyUserId, "followerHistory.date": date})
        if exists:
            self.mongo.update(
                collection="users", 
                id={"spotifyUserId": self.user.spotifyUserId},
                query={"$set": {"followers": followers}}
            )
            self.mongo.update(
                collection="users", 
                id={"spotifyUserId": self.user.spotifyUserId, "followerHistory.date": date},
                query={"$set": {"followerHistory.$.followers": followers}}
            )
        else:
            self.mongo.update(
                collection="users",
                id={"spotifyUserId": user["id"]},
                query={
                    "$set": {"followers": followers},
                    "$push": {"followerHistory": {"date": date, "followers": followers}},
                },
            )
        document = self.mongo.one(collection="users", query={"spotifyUserId": self.user.spotifyUserId})
        growth = self._average(history=document["followerHistory"])
        self.mongo.update(
            collection="users",
            id={"spotifyUserId": self.user.spotifyUserId},
            query={"$set": {"averageGrowth": growth}},
        )

    def _average(self, history: list[dict]) -> int:
        if not history or len(history) < 2:
            return 0.0
        counts = [item["followers"] for item in history]
        changes = [counts[i] - counts[i - 1] for i in range(1, len(counts))]
        return sum(changes) / len(changes)
