from fastapi import APIRouter, Depends, HTTPException

from src.models.user import User
from src.utils.auth import verify

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Welcome to the WavesOnly API"}

@router.get("/meetings")
async def meetings(user: User = Depends(verify)):
    if "Meetings" not in user.roles:
        raise HTTPException(status_code=403, detail=f"User with E-Mail '{user.email}' does not have Meetings access")