"""
Environment definitions and URL resolution for HRlens Portal.
"""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ALLOWED_ENVS = {"stg", "prod"}

# 1. Load primary .env file
load_dotenv(".env", override=False)

# 2. Fetch raw ENV variable and sanitize
raw_env = os.getenv("ENV", "stg").strip().lower()

if raw_env not in ALLOWED_ENVS:
    logger.warning(f"Invalid or unallowed ENV '{raw_env}' specified. Falling back strictly to Stage ('stg').")
    print(f"[WARNING] Invalid or unallowed ENV '{raw_env}' specified. Falling back strictly to Stage ('stg').")
    ENV = "stg"
else:
    ENV = raw_env

# 3. Override with environment-specific .env.stg or .env.prod if present
if os.path.exists(f".env.{ENV}"):
    load_dotenv(f".env.{ENV}", override=False)

# Explicit STG and PROD URLs
BASE_URL_STG = os.getenv("BASE_URL_STG") or "https://stg-hrlense.jobvritta.com"
API_BASE_URL_STG = os.getenv("API_BASE_URL_STG") or "https://audit.jobvritta.com/api"

BASE_URL_PROD = os.getenv("BASE_URL_PROD") or "https://www.hrlense.com"
API_BASE_URL_PROD = os.getenv("API_BASE_URL_PROD") or "https://hrmsapi.jobvritta.com/api"

# Legacy fallback
API_BASE_URL_LEGACY = os.getenv("API_BASE_URL")

# Determine active BASE_URL and API_BASE_URL based on active ENV
if ENV == "prod":
    BASE_URL = (os.getenv("BASE_URL_PROD") or "https://www.hrlense.com").strip()
    API_BASE_URL = (os.getenv("API_BASE_URL_PROD") or "https://hrmsapi.jobvritta.com/api").strip()
else:
    BASE_URL = (os.getenv("BASE_URL_STG") or os.getenv("BASE_URL") or "https://stg-hrlense.jobvritta.com").strip()
    API_BASE_URL = (os.getenv("API_BASE_URL_STG") or API_BASE_URL_LEGACY or "https://audit.jobvritta.com/api").strip()
