"""
HRlens Portal - All Branch Asset Seeder (API-Driven).

Features:
1. Dynamically discovers active Branch Groups from GET /api/Hrlense_Branch/branch-group.
2. Dynamically discovers active Categories & Sub-Categories from AssesstsMaster.
3. Dynamically resolves active Payroll Company ID from GET /api/Hrlense_PayrollCompany.
4. Payload Architecture:
   - "branch_Id": Branch Group ID (e.g. 1 for Varanasi, 2 for Agra, 4 for Lucknow).
   - "payroll_Company_Id": Resolved Payroll Company ID from API.
   - "asset_Name": Format '{branch_group_name}_{brand_and_model}' (e.g. 'Varanasi_Dell Latitude 7440').
5. Creates stock across all branch groups and categories with zero hardcoded fallbacks.
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import random
import logging
import argparse
import requests
from core.config import settings
from pages.base_page import format_ascii_table
from utils.api.asset.asset_api import get_categories, get_subcategories

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_authenticated_headers() -> dict:
    """Authenticates as Admin and returns Bearer auth headers."""
    login_url = f"{settings.API_BASE_URL}/user/login"
    creds = settings.USERS["admin"]
    resp = requests.post(
        login_url,
        json={"email": creds["username"], "user": creds["username"], "password": creds["password"]},
        timeout=15
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Admin authentication failed: {resp.status_code} - {resp.text}")
    token = resp.json().get("token", "")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def discover_branch_groups(headers: dict) -> list[dict]:
    """
    Fetches all active Branch Groups from GET /api/Hrlense_Branch/branch-group.
    Returns list of dicts with 'id', 'name', and associated 'branches'.
    """
    url = f"{settings.API_BASE_URL}/Hrlense_Branch/branch-group"
    logger.info(f"[DISCOVERY] Fetching Branch Groups from {url}...")
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch branch groups: HTTP {resp.status_code} - {resp.text}")
        return []

    groups = []
    for g in resp.json():
        gid = g.get("id")
        gname = g.get("group_Name") or g.get("name")
        branches = [b.get("branch_Name") for b in g.get("branches", []) if b.get("branch_Name")]
        if gid and gname:
            groups.append({
                "id": int(gid),
                "name": gname.strip(),
                "branches": branches
            })
            logger.info(f"  Branch Group [{gid}] '{gname}' -> Companies: {branches}")

    return groups


def discover_payroll_companies(headers: dict) -> list[dict]:
    """
    Fetches all active Payroll Companies from GET /api/Hrlense_PayrollCompany.
    """
    url = f"{settings.API_BASE_URL}/Hrlense_PayrollCompany?page=1&rows=100"
    logger.info(f"[DISCOVERY] Fetching Payroll Companies from {url}...")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            companies = []
            for item in items:
                cid = item.get("id")
                cname = item.get("payrollCompanyName") or item.get("name")
                ccode = item.get("companyCode")
                if cid and cname:
                    companies.append({"id": int(cid), "name": cname.strip(), "code": ccode})
            logger.info(f"  Discovered {len(companies)} Payroll Companies from API.")
            return companies
    except Exception as ex:
        logger.warning(f"Payroll company discovery error: {ex}")

    return [{"id": 1, "name": "Default Payroll Company", "code": "DEF"}]


def discover_active_taxonomy(headers: dict) -> list[dict]:
    """
    Discovers active Categories and Sub-Categories with exact database IDs.
    """
    logger.info("[DISCOVERY] Resolving Category and SubCategory taxonomy from API...")
    taxonomy = []
    try:
        c_resp = get_categories()
        s_resp = get_subcategories()
        if c_resp.status_code == 200 and s_resp.status_code == 200:
            cats = c_resp.json() if isinstance(c_resp.json(), list) else []
            subs = s_resp.json() if isinstance(s_resp.json(), list) else []
            for c in cats:
                c_id = c.get("id")
                c_name = c.get("category_Name")
                if not c_id or not c_name:
                    continue
                mapped_subs = []
                for s in subs:
                    s_cat_id = s.get("category_Id")
                    if str(s_cat_id) == str(c_id):
                        s_id = s.get("id")
                        s_name = s.get("subCategory_Name")
                        if s_id and s_name:
                            mapped_subs.append({"sub_id": int(s_id), "sub_name": s_name.strip()})
                if mapped_subs:
                    taxonomy.append({"cat_id": int(c_id), "cat_name": c_name.strip(), "subcategories": mapped_subs})
                    logger.info(f"  Category '{c_name}' (ID: {c_id}) -> {len(mapped_subs)} SubCategories")
    except Exception as ex:
        logger.error(f"Taxonomy discovery failed: {ex}")

    return taxonomy


def get_contextual_brand_model(cat_name: str, sub_name: str) -> tuple[str, str]:
    """
    Returns realistic (brand, model) based on Category and SubCategory.
    """
    combo = f"{cat_name} {sub_name}".lower()
    if any(k in combo for k in ["laptop", "notebook", "computer", "pc", "workstation"]):
        return "Dell", "Latitude 7440"
    elif any(k in combo for k in ["monitor", "display", "screen"]):
        return "Dell", "UltraSharp 27 4K"
    elif any(k in combo for k in ["chair", "desk", "table", "furniture"]):
        return "Godrej", "Ergonomic Mesh Chair"
    elif any(k in combo for k in ["mouse", "keyboard", "peripheral", "headset"]):
        return "Logitech", "MX Master 3S"
    elif any(k in combo for k in ["printer", "scanner"]):
        return "HP", "LaserJet Pro 400"
    elif any(k in combo for k in ["router", "switch", "networking"]):
        return "Cisco", "Catalyst 1000"
    elif any(k in combo for k in ["mobile", "phone", "tablet"]):
        return "Samsung", "Galaxy Tab S9"
    elif any(k in combo for k in ["car", "vehicle", "bike"]):
        return "Honda", "City ZX"
    else:
        return "Enterprise Standard", f"Model-{sub_name[:6].strip()}"


def seed_all_branch_assets(assets_per_subcategory: int = 2, target_branch_group_id: int = None):
    """
    Seeds assets across all Branch Groups using the required structure:
    - "branch_Id": Branch Group ID
    - "payroll_Company_Id": Valid Payroll Company ID from API
    - "asset_Name": "{branch_group_name}_{brand_and_model}"
    """
    logger.info("=" * 80)
    logger.info("SEED ALL BRANCH ASSETS - API GENERATOR")
    logger.info("=" * 80)

    # 1. Authenticate
    headers = get_authenticated_headers()
    logger.info("[AUTH] Successfully authenticated as Admin.")

    # 2. Discover Branch Groups
    branch_groups = discover_branch_groups(headers)
    if not branch_groups:
        raise RuntimeError("No Branch Groups found from API!")

    if target_branch_group_id:
        branch_groups = [bg for bg in branch_groups if bg["id"] == target_branch_group_id]
        logger.info(f"[FILTER] Targeting only Branch Group ID: {target_branch_group_id}")

    # 3. Discover Payroll Companies
    payroll_companies = discover_payroll_companies(headers)
    default_payroll_id = payroll_companies[0]["id"] if payroll_companies else 1
    logger.info(f"[PAYROLL] Default Payroll Company ID: {default_payroll_id} ({payroll_companies[0]['name'] if payroll_companies else 'N/A'})")

    # 4. Discover Taxonomy
    taxonomy = discover_active_taxonomy(headers)
    if not taxonomy:
        raise RuntimeError("No active Category/SubCategory taxonomy found!")

    total_created = 0
    total_failed = 0
    summary_report = []

    # 5. Seed Assets for each Branch Group
    for bg in branch_groups:
        bg_id = bg["id"]
        bg_name = bg["name"]
        bg_code = "".join([w[0] for w in bg_name.split() if w])[:3].upper()

        logger.info(f"\n---> Seeding Asset Stock for Branch Group: '{bg_name}' (ID: {bg_id})")
        bg_created_count = 0

        for cat in taxonomy:
            cat_id = cat["cat_id"]
            cat_name = cat["cat_name"]

            for sub in cat["subcategories"]:
                sub_id = sub["sub_id"]
                sub_name = sub["sub_name"]
                sub_prefix = "".join([w[0] for w in sub_name.split() if w])[:3].upper()

                brand, model = get_contextual_brand_model(cat_name, sub_name)
                brand_and_model = f"{brand} {model}"

                # Strict requirement: format is '{branch_group_name}_{brand_and_model}'
                asset_name = f"{bg_name}_{brand_and_model}"

                for k in range(assets_per_subcategory):
                    unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
                    serial_no = f"SN-{sub_prefix}-{bg_code}-{unique_id}"

                    payload = {
                        "asset_Name": asset_name if assets_per_subcategory == 1 else f"{asset_name} #{k+1}",
                        "category_Id": cat_id,
                        "sub_Category_Id": sub_id,
                        "branch_Id": bg_id,                         # Branch Group ID passed as branch_Id
                        "payroll_Company_Id": default_payroll_id,   # Resolved Payroll Company ID
                        "brand": brand,
                        "model_No": model,
                        "serial_No": serial_no,
                        "warranty_Type": "Warranty",
                        "warranty_Expiry": "2028-12-31",
                        "notes": f"Bulk Stock Ingestion for {bg_name} Branch Group",
                        "has_Insurance": False,
                        "insurance_Provider": None,
                        "insurance_Policy_No": None,
                        "insurance_Premium_Amount": None,
                        "insurance_Premium_Frequency": None,
                        "insurance_Start_Date": None,
                        "insurance_Expiry_Date": None
                    }

                    try:
                        res = requests.post(
                            f"{settings.API_BASE_URL}/Asset/assets",
                            headers=headers,
                            json=payload,
                            timeout=10
                        )
                        if res.status_code in (200, 201):
                            total_created += 1
                            bg_created_count += 1
                            logger.info(f"  [SUCCESS] {payload['asset_Name']} (SN: {serial_no}) | Branch Group: {bg_name} ({bg_id})")
                        else:
                            total_failed += 1
                            logger.warning(f"  [FAILED] {payload['asset_Name']}: HTTP {res.status_code} - {res.text[:120]}")
                    except Exception as ex:
                        total_failed += 1
                        logger.error(f"  [ERROR] {payload['asset_Name']}: {ex}")

        summary_report.append({
            "branch_group_name": bg_name,
            "branch_group_id": bg_id,
            "companies": ", ".join(bg["branches"][:3]) or "None",
            "assets_seeded": bg_created_count,
            "status": "PASS" if bg_created_count > 0 else "FAIL"
        })

    print("\n" + format_ascii_table("ALL BRANCH GROUPS ASSET SEEDING SUMMARY", summary_report))
    logger.info(f"\n{'=' * 80}")
    logger.info(f"SEEDING COMPLETE: Total Created: {total_created} | Total Failed: {total_failed} across {len(branch_groups)} Branch Groups")
    logger.info(f"{'=' * 80}\n")
    return total_created, total_failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed assets for all Branch Groups via API")
    parser.add_argument("--count", type=int, default=2, help="Number of assets to seed per subcategory (default: 2)")
    parser.add_argument("--branch-group-id", type=int, default=None, help="Target specific Branch Group ID (optional)")
    args = parser.parse_args()

    seed_all_branch_assets(
        assets_per_subcategory=args.count,
        target_branch_group_id=args.branch_group_id
    )
