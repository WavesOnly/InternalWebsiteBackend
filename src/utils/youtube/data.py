import json
import os

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

    def upload(self, path: str, title: str, description: str):
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
        if not location:
            raise Exception("Upload failed")
        size = 50 * 1024 * 1024
        with open(path, "rb") as video:
            while True:
                chunk = video.read(size)
                if not chunk:
                    break
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Range": f"bytes {video.tell() - len(chunk)}-{video.tell() - 1}/{os.path.getsize(path)}",
                    "Content-Type": "video/*",
                }
                response = self.session.put(location, headers=headers, data=chunk)
                if response.status_code != 200 and response.status_code != 201:
                    raise Exception(f"Upload failed with status code {response.status_code}")

        return response.json()

    # def upload(self, video: object, title: str, description: str):
    #     url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    #     metadata = {
    #         "snippet": {
    #             "title": title,
    #             "description": description,
    #             "tags": [title, "WavesOnly", "Electronic Music", "EDM", "Music Videos", "Lyric Videos"],
    #             "categoryId": "10",
    #         },
    #         "status": {
    #             "madeForKids": False,
    #             "privacyStatus": "private",
    #             "selfDeclaredMadeForKids": False,
    #         },
    #     }
    #     headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json", "Content-Type": "application/json"}
    #     response = self.session.post(url, headers=headers, data=json.dumps(metadata))
    #     location = response.headers.get("Location")
    #     if not location:
    #         raise Exception("Upload failed")
    #     headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "video/*"}
    #     response = self.session.put(location, headers=headers, data=video)
    #     return response.json()

    def thumbnail(self, videoId: str, path: str):
        url = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
        params = {"videoId": videoId, "uploadType": "media"}
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "image/jpeg"}
        with open(path, "rb") as thumbnail:
            response = self.session.post(url=url, headers=headers, params=params, data=thumbnail)
        return response.json()

    def playlist(self, playlistId: str, videoId: str):
        url = f"{YouTubeApiData.url}/playlistItems?part=snippet"
        data = {"snippet": {"playlistId": playlistId, "resourceId": {"kind": "youtube#video", "videoId": videoId}}}
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        response = self.session.post(url=url, headers=headers, json=data)
        return response.json()

    def rate(self, videoId: str, rating: str = "like") -> None:
        url = f"{YouTubeApiData.url}/videos/rate"
        params = {"id": videoId, "rating": rating}
        response = self.session.post(url=url, headers={"Authorization": f"Bearer {self.token}"}, params=params)
        if response.status_code != 204:
            raise Exception(f"Rating for video {videoId} failed")
