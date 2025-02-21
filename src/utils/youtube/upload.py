from tempfile import TemporaryDirectory

from src.utils.youtube.client import youtube
from src.utils.youtube.data import YouTubeApiData
from src.utils.screenshot import Screenshot


class Upload:
    def __init__(self):
        self.api = YouTubeApiData(token=youtube.token)

    def orchestrate(self, video: object, title: str, description: str, playlists: list[str]):
        upload = self.api.upload(video=video, title=title, description=description)
        print("Video uploaded")
        screenshot = Screenshot()
        thumbnail = screenshot.capture(video=video)
        with TemporaryDirectory() as directory:
            path = screenshot.save(frame=thumbnail, directory=directory)
            self.api.thumbnail(videoId=upload["id"], path=path)
            print("Screenshot uploaded")
        for playlistId in playlists:
            self.api.playlist(playlistId=playlistId, videoId=upload["id"])
        self.api.rate(videoId=upload["id"])
        print("Orchestration complete")
