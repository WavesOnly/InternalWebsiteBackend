from src.database.mongo import mongo
from src.models.user import User
from src.tasks.followers import UpdateSpotifyData
from src.tasks.remove import RemoveOutdatedSongs
from src.tasks.refresh import RefreshOutdatedSongs


def main():
    users = mongo.all(collection="users", query={"roles": "Spotify"})
    for user in users:
        user = User(email=user["email"], roles=user["roles"], spotifyUserId=user["spotifyUserId"], spotifyAccessToken=user["spotifyAccessToken"], spotifyRefreshToken=user["spotifyRefreshToken"], youtubeAccessToken=user["youtubeAccessToken"], youtubeRefreshToken=user["youtubeRefreshToken"])
        for task in [UpdateSpotifyData, RemoveOutdatedSongs, RefreshOutdatedSongs]:
                task(user).run()


main()
