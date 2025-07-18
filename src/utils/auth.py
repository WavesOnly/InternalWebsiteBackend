from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from src.utils.google import GoogleOAuth
from src.models.user import User
from src.config import bearer
from src.database.mongo import mongo


async def verify(credentials: HTTPAuthorizationCredentials = Security(bearer)):
    try:
        info = await GoogleOAuth().verify(token=credentials.credentials)
        user = mongo.one(collection="users", query={"email": info["email"].lower()}) 
        if not user:
            raise HTTPException(status_code=403, detail="Forbidden: User not authorized")
        return User(email=info["email"], roles=user["roles"], spotifyUserId=user["spotifyUserId"], spotifyAccessToken=user["spotifyAccessToken"], spotifyRefreshToken=user["spotifyRefreshToken"], youtubeAccessToken=user["youtubeAccessToken"], youtubeRefreshToken=user["youtubeRefreshToken"])
    except Exception as exception:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {exception}")
