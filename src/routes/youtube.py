from fastapi import APIRouter, UploadFile, Depends, File, Form, BackgroundTasks
from typing import Optional
from os.path import splitext
from ntpath import basename
from statistics import mean
from datetime import datetime, timedelta

from src.models.user import User
from src.utils.auth import verify
from src.models.user import User
from src.utils.youtube.client import youtube
from src.utils.youtube.data import YouTubeApiData
from src.utils.youtube.analytics import YouTubeApiAnalytics
from src.utils.youtube.upload import Upload
from src.utils.months import months
from src.utils.youtube.description import text


router = APIRouter(prefix="/youtube")


@router.get("/playlists")
async def playlists(user: User = Depends(verify)):
    playlists = YouTubeApiData(token=youtube.token).playlists()["items"]
    return {"playlists": [{"id": playlist["id"], "name": playlist["snippet"]["title"]} for playlist in playlists]}


@router.get("/subscribers-by-day")
async def subscribers(user: User = Depends(verify)):
    today = datetime.now().date()
    daily = YouTubeApiAnalytics(token=youtube.token).daily(
        start=(today - timedelta(days=29)),
        end=today,
        metrics=["views", "subscribersGained", "subscribersLost", "estimatedRevenue", "estimatedMinutesWatched"],
        filters={"channel": "UC9RKqI3GeK_fdHdQyaB5laQ"},
    )
    data = {"daily": [dict(zip([header["name"] for header in daily["columnHeaders"]], row)) for row in daily["rows"]]}
    return {
        "subscribersByDay": [
            {"date": row["day"], "subscribers": row["subscribersGained"] - row["subscribersLost"]} for row in data["daily"]
        ],
    }


@router.get("/analytics")
async def analytics(user: User = Depends(verify)):
    statistics = YouTubeApiData(token=youtube.token).channel()
    analytics = YouTubeApiAnalytics(token=youtube.token)
    today = datetime.now().date()
    daily = analytics.daily(
        start=(today - timedelta(days=29)),
        end=today,
        metrics=["views", "subscribersGained", "subscribersLost", "estimatedRevenue", "estimatedMinutesWatched"],
        filters={"channel": "UC9RKqI3GeK_fdHdQyaB5laQ"},
    )
    monthly = analytics.monthly()
    data = {
        "daily": [dict(zip([header["name"] for header in daily["columnHeaders"]], row)) for row in daily["rows"]],
        "monthly": [dict(zip([header["name"] for header in monthly["columnHeaders"]], row)) for row in monthly["rows"]],
    }
    return {
        "viewCount": int(statistics["items"][0]["statistics"]["viewCount"]),
        "subscriberCount": int(statistics["items"][0]["statistics"]["subscriberCount"]),
        "viewCountPrevious28Days": sum(row["views"] for row in data["daily"]),
        "subscribersCountPrevious28Days": sum(row["subscribersGained"] - row["subscribersLost"] for row in data["daily"]),
        "averageSubscriberGrowthPrevious28Days": mean(row["subscribersGained"] - row["subscribersLost"] for row in data["daily"]),
        "estimatedRevenuePrevious28Days": sum(row["estimatedRevenue"] for row in data["daily"]),
        "averageEstimatedRevenuePrevious28Days": mean(row["estimatedRevenue"] for row in data["daily"]),
        "watchTimePrevious28Days": int(sum(row["estimatedMinutesWatched"] for row in data["daily"]) / 60),
        "subscribersByDay": [
            {"date": row["day"], "subscribers": row["subscribersGained"] - row["subscribersLost"]} for row in data["daily"]
        ],
        "revenueByMonth": [
            {"month": months[row["month"].split("-")[1]], "value": round(row["estimatedRevenue"], 2)} for row in data["monthly"]
        ],
    }


@router.post("/upload")
async def upload(
    background: BackgroundTasks,
    user: User = Depends(verify),
    file: UploadFile = File(...),
    throwbackThursday: bool = Form(False),
    playlists: Optional[str] = Form(""),
    comment: Optional[str] = Form(""),
):
    video = await file.read()
    title = splitext(basename(file.filename))[0]
    description = f"{comment}\n\n{text}" if comment else text
    description = f"WavesOnly Throwback Thursday: {title}\n\n{description}" if throwbackThursday else f"{title}\n\n{description}"
    playlists = playlists.split(",") if playlists else []
    background.add_task(Upload().orchestrate, video=video, title=title, description=description, playlists=playlists)
    return {"message": "Upload started"}
