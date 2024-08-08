from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi.encoders import jsonable_encoder
import asyncio

from src.utils.auth import verify
from src.models.user import User
from src.models.monetization import Monetization
from src.models.spotify import AddSong, UpdatePlaylist
from src.models.database import SongHistory, SongHistoryCreate, FollowerHistoryItem
from src.utils.spotify.client import spotify
from src.utils.spotify.data import SpotifyApiData
from src.database.mongo import mongo


router = APIRouter(prefix="/spotify")


@router.get("/playlists")
async def playlists(user: User = Depends(verify)):
    playlists = SpotifyApiData(token=spotify.token).playlists()["items"]
    data = []
    for playlist in playlists:
        if playlist["owner"]["id"] == "w5sxze6rmcbs22r6w22ks8zme":
            document = mongo.one(collection="spotifyPlaylists", query={"playlistId": playlist["id"]})
            data.append(
                {
                    "id": playlist["id"],
                    "name": playlist["name"],
                    "trackCount": playlist["tracks"]["total"],
                    "followers": document["followers"],
                    "imageUrl": playlist["images"][0]["url"],
                    "averageGrowth": document["averageGrowth"],
                }
            )
    return {"playlists": data}


@router.get("/playlists/history/{id:path}")
async def playlist(id: Optional[str] = None, user: User = Depends(verify)):
    if not id:
        now = datetime.now(timezone.utc)
        followers = mongo.pipeline(
            collection="spotifyPlaylists",
            query=[
                {"$unwind": "$followerHistory"},
                {"$match": {"followerHistory.date": {"$gte": now - timedelta(days=28), "$lte": now}}},
                {"$group": {"_id": "$followerHistory.date", "totalFollowers": {"$sum": "$followerHistory.followers"}}},
                {"$sort": {"_id": -1}},
                {"$project": {"date": "$_id", "followers": "$totalFollowers"}},
            ],
        )
        return {"playlistFollowerHistory": jsonable_encoder([FollowerHistoryItem(**item) for item in followers])}
    else:
        playlist = mongo.one(collection="spotifyPlaylists", query={"playlistId": id})
        return {
            "playlistFollowerHistory": jsonable_encoder([FollowerHistoryItem(**item) for item in playlist["followerHistory"]])
        }


@router.get("/playlist/items/{id:path}")
async def items(id: Optional[str] = None, user: User = Depends(verify)):
    items = SpotifyApiData(token=spotify.token).items(id=id)["items"]
    items = [
        {
            "dateAdded": item["added_at"],
            "releaseDate": item["track"]["album"]["release_date"],
            "artists": [{"id": artist["id"], "name": artist["name"]} for artist in item["track"]["artists"]],
            "id": item["track"]["id"],
            "name": item["track"]["name"],
            "albumId": item["track"]["album"]["id"],
            "addedForPromotion": False,
        }
        for item in items
    ]
    return {"playlistItems": items}


@router.get("/curation/history")
async def history(user: User = Depends(verify)):
    history = mongo.all(collection="history", query={"promotion": True}, sort=[("dateAdded", -1)])
    for document in history:
        playlist = SpotifyApiData(token=spotify.token).playlist(id=document["playlist"]["id"])
        document["playlist"]["name"] = playlist["name"]
    history = [SongHistory(**document).model_dump() for document in history]
    return {"songHistory": history}


@router.post("/monetization-pipeline")
async def monetization(data: Monetization, user: User = Depends(verify)):
    await asyncio.sleep(1)
    return {"message": f"Pipeline started"}


@router.get("/analytics")
async def analytics(user: User = Depends(verify)):
    api = SpotifyApiData(token=spotify.token)
    user = api.user()
    playlists = mongo.pipeline(
        collection="spotifyPlaylists",
        query=[
            {"$group": {"_id": None, "totalFollowers": {"$sum": "$followers"}}},
            {"$project": {"_id": 0, "totalFollowers": 1}},
        ],
    )
    query = [
        {"$unwind": "$followerHistory"},
        {"$match": {"followerHistory.date": {"$eq": {"$date": {"$subtract": ["$$NOW", 28 * 24 * 60 * 60 * 1000]}}}}},
        {"$group": {"_id": None, "totalFollowers": {"$sum": "$followerHistory.followers"}}},
        {"$project": {"_id": 0, "totalFollowers": 1}},
    ]
    try:
        previous = mongo.pipeline(collection="spotifyPlaylists", query=query)[0]["totalFollowers"]
    except IndexError:
        previous = 0
    try:
        account = mongo.pipeline(collection="spotifyAccount", query=query)[0]["totalFollowers"]
    except IndexError:
        account = 0
    return {
        "accountFollowers": user["followers"]["total"],
        "playlistFollowers": playlists[0]["totalFollowers"],
        "accountFollowersPrevious28Days": api.user()["followers"]["total"] - account,
        "playlistFollowersPrevious28Days": playlists[0]["totalFollowers"] - previous,
    }


@router.post("/add-song")
async def add(data: AddSong, user: User = Depends(verify)):
    api = SpotifyApiData(token=spotify.token)
    if "spotify.com/track" not in data.link and "spotify.com/album" not in data.link:
        raise HTTPException(status_code=400, detail={"message": "Invalid Spotify link"})
    try:
        if "album" in data.link:
            album = api.album(id=data.link.split("album/")[1].split("?")[0].split("#")[0])
            track = api.track(id=album["tracks"]["items"][0]["id"])
        elif "track" in data.link:
            track = api.track(id=data.link.split("track/")[1].split("?")[0].split("#")[0])
    except Exception:
        raise HTTPException(status_code=404, detail={"message": "No track found"})
    for playlist in data.playlists:
        items = api.items(id=playlist.id)["items"]
        for item in items:
            if item["track"]["id"] == track["id"]:
                playlist = api.playlist(id=playlist.id)
                raise HTTPException(status_code=400, detail={"message": f"Track already in playlist '{playlist['name']}'"})
        today = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc)
        try:
            document = {
                "song": {"name": track["name"], "id": track["id"]},
                "artists": [{"name": artist["name"], "id": artist["id"]} for artist in track["artists"]],
                "playlist": {"id": playlist.id, "position": playlist.position, "duration": playlist.duration, "removed": False},
                "dateAdded": today,
                "dateRemoval": today + timedelta(days=playlist.duration) if playlist.duration else None,
                "promotion": data.promotion,
                "comment": data.comment,
            }
            history = SongHistoryCreate(**document)
            mongo.insert(collection="history", document=history.model_dump())
            api.add(id=playlist.id, uri=f"spotify:track:{track['id']}", position=(playlist.position - 1))
        except Exception as e:
            raise HTTPException(status_code=400, detail={"message": f"Error adding song {e}"})
    return {"message": "Added to playlist(s)"}


@router.put("/playlist/items/{id}")
async def update(data: UpdatePlaylist, user: User = Depends(verify)):
    SpotifyApiData(token=spotify.token).update(id=data.playlistId, ids=data.songIds)
    return {"message": "Playlist updated"}


@router.delete("/playlist/{id}/songs")
async def delete(id: str, ids: List[str] = Query(..., description="List of song IDs to delete"), user: User = Depends(verify)):
    SpotifyApiData(token=spotify.token).delete(id=id, ids=ids[0].split(","))
    return {"message": "Playlist updated"}
