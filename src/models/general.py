from pydantic import BaseModel


class Task(BaseModel):
    password: str