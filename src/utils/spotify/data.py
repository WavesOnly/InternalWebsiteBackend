from src.utils.api import session, SpotifyHandler
from src.models.user import User


class SpotifyApiData:
    url = "https://api.spotify.com/v1"

    def __init__(self, user: User):
        self.session = session
        self.session.hooks["response"] = []
        self.session.hooks["response"].append(SpotifyHandler(user=user).refresh)
        self.token = user.spotifyAccessToken

    def track(self, id: str) -> dict:
        url = f"{SpotifyApiData.url}/tracks/{id}"
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json()

    def album(self, id: str) -> dict:
        url = f"{SpotifyApiData.url}/albums/{id}"
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json()

    def playlists(self, user_id: str) -> dict:
        url = f"{SpotifyApiData.url}/users/{user_id}/playlists"
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json()

    def add(self, id: str, uri: str, position: int) -> None:
        url = f"{SpotifyApiData.url}/playlists/{id}/tracks"
        data = {"uris": [uri], "position": position}
        response = self.session.post(url=url, headers={"Authorization": f"Bearer {self.token}"}, json=data)
        return response.json()

    def remove(self, id: str, uri: str) -> None:
        url = f"{SpotifyApiData.url}/playlists/{id}/tracks"
        data = {"tracks": [{"uri": uri}]}
        response = self.session.delete(url=url, headers={"Authorization": f"Bearer {self.token}"}, json=data)
        return response.json()

    def items(self, id: str) -> dict:
        url = f"{SpotifyApiData.url}/playlists/{id}/tracks"
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json()

    def update(self, id: str, ids: list[str]) -> None:
        url = f"{SpotifyApiData.url}/playlists/{id}/tracks"
        data = {"range_start": 0, "uris": [f"spotify:track:{id}" for id in ids]}
        response = self.session.put(url=url, headers={"Authorization": f"Bearer {self.token}"}, json=data)
        return response.json()

    def delete(self, id: str, ids: list[str]) -> None:
        url = f"{SpotifyApiData.url}/playlists/{id}/tracks"
        data = {"tracks": [{"uri": f"spotify:track:{id}"} for id in ids]}
        response = self.session.delete(url=url, headers={"Authorization": f"Bearer {self.token}"}, json=data)
        return response.json()

    def user(self, id: str) -> dict:
        url = f"{SpotifyApiData.url}/users/{id}"
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json()

    def playlist(self, id: str) -> dict:
        url = f"{SpotifyApiData.url}/playlists/{id}"
        response = self.session.get(url=url, headers={"Authorization": f"Bearer {self.token}"})
        return response.json()
