import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import random
import logging
import requests
from core.config import settings
from pages.base_page import format_ascii_table
from playwright.sync_api import sync_playwright
from utils.api.asset.asset_api import get_categories, get_subcategories

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def discover_active_taxonomy(headers: dict = None) -> list[dict]:
    """
    Discovers active Categories and Sub-Categories with exact database IDs.
    First tries REST API endpoints via utils.api.asset_api, then falls back to UI discovery.
    """
    logger.info("[DYNAMIC DISCOVERY] Resolving Category and SubCategory database IDs from STG...")
    taxonomy = []
    
    # 1. Direct API Discovery via verified AssesstsMaster endpoints
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
                            mapped_subs.append({"sub_id": int(s_id), "sub_name": s_name})
                if mapped_subs:
                    taxonomy.append({"cat_id": int(c_id), "cat_name": c_name, "subcategories": mapped_subs})
                    logger.info(f"  [API DISCOVERY] Mapped Category '{c_name}' (ID: {c_id}) -> {len(mapped_subs)} SubCategories: {[s['sub_name'] for s in mapped_subs]}")
            if taxonomy:
                return taxonomy
    except Exception as ex:
        logger.warning(f"AssesstsMaster API discovery note: {ex}")

    # 2. UI Discovery Fallback (using msedge channel)
    logger.info("[UI DISCOVERY FALLBACK] Launching Edge browser to inspect modal dropdowns...")
    with sync_playwright() as p:
        try:
            try:
                browser = p.chromium.launch(channel="msedge", headless=True)
            except Exception:
                browser = p.chromium.launch(headless=False)
                
            page = browser.new_page()
            
            page.goto(f"{settings.BASE_URL}/login")
            page.fill("input[name='user'], input[name='username'], input[placeholder*='Username']", settings.USERS["admin"]["username"])
            page.fill("input[name='password'], input[placeholder*='Password']", settings.USERS["admin"]["password"])
            page.click("button[type='submit']")
            page.wait_for_timeout(3000)
            
            page.goto(f"{settings.BASE_URL}/asset-entry")
            page.wait_for_timeout(3000)
            
            btn = page.locator("button:has-text('Add Manual'), button:has-text('Add Asset')").first
            if btn.is_visible(timeout=5000):
                btn.click()
                page.wait_for_timeout(1500)
                
                modal = page.locator(".chakra-modal__content, [role='dialog']").first
                cat_select = modal.locator("//div[./label[contains(text(), 'Category') and not(contains(text(), 'Sub'))]]//select").first
                if not cat_select.is_visible(timeout=1000):
                    cat_select = modal.get_by_label("Category*", exact=False).first
                
                cat_opts = cat_select.locator("option").all()
                for opt in cat_opts:
                    val = opt.get_attribute("value")
                    txt = opt.inner_text().strip()
                    if val and val.strip() != "" and "select" not in txt.lower():
                        try:
                            c_id = int(val)
                            cat_select.select_option(value=val)
                            page.wait_for_timeout(600)
                            
                            sub_select = modal.locator("//div[./label[contains(text(), 'Sub Category')]]//select").first
                            if not sub_select.is_visible(timeout=1000):
                                sub_select = modal.get_by_label("Sub Category", exact=False).first
                            
                            sub_opts = sub_select.locator("option").all()
                            subs = []
                            for s_opt in sub_opts:
                                s_val = s_opt.get_attribute("value")
                                s_txt = s_opt.inner_text().strip()
                                if s_val and s_val.strip() != "" and "select" not in s_txt.lower():
                                    try:
                                        subs.append({"sub_id": int(s_val), "sub_name": s_txt})
                                    except ValueError:
                                        pass
                            
                            if subs:
                                taxonomy.append({
                                    "cat_id": c_id,
                                    "cat_name": txt,
                                    "subcategories": subs
                                })
                                logger.info(f"  [UI DISCOVERY] Mapped Category '{txt}' (ID: {c_id}) -> {len(subs)} SubCategories: {[s['sub_name'] for s in subs]}")
                        except ValueError:
                            pass
            browser.close()
        except Exception as ex:
            logger.warning(f"UI discovery note: {ex}")
            
    return taxonomy


