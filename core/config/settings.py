import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "dev")
load_dotenv(f".env.{ENV}" if ENV != "dev" else ".env")

BASE_URL = os.getenv("BASE_URL")
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"

USERS = {
    "admin": {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD")
    },
    "hr_manager": {
        "username": os.getenv("HR_MANAGER_USERNAME"),
        "password": os.getenv("HR_MANAGER_PASSWORD")
    },
    "recruiter": {
        "username": os.getenv("RECRUITER_USERNAME"),
        "password": os.getenv("RECRUITER_PASSWORD")
    },
    "finance": {
        "username": os.getenv("FINANCE_USERNAME"),
        "password": os.getenv("FINANCE_PASSWORD")
    }
}

EMPLOYEES = {
    "nitin": {
        "username": os.getenv("NITIN_USERNAME"),
        "password": os.getenv("NITIN_PASSWORD")
    },
    "anil": {
        "username": os.getenv("ANIL_USERNAME"),
        "password": os.getenv("ANIL_PASSWORD")
    },
    "neha": {
        "username": os.getenv("NEHA_USERNAME"),
        "password": os.getenv("NEHA_PASSWORD")
    },
    "praveen": {
        "username": os.getenv("PRAVEEN_USERNAME"),
        "password": os.getenv("PRAVEEN_PASSWORD")
    },
    "sunita": {
        "username": os.getenv("SUNITA_USERNAME"),
        "password": os.getenv("SUNITA_PASSWORD")
    }
}
