import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "dev")
load_dotenv(f".env.{ENV}" if ENV != "dev" else ".env")

BASE_URL = os.getenv("BASE_URL")
API_BASE_URL = os.getenv("API_BASE_URL", "https://audit.jobvritta.com/api")
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"

USERS = {
    "admin": {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD")
    },
    "vivek": {
        "username": os.getenv("VIVEK_USERNAME"),
        "password": os.getenv("VIVEK_PASSWORD")
    },
    "satyarth": {
        "username": os.getenv("SATYARTH_USERNAME"),
        "password": os.getenv("SATYARTH_PASSWORD")
    },
    "sanidhy": {
        "username": os.getenv("SANIDHY_USERNAME"),
        "password": os.getenv("SANIDHY_PASSWORD")
    },
    "kumar_piyush": {
        "username": os.getenv("KUMAR_PIYUSH_USERNAME"),
        "password": os.getenv("KUMAR_PIYUSH_PASSWORD")
    }
}
