from src.tasks.followers import UpdateSpotifyData
from src.tasks.remove import RemoveOutdatedSongs
from src.database.mongo import mongo
from src.models.user import User

def main():
    users = mongo.all(collection="users", query={"roles": "Spotify"})
    for user in users:
        user = User(email=user["email"], roles=user["roles"], spotifyUserId=user["spotifyUserId"], spotifyAccessToken=user["spotifyAccessToken"], spotifyRefreshToken=user["spotifyRefreshToken"], youtubeAccessToken=user["youtubeAccessToken"], youtubeRefreshToken=user["youtubeRefreshToken"])
        for task in [UpdateSpotifyData, RemoveOutdatedSongs]:
                task(user).run()


main()
