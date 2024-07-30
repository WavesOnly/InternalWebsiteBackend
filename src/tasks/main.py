from src.tasks.followers import UpdateSpotifyData
from src.tasks.remove import RemoveOutdatedSongs


def main():
    for task in [UpdateSpotifyData, RemoveOutdatedSongs]:
        task().run()


main()
