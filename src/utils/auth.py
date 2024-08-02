from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from src.utils.google import GoogleOAuth
from src.models.user import User
from src.config import bearer


async def verify(credentials: HTTPAuthorizationCredentials = Security(bearer)):
    try:
        info = await GoogleOAuth().verify(token=credentials.credentials)
        if info["email"].lower() != "wavesonlyofficial@gmail.com":
            raise HTTPException(status_code=403, detail="Forbidden: User not authorized")
        return User(email=info["email"])
    except Exception as exception:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {exception}")
