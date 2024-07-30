from typing import List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, date
from bson import ObjectId


class Song(BaseModel):
    name: str
    id: str


class Artist(BaseModel):
    name: str
    id: str


class Playlist(BaseModel):
    id: str
    position: int
    duration: Optional[Union[int, str]]
    removed: bool


class PlaylistWithName(Playlist):
    name: str


class SongHistoryBase(BaseModel):
    song: Song
    artists: List[Artist]
    playlist: Playlist
    dateAdded: datetime
    comment: Optional[str]
    promotion: bool


class SongHistoryCreate(SongHistoryBase):
    dateRemoval: Optional[datetime]


class SongHistory(SongHistoryBase):
    id: Optional[str] = Field(None, alias="_id")
    playlist: PlaylistWithName

    class Config:
        json_encoders = {ObjectId: str}


class FollowerHistoryItem(BaseModel):
    date: date
    followers: int
