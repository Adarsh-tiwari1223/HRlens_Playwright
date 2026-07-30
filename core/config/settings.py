import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ALLOWED_ENVS = {"stg", "prod"}

# Load .env file first
load_dotenv(".env", override=True)

# Fetch raw ENV variable and sanitize
raw_env = os.getenv("ENV", "stg").strip().lower()

if raw_env not in ALLOWED_ENVS:
    logger.warning(f"Invalid or unallowed ENV '{raw_env}' specified. Falling back strictly to Stage ('stg').")
    print(f"[WARNING] Invalid or unallowed ENV '{raw_env}' specified. Falling back strictly to Stage ('stg').")
    ENV = "stg"
else:
    ENV = raw_env

# Override with environment-specific .env.stg or .env.prod if present
if os.path.exists(f".env.{ENV}"):
    load_dotenv(f".env.{ENV}", override=True)

BASE_URL = os.getenv("BASE_URL")

# Explicit STG and PROD API URLs
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

def _get_env(key: str, default: str = None) -> str:
    val = os.getenv(key, default)
    return val.strip() if val else default

USERS = {
    "admin": {
        "username": _get_env("ADMIN_USERNAME"),
        "password": _get_env("ADMIN_PASSWORD")
    },
    "vivek": {
        "username": _get_env("VIVEK_USERNAME"),
        "password": _get_env("VIVEK_PASSWORD")
    },
    "tejaswini": {
        "username": _get_env("TEJASWINI"),
        "password": _get_env("TEJSWINI_PASSWORD")
    },
    "shiva": {
        "username": _get_env("SHIVA"),
        "password": _get_env("SHIVA_PASSWORD")
    },
    "sanidhy": {
        "username": _get_env("SANIDHY_USERNAME"),
        "password": _get_env("SANIDHY_PASSWORD")
    },
    "kumar_piyush": {
        "username": _get_env("KUMAR_PIYUSH_USERNAME"),
        "password": _get_env("KUMAR_PIYUSH_PASSWORD")
    },
    "ritesh_singh": {
        "username": _get_env("RITESH_SINGH_USERNAME"),
        "password": _get_env("RITESH_SINGH_PASSWORD")
    },
    "adarsh_tiwari": {
        "username": _get_env("ADARSH_TIWARI"),
        "password": _get_env("ADARSH_TIWARI_PASSWORD")
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
