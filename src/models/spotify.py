from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List


class PlaylistAddItem(BaseModel):
    id: str
    position: int
    duration: Optional[Union[int, str]]

    @field_validator("duration", mode="before")
    def convert(cls, duration):
        if isinstance(duration, str) and duration.lower() == "indefinite":
            return None
        return duration


class AddSong(BaseModel):
    link: str
    promotion: bool = False
    playlists: List[PlaylistAddItem] = Field(default_factory=list, min_items=1)
    comment: Optional[str] = None

    @field_validator("comment", mode="before")
    def convert(cls, comment):
        if isinstance(comment, str) and comment == "":
            return None
        return comment


class UpdatePlaylist(BaseModel):
    playlistId: str
    songIds: List[str] = Field(default_factory=list, min_items=1)
