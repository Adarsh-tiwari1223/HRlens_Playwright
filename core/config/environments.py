"""
Environment definitions and URL resolution for HRlens Portal.
"""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ALLOWED_ENVS = {"stg"}

# 1. Load primary .env file
load_dotenv(".env", override=False)

# 2. Target environment is strictly Stage ('stg')
ENV = "stg"

# 3. Override with environment-specific .env.stg if present
if os.path.exists(".env.stg"):
    load_dotenv(".env.stg", override=False)

# Stage Environment URLs
BASE_URL_STG = os.getenv("BASE_URL_STG") or os.getenv("BASE_URL") or "https://stg-hrlense.jobvritta.com"
API_BASE_URL_STG = os.getenv("API_BASE_URL_STG") or os.getenv("API_BASE_URL") or "https://audit.jobvritta.com/api"

# Active URLs
BASE_URL = BASE_URL_STG.strip()
API_BASE_URL = API_BASE_URL_STG.strip()
