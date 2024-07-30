from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from src.utils.api import session, YouTubeHandler


class YouTubeApiAnalytics:
    url = "https://youtubeanalytics.googleapis.com/v2"

    def __init__(self, token: str):
        self.session = session
        self.session.hooks["response"].append(YouTubeHandler().refresh)
        self.token = token

    def daily(self, id: str = "UC9RKqI3GeK_fdHdQyaB5laQ") -> dict:
        url = f"{YouTubeApiAnalytics.url}/reports"
        today = datetime.now().date()
        params = {
            "ids": "channel==MINE",
            "startDate": today - timedelta(days=29),
            "endDate": datetime.now().date(),
            "metrics": "views,subscribersGained,estimatedRevenue,estimatedMinutesWatched",
            "dimensions": "day",
            "filters": f"channel=={id}",
            "sort": "day",
        }
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"}, params=params)
        return response.json()

    def monthly(self, id: str = "UC9RKqI3GeK_fdHdQyaB5laQ") -> dict:
        url = f"{YouTubeApiAnalytics.url}/reports"
        today = datetime.now().date()
        params = {
            "ids": "channel==MINE",
            "startDate": (today.replace(day=1) - relativedelta(months=7)).replace(day=1),
            "endDate": (today.replace(day=1) - relativedelta(months=1)).replace(day=1),
            "metrics": "estimatedRevenue",
            "dimensions": "month",
            "filters": f"channel=={id}",
            "sort": "month",
        }
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"}, params=params)
        return response.json()
