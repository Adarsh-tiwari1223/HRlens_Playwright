import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import random
import logging
from core.config import settings
from utils.api.base_api import get, post
from pages.base_page import format_ascii_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def seed_assets_for_all_branches_api(assets_per_category: int = 5):
    """
    High-Speed Bulk Asset Generator for ALL Branches via POST /api/Asset/assets.
    Populates 5 active assets per category & sub-category for every single branch group!
    """
    logger.info("="*80)
    logger.info("STARTING HIGH-SPEED BULK ASSET SEEDING FOR ALL BRANCHES VIA API")
    logger.info("="*80)

    # 1. Fetch Branches
    try:
        branches_data = get("branch", user="admin")
        branches = branches_data if isinstance(branches_data, list) else branches_data.get("data", [])
    except Exception as e:
        logger.warning(f"Fallback fetching branches: {e}")
        branches = [
            {"id": 1, "branch_Name": "Varanasi"},
            {"id": 2, "branch_Name": "Agra"},
            {"id": 3, "branch_Name": "Noida"},
            {"id": 4, "branch_Name": "Greater Noida"},
            {"id": 5, "branch_Name": "Jaipur"},
            {"id": 6, "branch_Name": "Lucknow"},
            {"id": 7, "branch_Name": "Meerut"},
            {"id": 8, "branch_Name": "Ranchi"},
            {"id": 9, "branch_Name": "Bhubaneswar"}
        ]

    logger.info(f"Resolved {len(branches)} Branches across organization.")

    # 2. Asset Specifications across all 10 Categories
    TAXONOMY_10 = [
        {
            "cat_id": 1, "cat_name": "IT Hardware",
            "sub_id": 1, "sub_name": "Laptop", "prefix": "LAP",
            "models": [("Dell", "Latitude 7440"), ("Lenovo", "ThinkPad T14"), ("HP", "EliteBook 840"), ("Apple", "MacBook Pro 14"), ("Asus", "ExpertBook B9")]
        },
        {
            "cat_id": 2, "cat_name": "Office Furniture",
            "sub_id": 2, "sub_name": "Ergonomic Chair", "prefix": "CHR",
            "models": [("Godrej", "Executive Mesh Chair"), ("Featherlite", "Helix High-Back"), ("Steelcase", "Gesture Chair"), ("Herman Miller", "Aeron Chair"), ("Haworth", "Zody Ergonomic")]
        },
        {
            "cat_id": 3, "cat_name": "Peripherals",
            "sub_id": 3, "sub_name": "UltraSharp 4K Monitor", "prefix": "MON",
            "models": [("Dell", "UltraSharp U2723QE"), ("LG", "UltraFine 4K 27UN880"), ("Samsung", "ViewFinity S8 4K"), ("BenQ", "DesignVue PD2705U"), ("ASUS", "ProArt PA279CV")]
        },
        {
            "cat_id": 4, "cat_name": "Software Licenses",
            "sub_id": 4, "sub_name": "Operating System License", "prefix": "OSL",
            "models": [("Microsoft", "Windows 11 Pro"), ("Microsoft", "Windows 11 Enterprise"), ("RedHat", "RHEL 9 Workstation"), ("Canonical", "Ubuntu Pro Enterprise"), ("JetBrains", "All Products Pack")]
        },
        {
            "cat_id": 5, "cat_name": "Networking and Servers",
            "sub_id": 5, "sub_name": "Enterprise Edge Router", "prefix": "RTR",
            "models": [("Cisco", "Catalyst 8300 Router"), ("Juniper", "SRX345 Gateway"), ("Fortinet", "FortiGate 60F"), ("TP-Link", "Omada ER7206 Dual-WAN"), ("MikroTik", "CCR2004 Cloud Router")]
        },
        {
            "cat_id": 6, "cat_name": "Audio Visual",
            "sub_id": 6, "sub_name": "Conference Speakerphone", "prefix": "SPK",
            "models": [("Jabra", "Speak 750 Pod"), ("Poly", "Sync 40 Smart Speaker"), ("EPOS", "Expand SP 30+"), ("Anker", "PowerConf S500"), ("Bose", "Work Videobar VB1")]
        },
        {
            "cat_id": 7, "cat_name": "Mobile and Telephony",
            "sub_id": 7, "sub_name": "Business Smartphone", "prefix": "PHN",
            "models": [("Samsung", "Galaxy S23 Enterprise"), ("Apple", "iPhone 15 Corporate"), ("Google", "Pixel 8 Enterprise"), ("Motorola", "ThinkPhone Enterprise"), ("OnePlus", "12R Business Edition")]
        },
        {
            "cat_id": 8, "cat_name": "Security and Surveillance",
            "sub_id": 8, "sub_name": "CCTV Security Camera", "prefix": "CAM",
            "models": [("Hikvision", "4K Dome IP Camera"), ("Dahua", "WizSense 4MP Bullet"), ("CP Plus", "IntelliPro 5MP Dome"), ("Axis", "M3068-P Panoramic"), ("Bosch", "FLEXIDOME IP 5000i")]
        },
        {
            "cat_id": 9, "cat_name": "Power and Backup",
            "sub_id": 9, "sub_name": "Online UPS Inverter", "prefix": "UPS",
            "models": [("APC Schneider", "Smart-UPS RT 3000VA"), ("Eaton", "9PX 3000VA Online UPS"), ("Vertiv", "Liebert GXT5 2000VA"), ("Luminous", "Pro 2kVA Pure Sine"), ("Microtek", "Max Power 3kVA Online")]
        },
        {
            "cat_id": 10, "cat_name": "Facility and Pantry",
            "sub_id": 10, "sub_name": "Office Air Conditioner", "prefix": "OAC",
            "models": [("Daikin", "Inverter 2-Ton Split AC"), ("Voltas", "Vectra 1.5-Ton Inverter"), ("Blue Star", "5-Star Inverter AC"), ("Hitachi", "Toushi Split Inverter AC"), ("Mitsubishi", "Heavy Heavy Duty 2-Ton")]
        }
    ]

    total_created = 0
    total_failed = 0
    branch_summary = []

    for b in branches:
        branch_id = b.get("id") or b.get("branch_Id") or b.get("branchId")
        branch_name = b.get("branch_Name") or b.get("name") or f"Branch {branch_id}"
        branch_code = branch_name[:3].upper()

        logger.info(f"\n---> Seeding Assets for Branch: '{branch_name}' (ID: {branch_id})")
        branch_count = 0

        for tax in TAXONOMY_10:
            models_to_create = tax["models"][:assets_per_category]
            for brand, model in models_to_create:
                unique_suffix = f"{int(time.time())}_{random.randint(100, 999)}"
                serial_no = f"SN-{tax['prefix']}-{branch_code}-{unique_suffix}"
                asset_name = f"{brand} {model}"

                payload = {
                    "asset_Name": asset_name,
                    "category_Id": tax["cat_id"],
                    "sub_Category_Id": tax["sub_id"],
                    "branch_Id": branch_id,
                    "payroll_Company_Id": random.randint(1, 10),
                    "brand": brand,
                    "model_No": model,
                    "serial_No": serial_no,
                    "warranty_Type": "Warranty",
                    "warranty_Expiry": "2028-12-31",
                    "notes": f"API Bulk Ingestion for {branch_name}",
                    "has_Insurance": False,
                    "insurance_Provider": None,
                    "insurance_Policy_No": None,
                    "insurance_Premium_Amount": None,
                    "insurance_Premium_Frequency": None,
                    "insurance_Start_Date": None,
                    "insurance_Expiry_Date": None
                }

                try:
                    res = post("Asset/assets", user="admin", payload=payload)
                    total_created += 1
                    branch_count += 1
                except Exception as ex:
                    logger.warning(f"  [FAILED] {branch_name} | {asset_name} ({serial_no}): {ex}")
                    total_failed += 1

        branch_summary.append({
            "branch_name": branch_name,
            "branch_id": branch_id,
            "assets_seeded": branch_count,
            "status": "COMPLETED"
        })

    print("\n" + format_ascii_table("MULTI-BRANCH BULK ASSET SEEDING SUMMARY", branch_summary))
    logger.info(f"\n{'='*80}\n[BULK SEEDING COMPLETE] Successfully created {total_created} assets across {len(branches)} branches! (Failed: {total_failed})\n{'='*80}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    seed_assets_for_all_branches_api(count)
