import requests
from dotenv import load_dotenv
from os import environ
from base64 import b64encode, encode, decode


class SpotifyApiClient:
    url = "https://accounts.spotify.com/api/token"

    def __init__(self):
        load_dotenv(".env")
        self.id = environ["SPOTIFY_CLIENT_ID"]
        self.secret = environ["SPOTIFY_CLIENT_SECRET"]
        self.refresh = environ["SPOTIFY_REFRESH_TOKEN"]
        self.token = self.fetch()

    def fetch(self) -> str:
        authorization = f"Basic {b64encode(f'{self.id}:{self.secret}'.encode()).decode('ascii')}"
        headers = {"Authorization": authorization, "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "refresh_token", "refresh_token": self.refresh, "client_id": self.id}
        response = requests.post(url=SpotifyApiClient.url, headers=headers, data=data).json()
        self.token = response["access_token"]
        return self.token


spotify = SpotifyApiClient()
