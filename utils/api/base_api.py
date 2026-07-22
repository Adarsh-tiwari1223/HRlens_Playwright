import time
import base64
import json
import logging
from playwright.sync_api import sync_playwright, APIRequestContext
from core.config import settings

logger = logging.getLogger(__name__)

_token_cache: dict = {}
_pw_instance = None
_request_context: APIRequestContext = None


def get_request_context() -> APIRequestContext:
    global _pw_instance, _request_context
    if _request_context is None:
        _pw_instance = sync_playwright().start()
        _request_context = _pw_instance.request.new_context()
    return _request_context


def _is_token_expired(token: str) -> bool:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        exp = json.loads(base64.b64decode(payload)).get("exp", 0)
        return time.time() >= exp - 30
    except Exception:
        return True


def _redact(data):
    if isinstance(data, dict):
        return {
            k: ("***" if any(s in k.lower() for s in ["password", "token", "secret", "email", "username", "user"]) else _redact(v))
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [_redact(item) for item in data]
    return data


def get_token(user: str = "admin") -> str:
    if user not in _token_cache or _is_token_expired(_token_cache[user]):
        creds = settings.USERS[user]
        login_url = f"{settings.API_BASE_URL}/user/login"
        payload = {
            "email": creds["username"],
            "user": creds["username"],
            "password": creds["password"]
        }
        logger.info(f"Attempting login to: {login_url}")
        logger.info(f"Payload: {json.dumps(_redact(payload), default=str)}")
        req = get_request_context()
        response = req.post(login_url, data=payload, timeout=30000)
        if response.status != 200:
            logger.error(f"Login failed: {response.status} - {response.text()}")
            raise Exception(f"HTTP {response.status}: {response.text()}")
        _token_cache[user] = response.json()["token"]
    return _token_cache[user]


def clear_token_cache():
    _token_cache.clear()


def headers(user: str = "admin") -> dict:
    return {"Authorization": f"Bearer {get_token(user)}"}


def _fmt(data) -> str:
    return json.dumps(_redact(data), indent=2, default=str)


def _log_response(method: str, endpoint: str, status_code: int, body: dict, is_warning: bool = False):
    if isinstance(body, list):
        body_str = f"[List of {len(body)} items]"
    else:
        body_str = _fmt(body)
        if len(body_str) > 300:
            body_str = body_str[:300] + "\n... [TRUNCATED FOR LOGS]"
    if is_warning:
        logger.warning("%s %s → %s\n%s", method, endpoint, status_code, body_str)
    else:
        logger.info("%s %s → %s\n%s", method, endpoint, status_code, body_str)


def get(endpoint: str, user: str = "admin", params: dict = None) -> dict:
    logger.info("GET %s | user: %s\nparams:\n%s", endpoint, user, _fmt(params))
    req = get_request_context()
    response = req.get(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        params=params,
        timeout=30000
    )
    if not response.ok:
        raise Exception(f"HTTP {response.status}: {response.text()}")
    body = response.json()
    _log_response("GET", endpoint, response.status, body)
    return body


def post(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    logger.info("POST %s | user: %s\npayload:\n%s", endpoint, user, _fmt(payload))
    req = get_request_context()
    response = req.post(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        data=payload,
        timeout=30000
    )
    if response.status == 400:
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text()}
        _log_response("POST", endpoint, 400, body, is_warning=True)
        return body
    if not response.ok:
        raise Exception(f"HTTP {response.status}: {response.text()}")
    body = response.json()
    _log_response("POST", endpoint, response.status, body)
    return body


def put(endpoint: str, user: str = "admin", payload: dict = None) -> dict:
    logger.info("PUT %s | user: %s\npayload:\n%s", endpoint, user, _fmt(payload))
    req = get_request_context()
    response = req.put(
        f"{settings.API_BASE_URL}/{endpoint}",
        headers=headers(user),
        data=payload,
        timeout=30000
    )
    if response.status == 400:
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text()}
        _log_response("PUT", endpoint, 400, body, is_warning=True)
        return body
    if not response.ok:
        raise Exception(f"HTTP {response.status}: {response.text()}")
    body = response.json()
    _log_response("PUT", endpoint, response.status, body)
    return body

