from utils.api.base_api import get


import json
from utils.api.base_api import get


def get_regularization_approval_setting_api(user: str = "admin") -> dict:
    """GET /Regularization/RegularizationApprovalSetting — returns company, branch, department approval settings."""
    try:
        return get("Regularization/RegularizationApprovalSetting", user=user)
    except Exception:
        return {}


def determine_approval_hierarchy(duration_days: int) -> list[str]:
    """
    Default Approval Hierarchy Matrix:
    - 1 Day: Team Lead -> Manager -> Branch Head
    - 2–7 Days: Manager -> Branch Head
    - > 7 Days: Branch Head
    """
    if duration_days == 1:
        return ["Team Lead", "Manager", "Branch Head"]
    elif 2 <= duration_days <= 7:
        return ["Manager", "Branch Head"]
    else:
        return ["Branch Head"]


def get_dynamic_approval_hierarchy_api(duration_days: int, user: str = "admin") -> list[str]:
    """
    Dynamically fetches Regularization Approval Settings from:
    GET /Regularization/RegularizationApprovalSetting
    and resolves approval hierarchy based on active Company, Branch, & Department configuration.

    Fallback Rule:
    If setting does not exist or is unconfigured -> automatically falls back to ["Branch Head"].
    """
    settings_data = get_regularization_approval_setting_api(user=user)
    if isinstance(settings_data, list) and settings_data:
        for rule in settings_data:
            min_days = rule.get("minDays", 0)
            max_days = rule.get("maxDays", 999)
            if min_days <= duration_days <= max_days:
                hierarchy = rule.get("approvalHierarchy") or rule.get("levels") or rule.get("roles")
                if hierarchy:
                    return hierarchy if isinstance(hierarchy, list) else [str(hierarchy)]

    # Fallback Rule: Automatically falls back to ["Branch Head"] if setting does not exist
    return ["Branch Head"]
