from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import auth
from src.routes import youtube
from src.routes import spotify


app = FastAPI()

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


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

# @app.post("/add-song")
# async def add_song():
#     return {"message": "Hello World"}


# @app.get("/get-playlists")
# async def get_playlist():
#     return {"message": "Hello World"}


# @app.get("/get-playlist-items")
# async def get_playlist():
#     return {"message": "Hello World"}


# @app.put("/update-playlist")
# async def update_playlist():
#     return {"message": "Hello World"}


# @app.get("/history")
# async def history():
#     return {"message": "Hello World"}


# @app.post("/monetization")
# async def monetization():
#     return {"message": "Hello World"}


# @app.post("/spotify-analytics")
# async def spotify_analytics():
#     return {"message": "Hello World"}
