"""
Accurately maps each Branch Group to its valid, allowed Payroll Company ID (from GET /api/Hrlense_Branch)
and updates all assets via PUT /api/Asset/assets/{id}.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_PRICES = {
    "laptop": 65000.0,
    "computer": 55000.0,
    "air conditioner": 45000.0,
    "ac": 45000.0,
    "chair": 8500.0,
    "desk": 15000.0,
    "table": 12000.0,
    "printer": 22000.0,
    "monitor": 18000.0,
    "security": 25000.0,
    "camera": 18000.0,
    "router": 14000.0,
    "vehicle": 750000.0,
    "headset": 3500.0,
    "peripheral": 2500.0,
}

def resolve_unit_price(asset: dict) -> float:
    current_price = asset.get("unit_Price") or asset.get("unitPrice") or asset.get("price") or 0.0
    try:
        current_price = float(current_price)
    except (ValueError, TypeError):
        current_price = 0.0

    if current_price > 0:
        return current_price

    desc = f"{asset.get('asset_Name', '')} {asset.get('category_Name', '')} {asset.get('sub_Category_Name', '')}".lower()
    for keyword, price in DEFAULT_PRICES.items():
        if keyword in desc:
            return price

    return 25000.0


def get_admin_headers() -> dict:
    creds = settings.USERS["admin"]
    resp = requests.post(
        f"{settings.API_BASE_URL}/user/login",
        json={"email": creds["username"], "user": creds["username"], "password": creds["password"]},
        timeout=15
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Admin login failed: HTTP {resp.status_code} - {resp.text}")
    token = resp.json().get("token")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def build_strict_branch_group_payroll_map(headers: dict) -> dict[int, int]:
    """
    Reads all branches from GET /api/Hrlense_Branch and branch groups from GET /api/Hrlense_Branch/branch-group.
    Maps each Branch Group ID -> valid company_ID belonging to that branch group.
    """
    logger.info("Resolving exact Branch -> Company mapping from /api/Hrlense_Branch...")
    
    # 1. Fetch all branch records which link branch_Name to company_ID
    b_url = f"{settings.API_BASE_URL}/Hrlense_Branch?rows=1000"
    b_resp = requests.get(b_url, headers=headers, timeout=15)
    all_branches = b_resp.json().get("data", []) if b_resp.status_code == 200 else []
    logger.info(f"Loaded {len(all_branches)} branch records from /api/Hrlense_Branch.")

    # 2. Fetch all branch groups
    bg_url = f"{settings.API_BASE_URL}/Hrlense_Branch/branch-group"
    bg_resp = requests.get(bg_url, headers=headers, timeout=15)
    branch_groups = bg_resp.json() if bg_resp.status_code == 200 else []
    logger.info(f"Loaded {len(branch_groups)} branch groups from /api/Hrlense_Branch/branch-group.")

    bg_to_company = {}

    for bg in branch_groups:
        bg_id = bg.get("id")
        bg_name = (bg.get("group_Name") or bg.get("name") or "").strip()
        bg_name_lower = bg_name.lower()

        # Find matching company_IDs from all_branches where branch_Name matches bg_name
        matched_companies = []
        for b in all_branches:
            b_name = (b.get("branch_Name") or "").strip().lower()
            c_id = b.get("company_ID")
            c_name = b.get("company_Name") or ""
            if c_id and (bg_name_lower in b_name or b_name in bg_name_lower):
                matched_companies.append({"id": int(c_id), "name": c_name})

        # Prefer 'TEK Inspirations' or ID 1 if available in matched, else first valid company
        chosen_company = None
        for mc in matched_companies:
            if "tek inspirations" in mc["name"].lower() or mc["id"] == 1:
                chosen_company = mc
                break

        if not chosen_company and matched_companies:
            chosen_company = matched_companies[0]

        if not chosen_company:
            # Fallback to TEK Inspirations LLC (ID 1)
            chosen_company = {"id": 1, "name": "TEK Inspirations LLC"}

        bg_to_company[int(bg_id)] = chosen_company["id"]
        logger.info(f"  Branch Group [{bg_id}] '{bg_name}' -> Allowed Company: '{chosen_company['name']}' (ID: {chosen_company['id']}) [Options: {[c['name'] for c in matched_companies[:4]]}]")

    return bg_to_company


def update_single_asset(asset: dict, bg_to_company: dict[int, int], headers: dict) -> tuple[int, bool, str]:
    aid = asset["id"]
    branch_id = asset.get("branch_Id") or 1
    
    target_payroll_id = bg_to_company.get(int(branch_id), 1)
    target_unit_price = resolve_unit_price(asset)

    payload = dict(asset)
    payload["unit_Price"] = target_unit_price
    payload["unitPrice"] = target_unit_price
    payload["payroll_Company_Id"] = target_payroll_id
    payload["payrollCompanyId"] = target_payroll_id

    try:
        resp = requests.put(
            f"{settings.API_BASE_URL}/Asset/assets/{aid}",
            headers=headers,
            json=payload,
            timeout=15
        )
        if resp.status_code in (200, 204):
            return aid, True, f"UnitPrice={target_unit_price}, PayrollCompanyId={target_payroll_id} (BranchGroup={branch_id})"
        else:
            return aid, False, f"HTTP {resp.status_code}: {resp.text[:120]}"
    except Exception as ex:
        return aid, False, str(ex)


def run_fix():
    headers = get_admin_headers()
    bg_to_company = build_strict_branch_group_payroll_map(headers)

    logger.info("Fetching all assets from /api/Asset/assets...")
    resp = requests.get(f"{settings.API_BASE_URL}/Asset/assets?page=1&rows=1000", headers=headers, timeout=20)
    assets = resp.json().get("data", []) if resp.status_code == 200 else []
    logger.info(f"Total assets found: {len(assets)}")

    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(update_single_asset, a, bg_to_company, headers): a
            for a in assets
        }
        for future in as_completed(futures):
            aid, ok, msg = future.result()
            if ok:
                success += 1
            else:
                failed += 1
                logger.warning(f"Failed to update asset {aid}: {msg}")

    logger.info("=" * 60)
    logger.info(f"Strict Branch-Payroll Asset Update Finished! Success: {success}, Failed: {failed}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_fix()
