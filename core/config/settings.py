import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file first, then environment-specific .env.stg or .env.prod
load_dotenv(".env", override=True)  # Always load base .env first
ENV = os.getenv("ENV", "dev").strip()
if ENV != "dev":
    load_dotenv(f".env.{ENV}", override=True)  # Override with stg/prod values

BASE_URL = os.getenv("BASE_URL")

# New: Explicit STG and PROD API URLs
API_BASE_URL_STG = os.getenv("API_BASE_URL_STG")
API_BASE_URL_PROD = os.getenv("API_BASE_URL_PROD")

# Legacy fallback
API_BASE_URL_LEGACY = os.getenv("API_BASE_URL")

# Determine active API_BASE_URL based on ENV (strictly STG default)
if ENV == "prod":
    API_BASE_URL = (API_BASE_URL_PROD or "https://hrmsapi.jobvritta.com/api").strip()
else:
    API_BASE_URL = (API_BASE_URL_STG or API_BASE_URL_LEGACY or "https://audit.jobvritta.com/api").strip()


print("\n" + "="*50)
print("HRlens Playwright - Active Configuration")
print("="*50)
print("ENV:        " + ENV)
print("API URL:    " + str(API_BASE_URL))
print("="*50 + "\n")

logger.info(f"Active ENV: {ENV}")
logger.info(f"Active API URL: {API_BASE_URL}")

HEADLESS = os.getenv("HEADLESS", "False").lower() == "true" or os.getenv("CI", "false").lower() == "true"
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "60000"))
LEAVE_FROM_OFFSET = int(os.getenv("LEAVE_FROM_OFFSET", "1"))
LEAVE_TO_OFFSET = int(os.getenv("LEAVE_TO_OFFSET", "1"))
LEAVE_BACK_DATE_OFFSET = int(os.getenv("LEAVE_BACK_DATE_OFFSET", "1"))
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
    },
    "adarsh_tiwari": {
        "username": os.getenv("ADARSH_TIWARI"),
        "password": os.getenv("ADARSH_TIWARI_PASSWORD")
    }
}

# Maps app display name → USERS key
APPROVERS = {
    "Vivek": "vivek",
    "Vivek Singh": "vivek",
    "Tejaswini Rishivanshi": "tejaswini",
    "Shiva Singh": "shiva",
    "Ritesh Singh": "ritesh_singh",
}
