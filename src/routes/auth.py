from fastapi import APIRouter, Request, Response, HTTPException

from src.models.auth import Auth
from src.utils.google import GoogleOAuth
from src.database.mongo import mongo


router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(auth: Auth, response: Response):
    google = GoogleOAuth()
    tokens = await google.exchange(code=auth.code)
    info = await google.verify(token=tokens.idToken)
    user = mongo.one(collection="users", query={"email": info["email"].lower()}) 
    if not user:
        raise HTTPException(status_code=404, detail="Invalid user")
    response.set_cookie(key="refreshToken", value=tokens.refreshToken, httponly=True, secure=True, path="/", samesite="None")
    return {"idToken": tokens.idToken, "user": {"email": user["email"], "roles": user["roles"], "username": user["username"], "spotifyUserId": user["spotifyUserId"]}}


@router.get("/refresh-token")
async def refresh(request: Request):
    if not request.cookies.get("refreshToken", None):
        raise HTTPException(status_code=400, detail="No refresh token provided")
    google = GoogleOAuth()
    tokens = await google.refresh(refresh=request.cookies["refreshToken"])
    info = await google.verify(token=tokens["idToken"])
    user = mongo.one(collection="users", query={"email": info["email"].lower()}) 
    return {"idToken": tokens["idToken"], "user": {"email": user["email"], "roles": user["roles"], "username": user["username"], "spotifyUserId": user["spotifyUserId"]}}


@router.get("/logout")
async def logout(response: Response):
    response.set_cookie(
        key="refreshToken",
        value="",
        httponly=True,
        secure=True,
        path="/",
        samesite="None",
        expires=0,
    )
    return {"message": "Logged out"}
