from dotenv import load_dotenv
from os import environ
from fastapi import HTTPException
from httpx import AsyncClient
from urllib.parse import unquote

from src.models.auth import Tokens


class GoogleOAuth:
    url = "https://oauth2.googleapis.com"

    def __init__(self):
        load_dotenv(".env")

    async def exchange(self, code: str) -> Tokens:
        async with AsyncClient() as client:
            url = f"{GoogleOAuth.url}/token"
            uri = (
                "https://internalwebsitefrontend.onrender.com"
                if environ.get("ENVIRONMENT") == "Production"
                else "http://localhost:5173"
            )
            response = await client.post(
                url=url,
                data={
                    "code": unquote(code),
                    "client_id": environ["GOOGLE_CLIENT_ID"],
                    "client_secret": environ["GOOGLE_CLIENT_SECRET"],
                    "redirect_uri": uri,
                    "grant_type": "authorization_code",
                },
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
            data = response.json()
            return Tokens(accessToken=data["access_token"], refreshToken=data["refresh_token"], idToken=data["id_token"])

    async def verify(self, token: str) -> dict:
        async with AsyncClient() as client:
            url = f"{GoogleOAuth.url}/tokeninfo?id_token={token}"
            response = await client.get(url=url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid ID token")
            info = response.json()
            if info["aud"] != "451560312486-u0l307e2q72kaoj3fhe545vuvnakch3t.apps.googleusercontent.com":
                raise HTTPException(status_code=400, detail={"message": "Invalid client ID"})
            return info

    async def refresh(self, refresh: str) -> dict:
        async with AsyncClient() as client:
            url = f"{GoogleOAuth.url}/token"
            response = await client.post(
                url=url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": environ["GOOGLE_CLIENT_ID"],
                    "client_secret": environ["GOOGLE_CLIENT_SECRET"],
                    "refresh_token": refresh,
                },
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail={"message": "Failed to refresh access token"})
            data = response.json()
            return {"idToken": data["id_token"]}
