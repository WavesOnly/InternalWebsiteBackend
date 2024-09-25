from datetime import datetime, timedelta, timezone
from json import dump

from src.utils.youtube.client import youtube
from src.utils.youtube.data import YouTubeApiData
from src.utils.youtube.analytics import YouTubeApiAnalytics


class YouTube:
    def __init__(self):
        self.data = YouTubeApiData(token=youtube.token)
        self.analytics = YouTubeApiAnalytics(token=youtube.token)

    def run(self):
        self._views()

    def _views(self):
        uploads = self.data.items()
        videos = []
        start = datetime.strptime("2024-01-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        for upload in reversed(uploads):
            date = datetime.strptime(upload["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if start <= date <= (datetime.now(timezone.utc) - timedelta(days=28)):
                videos.append(upload)
        statistics = []
        for video in videos:
            start = datetime.strptime(video["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).date()
            end = start + timedelta(days=14)
            metrics = ["views"]
            filters = {"video": video["snippet"]["resourceId"]["videoId"]}
            views = self.analytics.daily(start=start, end=end, metrics=metrics, filters=filters)
            published = datetime.strptime(video["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            statistics.append(
                {
                    "videoId": video["snippet"]["resourceId"]["videoId"],
                    "title": video["snippet"]["title"],
                    "publishedAt": video["snippet"]["publishedAt"],
                    "publishDate": datetime.combine(published.date(), datetime.min.time(), tzinfo=timezone.utc),
                    "views": sum(int(item[1]) for item in views["rows"]),
                }
            )
        statistics = sorted(statistics, key=lambda x: x["publishDate"])
        for statistic in statistics:
            statistic["publishDate"] = statistic["publishDate"].strftime("%Y-%m-%dT%H:%M:%SZ")
        with open("videoViewsInFirstTwoWeeks.json", "w") as file:
            dump(statistics, file, indent=4)
