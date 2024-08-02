from fastapi import APIRouter, UploadFile, Depends, File, Form, BackgroundTasks
from typing import Optional
from os.path import splitext
from ntpath import basename
from tempfile import NamedTemporaryFile

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


@router.get("/subscribers-by-day")
async def subscribers(user: User = Depends(verify)):
    daily = YouTubeApiAnalytics(token=youtube.token).daily()
    return {
        "subscribersByDay": [{"date": row[0], "subscribers": row[2]} for row in daily["rows"]],
    }


@router.get("/analytics")
async def analytics(user: User = Depends(verify)):
    statistics = YouTubeApiData(token=youtube.token).channel()
    analytics = YouTubeApiAnalytics(token=youtube.token)
    daily = analytics.daily()
    monthly = analytics.monthly()
    return {
        "viewCount": int(statistics["items"][0]["statistics"]["viewCount"]),
        "subscriberCount": int(statistics["items"][0]["statistics"]["subscriberCount"]),
        "viewCountPrevious28Days": sum(row[1] for row in daily["rows"]),
        "subscribersCountPrevious28Days": sum(row[2] for row in daily["rows"]),
        "estimatedRevenuePrevious28Days": round(sum(row[3] for row in daily["rows"]), 2),
        "watchTimePrevious28Days": int(sum(row[4] for row in daily["rows"]) / 60),
        "subscribersByDay": [{"date": row[0], "subscribers": row[2]} for row in daily["rows"]],
        "revenueByMonth": [{"month": months[row[0].split("-")[1]], "value": round(row[1], 2)} for row in monthly["rows"]],
    }


@router.get("/playlists")
async def playlists(user: User = Depends(verify)):
    playlists = YouTubeApiData(token=youtube.token).playlists()["items"]
    return {"playlists": [{"id": playlist["id"], "name": playlist["snippet"]["title"]} for playlist in playlists]}


@router.post("/upload")
async def upload(
    background: BackgroundTasks,
    user: User = Depends(verify),
    file: UploadFile = File(...),
    throwbackThursday: bool = Form(False),
    playlists: Optional[str] = Form(""),
    comment: Optional[str] = Form(""),
):
    with NamedTemporaryFile(delete=False, suffix=".mp4") as video:
        while chunk := await file.read(4096):
            video.write(chunk)
            print("Chunk wrote")
        path = video.name
    title = splitext(basename(file.filename))[0]
    description = f"{comment}\n\n{text}" if comment else text
    description = f"WavesOnly Throwback Thursday: {title}\n\n{description}" if throwbackThursday else f"{title}\n\n{description}"
    playlists = playlists.split(",") if playlists else []
    background.add_task(Upload().orchestrate, path=path, title=title, description=description, playlists=playlists)
    return {"message": "Uploaded started"}
