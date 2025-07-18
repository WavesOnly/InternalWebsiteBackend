import requests
from requests import Response

from src.utils.spotify.client import SpotifyApiClient
from src.utils.youtube.client import youtube
from src.database.mongo import mongo
from src.models.user import User


session = requests.Session()


class SpotifyHandler:
    def __init__(self, user: User):
        self.user = user
        self.spotify = SpotifyApiClient(user=user)

    def refresh(self, response: Response, *args, **kwargs) -> object:
        if response.status_code == 401:
            token = self.spotify.fetch()
            session.headers.update({"Authorization": f"Bearer {token}"})
            response.request.headers["Authorization"] = session.headers["Authorization"]
            mongo.update(collection="users", id={"spotifyUserId": self.user.spotifyUserId}, query={"$set": {"spotifyAccessToken": token}})
            return session.send(response.request, verify=True)


class YouTubeHandler:
    def __init__(self):
        pass

    def refresh(self, response: Response, *args, **kwargs) -> object:
        if response.status_code == 401:
            token = youtube.fetch()
            session.headers.update({"Authorization": f"Bearer {token}"})
            response.request.headers["Authorization"] = session.headers["Authorization"]
            return session.send(response.request, verify=True)
