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
from src.utils.spotify.data import SpotifyApiData
from src.database.mongo import mongo


router = APIRouter(prefix="/spotify")


@router.get("/playlists")
async def playlists(user: User = Depends(verify)):
    playlists = SpotifyApiData(user=user).playlists(user_id=user.spotifyUserId)["items"]
    data = []
    for playlist in playlists:
        if playlist["owner"]["id"] == user.spotifyUserId and playlist["public"]:
            document = mongo.one(collection="spotifyPlaylists", query={"playlistId": playlist["id"]})
            data.append(
                {
                    "id": playlist["id"],
                    "name": playlist["name"],
                    "trackCount": playlist["tracks"]["total"],
                    "followers": document["followers"],
                    "imageUrl": playlist["images"][0]["url"],
                    "averageGrowth": document["averageGrowth"],
                    "lastUpdated": document["lastUpdated"],
                }
            )
    return {"playlists": sorted(data, key=lambda playlist: playlist["followers"], reverse=True)}


@router.post("/playlists")
async def playlists(user: User = Depends(verify)):
    spotify = SpotifyApiData(user=user)
    playlists = spotify.playlists(user_id=user.spotifyUserId)["items"]
    for playlist in playlists:
        if playlist["owner"]["id"] == user.spotifyUserId:
            document = mongo.one(collection="spotifyPlaylists", query={"playlistId": playlist["id"]})
            if not document:
                data = spotify.playlist(id=playlist["id"])
                items = spotify.items(id=playlist["id"])
                for item in items["items"]:
                    item["added_at"] = datetime.strptime(item["added_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                updated = max(items["items"], key=lambda x: x["added_at"])["added_at"]
                mongo.insert(
                    collection="spotifyPlaylists", 
                    document={"playlistId": playlist["id"], "spotifyUserId": user.spotifyUserId, "followerHistory": [], "followers": data["followers"]["total"], "averageGrowth": None, "lastUpdated": updated}
                )
    return {"message": "Playlists synchornized"}



@router.get("/playlists/history/{id:path}")
async def playlist(id: Optional[str] = None, user: User = Depends(verify)):
    if not id:
        now = datetime.now(timezone.utc)
        followers = mongo.pipeline(
            collection="spotifyPlaylists",
            query=[
                {"$match": {"spotifyUserId": user.spotifyUserId}},
                {"$unwind": "$followerHistory"},
                {"$match": {"followerHistory.date": {"$gte": now - timedelta(days=28), "$lte": now}}},
                {"$group": {"_id": "$followerHistory.date", "totalFollowers": {"$sum": "$followerHistory.followers"}}},
                {"$sort": {"_id": -1}},
                {"$project": {"date": "$_id", "followers": "$totalFollowers"}},
            ],
        )
        return {"playlistFollowerHistory": jsonable_encoder([FollowerHistoryItem(**item) for item in followers])}
    else:
        playlist = mongo.one(collection="spotifyPlaylists", query={"playlistId": id, "spotifyUserId": user.spotifyUserId})
        return {
            "playlistFollowerHistory": jsonable_encoder([FollowerHistoryItem(**item) for item in playlist["followerHistory"]])
        }


@router.get("/playlist/items/{id:path}")
async def items(id: Optional[str] = None, user: User = Depends(verify)):
    playlist = mongo.one(collection="spotifyPlaylists", query={"playlistId": id, "spotifyUserId": user.spotifyUserId})
    if not playlist:
        raise HTTPException(status_code=403, detail="You don't have access to this playlist")
    items = SpotifyApiData(user=user).items(id=id)["items"]
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
    history = mongo.all(collection="history", query={"promotion": True, "spotifyUserId": user.spotifyUserId}, sort=[("dateAdded", -1)])
    for document in history:
        playlist = SpotifyApiData(user=user).playlist(id=document["playlist"]["id"])
        document["playlist"]["name"] = playlist["name"]
    history = [SongHistory(**document).model_dump() for document in history]
    return {"songHistory": history}


@router.post("/monetization-pipeline")
async def monetization(data: Monetization, user: User = Depends(verify)):
    await asyncio.sleep(1)
    return {"message": f"Pipeline started"}


@router.get("/analytics")
async def analytics(user: User = Depends(verify)):
    api = SpotifyApiData(user=user)
    data = api.user(id=user.spotifyUserId)
    playlists = mongo.pipeline(
        collection="spotifyPlaylists",
        query=[
            {"$match": {"spotifyUserId": user.spotifyUserId}},
            {"$group": {"_id": None, "totalFollowers": {"$sum": "$followers"}}},
            {"$project": {"_id": 0, "totalFollowers": 1}},
        ],
    )
    date = datetime.now() - timedelta(days=28)
    query = [
        {"$match": {"spotifyUserId": user.spotifyUserId}},
        {"$unwind": "$followerHistory"},
        {"$match": {"followerHistory.date": {"$gte": date, "$lt": date + timedelta(days=1)}}},
        {"$group": {"_id": None, "totalFollowers": {"$sum": "$followerHistory.followers"}}},
        {"$project": {"_id": 0, "totalFollowers": 1}},
    ]
    previous = mongo.pipeline(collection="spotifyPlaylists", query=query)[0]["totalFollowers"]
    account = mongo.pipeline(collection="users", query=query)[0]["totalFollowers"]
    return {
        "accountFollowers": data["followers"]["total"],
        "playlistFollowers": playlists[0]["totalFollowers"],
        "accountFollowersPrevious28Days": api.user(id=user.spotifyUserId)["followers"]["total"] - account,
        "playlistFollowersPrevious28Days": playlists[0]["totalFollowers"] - previous,
    }


@router.post("/add-song")
async def add(data: AddSong, user: User = Depends(verify)):
    if "spotify.com/track" not in data.link and "spotify.com/album" not in data.link:
        raise HTTPException(status_code=400, detail={"message": "Invalid Spotify link"})
    for playlist in data.playlists:
        exists = mongo.one(collection="spotifyPlaylists", query={"playlistId": playlist.id, "spotifyUserId": user.spotifyUserId})
        if not exists:
            raise HTTPException(status_code=403, detail=f"You don't have access to playlist {playlist.id}")
    api = SpotifyApiData(user=user)
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
        now = datetime.now(timezone.utc)
        today = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
        try:
            document = {
                "spotifyUserId": user.spotifyUserId,
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
        except Exception as e:
            raise HTTPException(status_code=400, detail={"message": f"Error insertion song data into database: {e}"})
        try:
            api.add(id=playlist.id, uri=f"spotify:track:{track['id']}", position=(playlist.position - 1))
        except Exception as e:
            raise HTTPException(status_code=400, detail={"message": f"Error adding song to Spotify playlist {playlist.id}: {e}"})
        try:
            mongo.update(collection="spotifyPlaylists", id={"playlistId": playlist.id}, query={"$set": {"lastUpdated": now}})
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Error updating 'Last Updated' for playlist {playlist.id} on database: {e}"},
            )
    return {"message": "Added to playlist(s)"}


@router.put("/playlist/items/{id}")
async def update(data: UpdatePlaylist, user: User = Depends(verify)):
    playlist = mongo.one(collection="spotifyPlaylists", query={"playlistId": data.playlistId, "spotifyUserId": user.spotifyUserId})
    if not playlist:
        raise HTTPException(status_code=403, detail="You don't have access to this playlist")
    SpotifyApiData(user=user).update(id=data.playlistId, ids=data.songIds)
    return {"message": "Playlist updated"}


@router.delete("/playlist/{id}/songs")
async def delete(id: str, ids: List[str] = Query(..., description="List of song IDs to delete"), user: User = Depends(verify)):
    playlist = mongo.one(collection="spotifyPlaylists", query={"playlistId": id, "spotifyUserId": user.spotifyUserId})
    if not playlist:
        raise HTTPException(status_code=403, detail="You don't have access to this playlist")
    SpotifyApiData(user=user).delete(id=id, ids=ids[0].split(","))
    return {"message": "Playlist updated"}
