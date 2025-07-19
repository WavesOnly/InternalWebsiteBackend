from fastapi import APIRouter, Depends, HTTPException

from src.models.user import User
from src.models.general import Task
from src.utils.auth import verify
from src.tasks.main import main

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Welcome to the WavesOnly API"}

@router.get("/meetings")
async def meetings(user: User = Depends(verify)):
    if "Meetings" not in user.roles:
        raise HTTPException(status_code=403, detail=f"User with E-Mail '{user.email}' does not have Meetings access")
    
@router.post("/task")
async def task(data: Task):
    if data.password != "cron-job":
        return HTTPException(status_code=403, detail="Access prohibited")
    main()
    return {"message": "Task(s) completed successfully"}