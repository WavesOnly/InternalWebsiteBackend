from fastapi import APIRouter, Request, Response, HTTPException

from src.models.auth import Auth
from src.utils.google import exchange_code_for_tokens, verify_google_token, refresh_access_token


router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(auth: Auth, response: Response):
    tokens = await exchange_code_for_tokens(auth.code)
    user = await verify_google_token(tokens.idToken)
    if user["email"].lower() != "wavesonlyofficial@gmail.com":
        raise HTTPException(status_code=404, detail="Invalid user")
    response.set_cookie(key="refreshToken", value=tokens.refreshToken, httponly=True, secure=True)
    return {"idToken": tokens.idToken, "user": {"email": user["email"], "name": user["name"]}}


@router.get("/refresh-token")
async def refresh(request: Request):
    if not request.cookies.get("refreshToken", None):
        raise HTTPException(status_code=400, detail="No refresh token provided")
    tokens = await refresh_access_token(request.cookies["refreshToken"])
    return {"idToken": tokens["idToken"]}


@router.get("/logout")
async def logout(response: Response):
    response.set_cookie(key="refreshToken", value="", httponly=True, secure=True, expires=0)
    return {"message": "Logged out"}


# async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer)):
#     token = credentials.credentials
#     info = await verify_google_token(token)
#     return User(email=info["email"], name=info["name"])


# @app.get("/protected-route")
# async def protected_route(user: User = Depends(get_current_user)):
#     return {"message": f"Hello {user.name}, you have access to this route."}
