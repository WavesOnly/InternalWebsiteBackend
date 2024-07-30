import requests
from requests import Response

from src.utils.spotify.client import spotify
from src.utils.youtube.client import youtube


session = requests.Session()


class SpotifyHandler:
    def __init__(self):
        pass

    def refresh(self, response: Response, *args, **kwargs) -> object:
        if response.status_code == 401:
            spotify.token = spotify.fetch()
            session.headers.update({"Authorization": f"Bearer {spotify.token}"})
            response.request.headers["Authorization"] = session.headers["Authorization"]
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
