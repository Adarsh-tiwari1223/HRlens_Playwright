"""
Centralized Test Suite Registry for HRlens Playwright Framework.

Defines the authoritative mapping of test suites (smoke, sanity, regression, etc.)
to their targeted files, markers, and test scenarios. This avoids scanning unrelated
modules during targeted runs (e.g. running 3 smoke tests in 0.18s instead of 15s).
"""

from typing import Dict, List, Any


SUITE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "smoke": {
        "name": "Smoke Suite",
        "description": "Critical path verification: authentication validation and end-to-end leave lifecycle",
        "marker": "smoke",
        "files": [
            "tests/hrlense_portal/ui/employee/test_hr_lens_auth.py",
            "tests/hrlense_portal/ui/attendance/test_leave.py",
        ],
        "test_names": [
            "test_login",
            "test_empty_fields_validation",
            "test_full_leave_apply_and_approve_workflow",
        ],
    },
    "sanity": {
        "name": "Sanity Suite",
        "description": "Essential operational checks across auth, leave, attendance sheet, and asset request",
        "marker": "sanity",
        "files": [
            "tests/hrlense_portal/ui/employee/test_hr_lens_auth.py",
            "tests/hrlense_portal/ui/attendance/test_leave.py",
            "tests/hrlense_portal/ui/attendance/test_attendance_sheet.py",
            "tests/hrlense_portal/ui/asset/test_asset_request.py",
        ],
        "test_names": [],
    },
    "attendance": {
        "name": "Attendance Domain Suite",
        "description": "Full attendance, leave rules, absence cases, regularization, and attendance sheets",
        "marker": "attendance",
        "files": [
            "tests/hrlense_portal/ui/attendance/",
        ],
        "test_names": [],
    },
    "asset": {
        "name": "Asset Domain Suite",
        "description": "Asset request, assignment, stock entry, and hardware/software inventory",
        "marker": "asset",
        "files": [
            "tests/hrlense_portal/ui/asset/",
        ],
        "test_names": [],
    },
    "resignation": {
        "name": "Resignation Domain Suite",
        "description": "Resignation submission, approval/rejection, exit interviews, and buyout workflows",
        "marker": "resignation",
        "files": [
            "tests/hrlense_portal/ui/resignation/",
        ],
        "test_names": [],
    },
    "internal_mail": {
        "name": "Internal Mail Suite",
        "description": "Company email compose, inbox, sent, trash, and draft management",
        "marker": "internal_mail",
        "files": [
            "tests/hrlense_portal/ui/internal_mail/",
        ],
        "test_names": [],
    },
    "regression": {
        "name": "Full Regression Suite",
        "description": "Complete test coverage across all portals, workflows, and APIs",
        "marker": "regression",
        "files": [
            "tests/",
        ],
        "test_names": [],
    },
}


def get_suite_files(suite_name: str) -> List[str]:
    """
    Returns the specific file or directory paths for a given suite name.
    Falls back to 'tests/' if suite name is unrecognized or regression.
    """
    suite = SUITE_REGISTRY.get(suite_name.lower())
    if suite and suite.get("files"):
        return suite["files"]
    return ["tests/"]


def get_suite_marker(suite_name: str) -> str:
    """Returns the pytest marker associated with a suite."""
    suite = SUITE_REGISTRY.get(suite_name.lower())
    if suite and suite.get("marker"):
        return suite["marker"]
    return suite_name


def get_smoke_files() -> List[str]:
    """Returns the explicit file list comprising the smoke test suite."""
    return SUITE_REGISTRY["smoke"]["files"]


def get_suite_target_string(suite_name: str) -> str:
    """
    Returns space-separated file paths for CLI invocation.
    Example: 'tests/.../test_hr_lens_auth.py tests/.../test_leave.py'
    """
    return " ".join(get_suite_files(suite_name))
