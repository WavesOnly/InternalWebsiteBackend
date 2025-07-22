from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from src.utils.spotify.data import SpotifyApiData
from src.database.mongo import mongo
from src.models.user import User


class RefreshOutdatedSongs:
    def __init__(self, user: User):
        self.mongo = mongo
        self.user = user
        self.api = SpotifyApiData(user=user)

    def run(self):
        self._refresh()

    def _refresh(self):
        playlists = self.api.playlists(user_id=self.user.spotifyUserId)["items"]
        playlists = [{"id": playlist["id"]} for playlist in playlists if (playlist["owner"]["id"] == self.user.spotifyUserId and playlist["public"] == True)]
        for playlist in playlists:
            self._update(id=playlist["id"])

    def _update(self, id: str):
        tracks = self.api.items(id=id)
        outdated = {}
        cutoff = (datetime.now(timezone.utc) - relativedelta(months=2)).date()
        for index, track in enumerate(tracks["items"]):
            added = datetime.strptime(track["added_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).date()
            if added <= cutoff:
                outdated[index] = track["track"]["uri"]
        for index in sorted(outdated.keys(), reverse=True):
            uri = outdated[index]
            self.api.remove(id=id, uri=uri)
            self.api.add(id=id, uri=uri, position=index)