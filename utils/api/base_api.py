import requests
from core.config import settings

_token_cache: dict = {}


def get_token(user: str = "admin") -> str:
    if user not in _token_cache:
        creds = settings.USERS[user]
        response = requests.post(f"{settings.API_BASE_URL}/user/login", json={
            "username": creds["username"],
            "password": creds["password"]
        })
        response.raise_for_status()
        _token_cache[user] = response.json()["token"]
    return _token_cache[user]


def clear_token_cache():
    _token_cache.clear()


def headers(user: str = "admin") -> dict:
    return {"Authorization": f"Bearer {get_token(user)}"}


def get(endpoint: str, user: str = "admin", params: dict = None) -> dict:
    response = requests.get(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        params=params
    )
    response.raise_for_status()
    return response.json()


def post(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    response = requests.post(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        json=payload
    )
    response.raise_for_status()
    return response.json()
