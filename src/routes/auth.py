from fastapi import APIRouter, Request, Response, HTTPException

from src.models.auth import Auth
from src.utils.google import GoogleOAuth


router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(auth: Auth, response: Response):
    google = GoogleOAuth()
    tokens = await google.exchange(code=auth.code)
    user = await google.verify(token=tokens.idToken)
    if user["email"].lower() != "wavesonlyofficial@gmail.com":
        raise HTTPException(status_code=404, detail="Invalid user")
    response.set_cookie(key="refreshToken", value=tokens.refreshToken, httponly=True, secure=True, path="/", samesite="None")
    return {"idToken": tokens.idToken, "user": {"email": user["email"], "name": user["name"]}}


@router.get("/refresh-token")
async def refresh(request: Request):
    if not request.cookies.get("refreshToken", None):
        raise HTTPException(status_code=400, detail="No refresh token provided")
    tokens = await GoogleOAuth().refresh(refresh=request.cookies["refreshToken"])
    return {"idToken": tokens["idToken"]}


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
