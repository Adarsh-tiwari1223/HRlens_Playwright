import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "dev")
load_dotenv(f".env.{ENV}" if ENV != "dev" else ".env")

BASE_URL = os.getenv("BASE_URL")
API_BASE_URL = os.getenv("API_BASE_URL")
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "60000"))
LEAVE_FROM_OFFSET = int(os.getenv("LEAVE_FROM_OFFSET", "1"))
LEAVE_TO_OFFSET = int(os.getenv("LEAVE_TO_OFFSET", "1"))
EMPLOYEE_USER = os.getenv("EMPLOYEE_USER", "sanidhy")

USERS = {
    "admin": {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD")
    },
    "vivek": {
        "username": os.getenv("VIVEK_USERNAME"),
        "password": os.getenv("VIVEK_PASSWORD")
    },
    "tejaswini": {
        "username": os.getenv("TEJASWINI"),
        "password": os.getenv("TEJSWINI_PASSWORD")
    },
    "shiva": {
        "username": os.getenv("SHIVA"),
        "password": os.getenv("SHIVA_PASSWORD")
    },
    "sanidhy": {
        "username": os.getenv("SANIDHY_USERNAME"),
        "password": os.getenv("SANIDHY_PASSWORD")
    },
    "kumar_piyush": {
        "username": os.getenv("KUMAR_PIYUSH_USERNAME"),
        "password": os.getenv("KUMAR_PIYUSH_PASSWORD")
    },
    "ritesh_singh": {
        "username": os.getenv("RITESH_SINGH_USERNAME"),
        "password": os.getenv("RITESH_SINGH_PASSWORD")
    }
}

# Maps app display name → USERS key
APPROVERS = {
    "Vivek": "vivek",
    "Vivek Singh": "vivek",
    "Tejaswini Rishivanshi": "tejaswini",
    "Shiva Singh": "shiva",
}
