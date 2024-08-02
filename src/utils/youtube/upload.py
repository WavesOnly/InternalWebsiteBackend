from tempfile import TemporaryDirectory
from os import remove

from src.utils.youtube.client import youtube
from src.utils.youtube.data import YouTubeApiData
from src.utils.screenshot import Screenshot


class Upload:
    def __init__(self):
        self.api = YouTubeApiData(token=youtube.token)
        self.screenshot = Screenshot()

    def orchestrate(self, path: str, title: str, description: str, playlists: list[str]):
        try:
            upload = self.api.upload(path=path, title=title, description=description)
        except Exception as e:
            print(e)
        try:
            with TemporaryDirectory() as directory:
                with open(path, "rb") as video:
                    thumbnail = self.screenshot.capture(video=video.read())
                location = self.screenshot.save(frame=thumbnail, directory=directory)
                self.api.thumbnail(videoId=upload["id"], path=location)
        except Exception as e:
            print(e)
        try:
            for playlistId in playlists:
                self.api.playlist(playlistId=playlistId, videoId=upload["id"])
        except Exception as e:
            print(e)
        try:
            self.api.rate(videoId=upload["id"])
        except Exception as e:
            print(e)
        finally:
            remove(path)
