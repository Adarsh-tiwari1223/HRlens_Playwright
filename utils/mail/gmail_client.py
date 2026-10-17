"""
HRlens Portal — Gmail REST API Client.
Reads, fetches, and verifies transactional/notification emails sent to qa.tekinspirations@gmail.com
for candidate offboarding, resignation letters, and system alerts.

Uses OAuth 2.0 Desktop credentials from client_sec.json / client_secret.json.
Generates and persists token.json for permanent background execution without repeated login prompts.
"""

import os
import json
import base64
import time
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
from typing import Optional, Dict, Any, List

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def _find_client_secret_file() -> str:
    """Finds client_sec.json or client_secret.json in project root."""
    for filename in ["client_sec.json", "client_secret.json"]:
        path = os.path.join(BASE_DIR, filename)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        f"OAuth client file (client_sec.json or client_secret.json) not found in {BASE_DIR}"
    )


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Local HTTP handler to receive Google OAuth authorization code."""
    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            _OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;padding:50px;'>"
                b"<h2 style='color:#16a34a;'>Authentication Successful!</h2>"
                b"<p>Google OAuth authorization complete for qa.tekinspirations@gmail.com.</p>"
                b"<p>You can close this tab and return to the terminal.</p>"
                b"</body></html>"
            )
        elif "error" in params:
            _OAuthCallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h2>Authentication Failed</h2><p>{_OAuthCallbackHandler.error}</p></body></html>".encode("utf-8")
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default HTTP server logging
        pass


class GmailClient:
    """Gmail API Client tailored for HRlens email verification."""

    def __init__(self, token_path: Optional[str] = None, client_secret_path: Optional[str] = None):
        self.token_path = token_path or TOKEN_PATH
        self.client_secret_path = client_secret_path or _find_client_secret_file()
        self.service = None

    def authenticate(self, port: int = 8088) -> Credentials:
        """
        Loads existing token.json or runs 1-time OAuth authorization flow via browser.
        """
        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                logger.info(f"Loaded existing Gmail OAuth credentials from {self.token_path}")
            except Exception as e:
                logger.warning(f"Failed to load {self.token_path}: {e}. Re-authenticating...")

        # If credentials don't exist or are invalid, refresh or re-authorize
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Gmail OAuth token expired. Refreshing token via Google...")
                creds.refresh(Request())
                with open(self.token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(creds.to_json())
                logger.info("Gmail OAuth token successfully refreshed and saved.")
                return creds
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}. Initiating fresh authorization flow...")
                creds = None

        if not creds or not creds.valid:
            logger.info("Initiating 1-time Google OAuth authorization flow for Gmail...")
            with open(self.client_secret_path, "r", encoding="utf-8") as f:
                client_data = json.load(f)

            installed_info = client_data.get("installed") or client_data.get("web")
            if not installed_info:
                raise ValueError(f"Invalid OAuth secret structure in {self.client_secret_path}")

            client_id = installed_info["client_id"]
            client_secret = installed_info["client_secret"]
            redirect_uri = f"http://localhost:{port}"

            # Prepare OAuth authorization URL
            auth_params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(SCOPES),
                "access_type": "offline",
                "prompt": "consent",
            }
            auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(auth_params)}"

            print("\n" + "=" * 70)
            print("GMAIL OAUTH AUTHORIZATION REQUIRED")
            print("=" * 70)
            print(f"Please log in with: qa.tekinspirations@gmail.com")
            print(f"Opening browser link: {auth_url}")
            print("=" * 70 + "\n")

            # Start local server to receive auth code
            server = HTTPServer(("localhost", port), _OAuthCallbackHandler)
            _OAuthCallbackHandler.auth_code = None
            _OAuthCallbackHandler.error = None

            webbrowser.open(auth_url)

            # Wait for callback
            server.handle_request()
            server.server_close()

            if _OAuthCallbackHandler.error:
                raise RuntimeError(f"Google OAuth authorization failed: {_OAuthCallbackHandler.error}")

            auth_code = _OAuthCallbackHandler.auth_code
            if not auth_code:
                raise RuntimeError("Failed to capture Google OAuth authorization code from callback.")

            # Exchange code for access & refresh token
            logger.info("Exchanging authorization code for OAuth tokens...")
            token_res = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": auth_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
                timeout=15
            )

            if token_res.status_code != 200:
                raise RuntimeError(f"Token exchange failed: {token_res.status_code} - {token_res.text}")

            token_payload = token_res.json()
            creds = Credentials(
                token=token_payload["access_token"],
                refresh_token=token_payload.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES,
            )

            with open(self.token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

            logger.info(f"OAuth credentials saved successfully to {self.token_path}!")

        return creds

    def get_service(self):
        """Returns the cached Gmail v1 API service resource."""
        if not self.service:
            creds = self.authenticate()
            self.service = build("gmail", "v1", credentials=creds)
        return self.service

    def search_messages(self, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Searches emails using standard Gmail search syntax.
        Example queries:
        - 'subject:Relieving'
        - 'from:noreply to:qa.tekinspirations@gmail.com'
        - 'Adarsh Tiwari'
        """
        service = self.get_service()
        logger.info(f"Querying Gmail API: query='{query}', max_results={max_results}")
        res = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = res.get("messages", [])
        return messages

    def get_message_detail(self, message_id: str) -> Dict[str, Any]:
        """
        Fetches full details of a single message including headers, body, and attachment names.
        """
        service = self.get_service()
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()

        payload = msg.get("payload", {})
        headers_list = payload.get("headers", [])
        headers = {h["name"].lower(): h["value"] for h in headers_list}

        # Extract attachments and body
        attachments = []
        body_text = ""

        def parse_parts(parts):
            nonlocal body_text
            for part in parts:
                filename = part.get("filename")
                if filename:
                    attachments.append(filename)
                mime_type = part.get("mimeType", "")
                part_body = part.get("body", {})
                data = part_body.get("data")
                if data and ("text/plain" in mime_type or "text/html" in mime_type):
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        body_text += "\n" + decoded
                    except Exception:
                        pass
                if "parts" in part:
                    parse_parts(part["parts"])

        if "parts" in payload:
            parse_parts(payload["parts"])
        else:
            data = payload.get("body", {}).get("data")
            if data:
                try:
                    body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                except Exception:
                    pass

        return {
            "id": message_id,
            "threadId": msg.get("threadId"),
            "subject": headers.get("subject", ""),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "date": headers.get("date", ""),
            "snippet": msg.get("snippet", ""),
            "body": body_text.strip(),
            "attachments": attachments,
        }

    def wait_for_email(
        self,
        subject_keyword: str,
        employee_name: Optional[str] = None,
        timeout_sec: int = 60,
        poll_interval: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Polls Gmail until an email matching subject_keyword (and optionally employee_name) arrives.
        Returns the parsed message details or None if timed out.
        """
        query_parts = [f"subject:{subject_keyword}"]
        if employee_name:
            query_parts.append(f'"{employee_name}"')
        query = " ".join(query_parts)

        logger.info(f"[MAIL POLLER] Waiting for email matching '{query}' (timeout={timeout_sec}s)...")
        start_time = time.time()

        while time.time() - start_time < timeout_sec:
            messages = self.search_messages(query=query, max_results=5)
            if messages:
                latest_msg_id = messages[0]["id"]
                detail = self.get_message_detail(latest_msg_id)
                logger.info(f"[MAIL POLLER] Matched email! Subject: '{detail['subject']}' | From: '{detail['from']}'")
                return detail

            time.sleep(poll_interval)

        logger.warning(f"[MAIL POLLER] Timed out waiting for email matching '{query}' after {timeout_sec}s")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = GmailClient()
    print("Testing Gmail API Authentication...")
    creds = client.authenticate()
    print("Credentials valid:", creds.valid)
    service = client.get_service()
    profile = service.users().getProfile(userId="me").execute()
    print("\nGmail User Profile:")
    print("Email Address :", profile.get("emailAddress"))
    print("Total Messages:", profile.get("messagesTotal"))
    print("\nListing latest 5 messages:")
    msgs = client.search_messages(max_results=5)
    for m in msgs:
        d = client.get_message_detail(m["id"])
        print(f"- [{d['date']}] Subject: {d['subject']} | From: {d['from']}")
