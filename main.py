from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import auth
from src.routes import youtube
from src.routes import spotify
from src.routes import general


app = FastAPI()

app.include_router(general.router)
app.include_router(auth.router)
app.include_router(spotify.router)
app.include_router(youtube.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
