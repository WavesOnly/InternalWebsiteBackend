from fastapi import HTTPException
import httpx
import os
from urllib.parse import unquote
from time import time

from src.models.auth import Tokens


async def exchange_code_for_tokens(code: str) -> Tokens:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": unquote(code),
                "client_id": "451560312486-u0l307e2q72kaoj3fhe545vuvnakch3t.apps.googleusercontent.com",
                "client_secret": "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",
                "redirect_uri": "https://internalwebsitefrontend.onrender.com/",
                "grant_type": "authorization_code",
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        data = response.json()
        return Tokens(accessToken=data["access_token"], refreshToken=data["refresh_token"], idToken=data["id_token"])


async def verify_google_token(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid ID token")
        info = response.json()

        # Check audience (client ID)
        if info["aud"] != "451560312486-u0l307e2q72kaoj3fhe545vuvnakch3t.apps.googleusercontent.com":
            raise HTTPException(status_code=400, detail="Invalid client ID")

        if int(info["exp"]) < int(time()):
            raise HTTPException(status_code=400, detail="ID token has expired")

        return info


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "refresh_token",
                "client_id": "451560312486-u0l307e2q72kaoj3fhe545vuvnakch3t.apps.googleusercontent.com",
                "client_secret": "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",
                "refresh_token": refresh_token,
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to refresh access token")

        data = response.json()

        return {"idToken": data["id_token"]}
