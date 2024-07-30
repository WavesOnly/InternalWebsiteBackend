import json

from src.utils.api import session, YouTubeHandler


class YouTubeApiData:
    url = "https://www.googleapis.com/youtube/v3"

    def __init__(self, token: str):
        self.session = session
        self.session.hooks["response"].append(YouTubeHandler().refresh)
        self.token = token

    def channel(self, id: str = "UC9RKqI3GeK_fdHdQyaB5laQ") -> dict:
        url = f"{YouTubeApiData.url}/channels"
        params = {"part": "snippet,statistics", "id": id}
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"}, params=params)
        return response.json()

    def playlists(self, id: str = "UC9RKqI3GeK_fdHdQyaB5laQ") -> dict:
        url = f"{YouTubeApiData.url}/playlists"
        params = {"part": "snippet,contentDetails", "channelId": id, "maxResults": 50}
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"}, params=params)
        return response.json()

    def upload(self, video: object, title: str, description: str):
        url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": [title, "WavesOnly", "Electronic Music", "EDM", "Music Videos", "Lyric Videos"],
                "categoryId": "10",
            },
            "status": {
                "madeForKids": False,
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": False,
            },
        }
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json", "Content-Type": "application/json"}
        response = self.session.post(url, headers=headers, data=json.dumps(metadata))
        location = response.headers.get("Location")
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "video/*"}
        response = self.session.put(location, headers=headers, data=video)
        return response.json()
