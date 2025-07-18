from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    email: str
    roles: list
    spotifyUserId: str
    spotifyAccessToken: str
    spotifyRefreshToken: str
    youtubeAccessToken: Optional[str]
    youtubeRefreshToken: Optional[str]
