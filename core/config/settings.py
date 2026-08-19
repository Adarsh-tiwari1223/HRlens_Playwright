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

# Explicit STG and PROD URLs
BASE_URL_STG = os.getenv("BASE_URL_STG") or "https://stg-hrlense.jobvritta.com"
API_BASE_URL_STG = os.getenv("API_BASE_URL_STG") or "https://audit.jobvritta.com/api"

BASE_URL_PROD = os.getenv("BASE_URL_PROD") or "https://www.hrlense.com"
API_BASE_URL_PROD = os.getenv("API_BASE_URL_PROD") or "https://hrmsapi.jobvritta.com/api"

# Legacy fallback
API_BASE_URL_LEGACY = os.getenv("API_BASE_URL")

# Determine active BASE_URL and API_BASE_URL based on ENV
if ENV == "prod":
    BASE_URL = (os.getenv("BASE_URL_PROD") or "https://www.hrlense.com").strip()
    API_BASE_URL = (os.getenv("API_BASE_URL_PROD") or "https://hrmsapi.jobvritta.com/api").strip()
else:
    BASE_URL = (os.getenv("BASE_URL_STG") or os.getenv("BASE_URL") or "https://stg-hrlense.jobvritta.com").strip()
    API_BASE_URL = (os.getenv("API_BASE_URL_STG") or API_BASE_URL_LEGACY or "https://audit.jobvritta.com/api").strip()



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
EMPLOYEE_USER = os.getenv("EMPLOYEE_USER", "uttam_kumar")

def _get_env(key: str, default: str = None) -> str:
    env_key = f"{key}_{ENV.upper()}"
    val = os.getenv(env_key) or os.getenv(key, default)
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
    },
    "uttam_kumar": {
        "username": _get_env("UTTAM_KUMAR_USERNAME"),
        "password": _get_env("UTTAM_KUMAR_PASSWORD")
    },
    "abhishek_singh": {
        "username": _get_env("ABHISHEK_SINGH_USERNAME"),
        "password": _get_env("ABHISHEK_SINGH_PASSWORD")
    },
    "it_admin": {
        "username": _get_env("IT_ADMIN_USERNAME", "tejasav.jaiswal@tekinspirations.com"),
        "password": _get_env("IT_ADMIN_PASSWORD", "Tejasav@5")
    },
    "it_agra_ritesh": {
        "username": _get_env("IT_AGRA_RITESHYADAV_USERNAME", "ritesh.y@tekinspirations.com"),
        "password": _get_env("IT_AGRA_RITESHYADAV_PASSWORD", "Ritesh@221208")
    },
    "it_lucknow_amit": {
        "username": _get_env("IT_LUCKNOW_AMITPAL_USERNAME", "amit.pal@codecrewzs.com"),
        "password": _get_env("IT_LUCKNOW_AMITPAL_PASSWORD", "")
    },
    "it_greaternoida_shubham": {
        "username": _get_env("IT_GREATERNOIDA_SHUBHAMKUMAR_USERNAME", "shubham@technovion.com"),
        "password": _get_env("IT_GREATERNOIDA_SHUBHAMKUMAR_PASSWORD", "Shubham9876@")
    },
    "it_admin_greaternoida": {
        "username": _get_env("IT_ADMIN_GREATERNOIDA_USERNAME", "shubham@technovion.com"),
        "password": _get_env("IT_ADMIN_GREATERNOIDA_PASSWORD", "Shubham9876@")
    },
    "it_varanasi_raunak": {
        "username": _get_env("IT_VARANASI_RAUNAKRAI_USERNAME", "raunak.rai@tekinspirations.com"),
        "password": _get_env("IT_VARANASI_RAUNAKRAI_PASSWORD", "")
    },
    "it_jaipur_ashu": {
        "username": _get_env("IT_JAIPUR_ASHUSAIN_USERNAME", "ashu.sain@corehuntinc.com"),
        "password": _get_env("IT_JAIPUR_ASHUSAIN_PASSWORD", "Ashu456sain")
    },
    "it_admin_jaipur": {
        "username": _get_env("IT_ADMIN_JAIPUR_USERNAME", "ashu.sain@corehuntinc.com"),
        "password": _get_env("IT_ADMIN_JAIPUR_PASSWORD", "Ashu456sain")
    },
    "it_meerut_aditya": {
        "username": _get_env("IT_MEERUT_ADITYASAXENA_USERNAME", "aditya.saxena@tekinspirations.com"),
        "password": _get_env("IT_MEERUT_ADITYASAXENA_PASSWORD", "")
    },
    "it_noida_puneet": {
        "username": _get_env("IT_NOIDA_PUNEETPRASAD_USERNAME", "pprasad@vyzeinc.com"),
        "password": _get_env("IT_NOIDA_PUNEETPRASAD_PASSWORD", "")
    },
    "it_noida_amarjeet": {
        "username": _get_env("IT_NOIDA_AMARJEETKUMAR_USERNAME", "amarjeet.kumar@vyzeinc.com"),
        "password": _get_env("IT_NOIDA_AMARJEETKUMAR_PASSWORD", "")
    },
    "it_varanasi_ashutosh": {
        "username": _get_env("IT_VARANASI_ASHUTOSHKUMAR_USERNAME", "ashutosh.kumar@jobvritta.com"),
        "password": _get_env("IT_VARANASI_ASHUTOSHKUMAR_PASSWORD", "Aditi@123")
    },
    "it_noida_abhishek": {
        "username": _get_env("IT_NOIDA_ABHISHEKKUMAR_USERNAME", "abhishek.kumar@vyzeinc.com"),
        "password": _get_env("IT_NOIDA_ABHISHEKKUMAR_PASSWORD", "")
    },
    "it_agra_sandeep": {
        "username": _get_env("IT_AGRA_SANDEEPSINGH_USERNAME", "sandeep.singh@tekinspirations.com"),
        "password": _get_env("IT_AGRA_SANDEEPSINGH_PASSWORD", "")
    },
    "it_noida_chandan": {
        "username": _get_env("IT_NOIDA_CHANDAN_USERNAME", "chandan@tekinspirations.com"),
        "password": _get_env("IT_NOIDA_CHANDAN_PASSWORD", "")
    },
    "it_varanasi_tejasav": {
        "username": _get_env("IT_VARANASI_TEJASAVJAISWAL_USERNAME", "tejasav.jaiswal@tekinspirations.com"),
        "password": _get_env("IT_VARANASI_TEJASAVJAISWAL_PASSWORD", "Tejasav@5")
    }
}

# Maps app display name → USERS key
APPROVERS = {
    "Vivek": "vivek",
    "Vivek Singh": "vivek",
    "Tejaswini Rishivanshi": "tejaswini",
    "Shiva Singh": "shiva",
    "Ritesh Singh": "ritesh_singh",
    "Uttam Kumar": "uttam_kumar",
    "Abhishek Singh": "abhishek_singh",
}
