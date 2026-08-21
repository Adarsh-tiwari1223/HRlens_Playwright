"""
Application-wide constants and default runtime parameter settings.
"""

import os

# Default timeout in milliseconds for Playwright actions and assertions
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "60000"))

# Default leave offset configurations (in days)
LEAVE_FROM_OFFSET = int(os.getenv("LEAVE_FROM_OFFSET", "1"))
LEAVE_TO_OFFSET = int(os.getenv("LEAVE_TO_OFFSET", "1"))
LEAVE_BACK_DATE_OFFSET = int(os.getenv("LEAVE_BACK_DATE_OFFSET", "1"))

# Default employee test user key
EMPLOYEE_USER = os.getenv("EMPLOYEE_USER", "uttam_kumar")