def seed_assets_for_all_branches_api(assets_per_subcategory: int = 1):
    """
    High-Speed Bulk Asset Generator for ALL Branches via POST /api/Asset/assets.
    Seeds assets across all 3 sub-categories for every active category.
    """
    logger.info("="*80)
    logger.info("STARTING DYNAMIC BULK ASSET SEEDING FOR ALL BRANCHES VIA REST API")
    logger.info("="*80)

    # 1. Authenticate via REST API
    login_url = f"{settings.API_BASE_URL}/user/login"
    creds = settings.USERS["admin"]
    try:
        login_resp = requests.post(login_url, json={"email": creds["username"], "user": creds["username"], "password": creds["password"]}, timeout=15)
        token = login_resp.json().get("token", "")
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("[AUTH SUCCESS] Obtained Bearer token for asset seeding.")
    except Exception as e:
        logger.error(f"[AUTH FAILED] {e}")
        return

    # 2. Discover STG Database Taxonomy (Category IDs + SubCategory IDs)
    taxonomy = discover_active_taxonomy(headers)
    if not taxonomy:
        logger.error("[SEEDING ABORTED] Could not resolve active taxonomy from database!")
        return

    # 3. Fetch Branches via REST API
    branches = []
    try:
        b_resp = requests.get(f"{settings.API_BASE_URL}/Hrlense_Branch", headers=headers, params={"rows": 1000}, timeout=15)
        if b_resp.status_code == 200:
            b_data = b_resp.json()
            branches = b_data if isinstance(b_data, list) else (b_data.get("data", []) if isinstance(b_data, dict) else [])
    except Exception as e:
        logger.warning(f"Error fetching branches via API: {e}")

    if not branches:
        branches = [
            {"id": 1, "branch_Name": "JOB- (VARANASI)"},
            {"id": 2, "branch_Name": "VIZ- (AGRA)"},
            {"id": 3, "branch_Name": "TEK- (NOIDA)"},
            {"id": 4, "branch_Name": "NEX- (GREATER NOIDA)"},
            {"id": 5, "branch_Name": "TEC- (JAIPUR)"},
            {"id": 6, "branch_Name": "TEK- (LUCKNOW)"},
            {"id": 7, "branch_Name": "VYZ- (MEERUT)"},
            {"id": 8, "branch_Name": "JOB- (RANCHI)"},
            {"id": 9, "branch_Name": "TEK- (BHUBANESWAR)"}
        ]

    logger.info(f"\nResolved {len(branches)} Branches across organization for asset stock generation.")

    total_created = 0
    total_failed = 0
    branch_summary = []

    for b in branches:
        branch_id = b.get("id") or b.get("branch_Id") or b.get("branchId")
        branch_name = b.get("branch_Name") or b.get("name") or f"Branch {branch_id}"
        branch_code = "".join([part[0] for part in branch_name.replace("(", "").replace(")", "").split() if part])[:3].upper()

        logger.info(f"\n---> Seeding Asset Stock for Branch: '{branch_name}' (ID: {branch_id})")
        branch_count = 0

        for cat in taxonomy:
            cat_id = cat["cat_id"]

            for sub in cat["subcategories"]:
                sub_id = sub["sub_id"]
                sub_name = sub["sub_name"]
                prefix = sub_name[:3].upper()

                for k in range(assets_per_subcategory):
                    unique_suffix = f"{int(time.time())}_{random.randint(100, 999)}"
                    serial_no = f"SN-{prefix}-{branch_code}-{unique_suffix}"
                    asset_name = f"Enterprise {sub_name} #{k+1}"

                    payload = {
                        "asset_Name": asset_name,
                        "category_Id": cat_id,
                        "sub_Category_Id": sub_id,
                        "branch_Id": branch_id,
                        "payroll_Company_Id": 1,
                        "brand": "Enterprise Standard",
                        "model_No": f"Model-{sub_name[:5]}",
                        "serial_No": serial_no,
                        "warranty_Type": "Warranty",
                        "warranty_Expiry": "2028-12-31",
                        "notes": f"Bulk Stock Ingestion for {branch_name}",
                        "has_Insurance": False,
                        "insurance_Provider": None,
                        "insurance_Policy_No": None,
                        "insurance_Premium_Amount": None,
                        "insurance_Premium_Frequency": None,
                        "insurance_Start_Date": None,
                        "insurance_Expiry_Date": None
                    }

                    try:
                        res = requests.post(f"{settings.API_BASE_URL}/Asset/assets", headers=headers, json=payload, timeout=10)
                        if res.status_code in (200, 201):
                            total_created += 1
                            branch_count += 1
                            logger.info(f"  [SUCCESS] {branch_name} | {asset_name} ({serial_no})")
                        else:
                            logger.warning(f"  [FAILED] {branch_name} | {asset_name} ({serial_no}): Status {res.status_code} - {res.text[:100]}")
                            total_failed += 1
                    except Exception as ex:
                        logger.warning(f"  [EXCEPT] {branch_name} | {asset_name} ({serial_no}): {ex}")
                        total_failed += 1

        branch_summary.append({
            "branch_name": branch_name,
            "branch_id": branch_id,
            "assets_created": branch_count,
            "status": "COMPLETED" if branch_count > 0 else "ATTEMPTED"
        })

    print("\n" + format_ascii_table("MULTI-BRANCH BULK ASSET SEEDING SUMMARY", branch_summary))
    logger.info(f"\n{'='*80}\n[BULK ASSET SEEDING COMPLETE] Successfully created {total_created} assets across {len(branches)} branches! (Failed: {total_failed})\n{'='*80}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    seed_assets_for_all_branches_api(count)
