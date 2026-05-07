import time
import base64
import json
import logging
import requests
from core.config import settings

logger = logging.getLogger(__name__)

_token_cache: dict = {}


def _is_token_expired(token: str) -> bool:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        exp = json.loads(base64.b64decode(payload)).get("exp", 0)
        return time.time() >= exp - 30
    except Exception:
        return True


def get_token(user: str = "admin") -> str:
    if user not in _token_cache or _is_token_expired(_token_cache[user]):
        creds = settings.USERS[user]
        response = requests.post(f"{settings.API_BASE_URL}/user/login", json={
            "email": creds["username"],
            "user": creds["username"],
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
    logger.info("GET %s | user: %s | params: %s", endpoint, user, params)
    response = requests.get(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        params=params
    )
    response.raise_for_status()
    body = response.json()
    logger.info("GET %s → %s: %s", endpoint, response.status_code, body)
    return body


def post(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    logger.info("POST %s | user: %s | payload: %s", endpoint, user, json.dumps(payload, default=str))
    response = requests.post(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        json=payload
    )
    if response.status_code == 400:
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}
        logger.warning("POST %s → 400: %s", endpoint, body)
        return body
    response.raise_for_status()
    body = response.json()
    logger.info("POST %s → %s: %s", endpoint, response.status_code, body)
    return body


def put(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    logger.info("PUT %s | user: %s | payload: %s", endpoint, user, json.dumps(payload, default=str))
    response = requests.put(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        json=payload
    )
    if response.status_code == 400:
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}
        logger.warning("PUT %s → 400: %s", endpoint, body)
        return body
    response.raise_for_status()
    body = response.json()
    logger.info("PUT %s → %s: %s", endpoint, response.status_code, body)
    return body
