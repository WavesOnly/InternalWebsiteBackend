from pydantic import BaseModel


class Auth(BaseModel):
    code: str


class Tokens(BaseModel):
    accessToken: str
    refreshToken: str
    idToken: str
