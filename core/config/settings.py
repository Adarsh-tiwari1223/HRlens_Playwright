"""
HRlens Portal — Public Runtime Configuration Interface.

Combines and re-exports environment, user, and constant configurations
to maintain 100% backward-compatibility across all tests, page objects, and utilities.
"""

import os
import logging

from core.config.environments import (
    ALLOWED_ENVS,
    ENV,
    BASE_URL,
    API_BASE_URL,
    BASE_URL_STG,
    API_BASE_URL_STG,
    BASE_URL_PROD,
    API_BASE_URL_PROD,
    API_BASE_URL_LEGACY,
)
from core.config.constants import (
    DEFAULT_TIMEOUT,
    LEAVE_FROM_OFFSET,
    LEAVE_TO_OFFSET,
    LEAVE_BACK_DATE_OFFSET,
    EMPLOYEE_USER,
)
from core.config.users import (
    USERS,
    APPROVERS,
    _get_env,
)

logger = logging.getLogger(__name__)

# Active Headless configuration (CLI or environment variable override)
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true" or os.getenv("CI", "false").lower() == "true"

# Print startup banner matching existing behavior
print("\n" + "=" * 50)
print("HRlens Playwright - Active Configuration")
print("=" * 50)
print(f"ENV:        {ENV}")
print(f"API URL:    {API_BASE_URL}")
print("=" * 50 + "\n")

logger.info(f"Active ENV: {ENV}")
logger.info(f"Active API URL: {API_BASE_URL}")
