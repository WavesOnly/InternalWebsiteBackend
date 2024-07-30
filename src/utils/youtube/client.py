import requests
from dotenv import load_dotenv
from os import environ
from base64 import b64encode, encode, decode


class YouTubeApiClient:
    url = "https://oauth2.googleapis.com/token"

    def __init__(self):
        load_dotenv(".env")
        self.id = environ["YOUTUBE_CLIENT_ID"]
        self.secret = environ["YOUTUBE_CLIENT_SECRET"]
        self.refresh = environ["YOUTUBE_REFRESH_TOKEN"]
        self.token = self.fetch()

    def fetch(self) -> str:
        data = {"client_id": self.id, "client_secret": self.secret, "refresh_token": self.refresh, "grant_type": "refresh_token"}
        response = requests.post(url=YouTubeApiClient.url, data=data).json()
        self.token = response["access_token"]
        return self.token


youtube = YouTubeApiClient()
