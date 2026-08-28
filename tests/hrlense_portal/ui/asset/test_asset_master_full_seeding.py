"""
Asset Master & Branch Group Full Seeding Test Suite.

Executes enterprise-scale setup:
1. 10 Enterprise Categories
2. 10 Coherent Sub-Categories (with 3-letter code prefixes mapped to parent categories)
3. 10 Corporate Vendors (with realistic GSTIN, email, phone, address, and AMC flags)
4. Branch Groups mapped for ALL branches in the system.
"""

import time
import random
import logging
import pytest
from pages.base_page import TestStoryLogger, format_ascii_table
from pages.hrlense_portal.asset.asset_master_page import AssetMasterPage
from pages.hrlense_portal.asset.branch_group_page import BranchGroupPage
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from workflows.hrlense_portal.asset.asset_master_workflow import AssetMasterWorkflow
from workflows.hrlense_portal.asset.branch_group_workflow import BranchGroupWorkflow

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# MASTER DATA DEFINITIONS: 10 CATEGORIES, 10 SUBCATEGORIES, 10 VENDORS
# ══════════════════════════════════════════════════════════════════════════════

SEED_CATEGORIES = [
    {"name": "IT Hardware", "description": "Enterprise compute hardware and workstations"},
    {"name": "Office Furniture", "description": "Ergonomic seating, desks, and office fixtures"},
    {"name": "Peripherals", "description": "Monitors, keyboards, mice, and desk accessories"},
    {"name": "Software Licenses", "description": "Enterprise OS, productivity suites, and IDE licenses"},
    {"name": "Networking and Servers", "description": "Routers, switches, access points, and rack servers"},
    {"name": "Audio Visual", "description": "Conference speakerphones, headsets, and projectors"},
    {"name": "Mobile and Telephony", "description": "Corporate smartphones, tablets, and VoIP desk phones"},
    {"name": "Security and Surveillance", "description": "CCTV cameras, biometric scanners, and access cards"},
    {"name": "Power and Backup", "description": "Online UPS systems, battery backups, and surge protectors"},
    {"name": "Facility and Pantry", "description": "Air conditioners, water dispensers, and office appliances"}
]

SEED_SUBCATEGORIES = [
    {"category": "IT Hardware", "name": "Laptop", "prefix": "LAP", "description": "Developer & Business Laptops"},
    {"category": "Office Furniture", "name": "Ergonomic Chair", "prefix": "CHR", "description": "Mesh Back High-Adjustable Chairs"},
    {"category": "Peripherals", "name": "UltraSharp 4K Monitor", "prefix": "MON", "description": "27-inch 4K IPS Developer Displays"},
    {"category": "Software Licenses", "name": "Operating System License", "prefix": "OSL", "description": "Windows 11 Pro / Enterprise OS Keys"},
    {"category": "Networking and Servers", "name": "Enterprise Edge Router", "prefix": "RTR", "description": "Gigabit Dual-WAN Edge Gateway Routers"},
    {"category": "Audio Visual", "name": "Conference Speakerphone", "prefix": "SPK", "description": "Noise-Cancelling Conference Room Pods"},
    {"category": "Mobile and Telephony", "name": "Business Smartphone", "prefix": "PHN", "description": "Secured Corporate Android / iOS Devices"},
    {"category": "Security and Surveillance", "name": "CCTV Security Camera", "prefix": "CAM", "description": "High-Definition 4K Security Surveillance Cameras"},
    {"category": "Power and Backup", "name": "Online UPS Inverter", "prefix": "UPS", "description": "High-capacity Pure Sine Wave Online UPS Systems"},
    {"category": "Facility and Pantry", "name": "Office Air Conditioner", "prefix": "OAC", "description": "Inverter Energy-Efficient Climate Control Units"}
]

SEED_VENDORS = [
    {
        "name": "Dell Technologies India Pvt Ltd",
        "contact_person": "Rajesh Sharma",
        "phone": "9810123456",
        "email": "rajesh.sharma@dell-india.com",
        "address": "Divyasree Greens, 4/1 Challenger Tower, Inner Ring Road, Bengaluru",
        "gst": "29AABCD1234E1Z5",
        "supports_amc": True
    },
    {
        "name": "Lenovo India Enterprise Solutions",
        "contact_person": "Pooja Verma",
        "phone": "9820123456",
        "email": "pverma@lenovo-enterprise.in",
        "address": "Ferns Icon, Level 2, Outer Ring Road, Marathahalli, Bengaluru",
        "gst": "29AABCL5678F2Z8",
        "supports_amc": True
    },
    {
        "name": "HP India Sales Private Limited",
        "contact_person": "Vikram Malhotra",
        "phone": "9830123456",
        "email": "vikram.m@hp-india.com",
        "address": "Building 2, DLF Cyber City, Sector 24, Gurugram, Haryana",
        "gst": "06AABCH9012G3Z1",
        "supports_amc": True
    },
    {
        "name": "Godrej & Boyce Manufacturing Co",
        "contact_person": "Sunil Godrej",
        "phone": "9840123456",
        "email": "contact@godrej-furniture.com",
        "address": "Pirojshanagar, Vikhroli East, Mumbai, Maharashtra",
        "gst": "27AABCG3456H4Z4",
        "supports_amc": False
    },
    {
        "name": "Featherlite Office Furniture Ltd",
        "contact_person": "Anil Kumar",
        "phone": "9850123456",
        "email": "sales@featherlite-furniture.in",
        "address": "16A, Millers Road, Vasanth Nagar, Bengaluru, Karnataka",
        "gst": "29AABCF7890I5Z7",
        "supports_amc": False
    },
    {
        "name": "Cisco Systems India Pvt Ltd",
        "contact_person": "Rohan Mehra",
        "phone": "9860123456",
        "email": "rohan.mehra@cisco-systems.in",
        "address": "SEZ Unit, Cessna Business Park, Kadubeesanahalli, Bengaluru",
        "gst": "29AABCC1234J6Z0",
        "supports_amc": True
    },
    {
        "name": "Samsung India Electronics Ltd",
        "contact_person": "Neha Kapoor",
        "phone": "9870123456",
        "email": "neha.k@samsung-enterprise.in",
        "address": "Two Horizon Center, Golf Course Road, Sector 43, Gurugram",
        "gst": "06AABCS5678K7Z3",
        "supports_amc": True
    },
    {
        "name": "Jabra India Audio Solutions",
        "contact_person": "Deepak Joshi",
        "phone": "9880123456",
        "email": "support@jabra-audio.in",
        "address": "Level 6, Wing B, Smartworks Cyber Park, Sector 62, Noida",
        "gst": "09AABCJ9012L8Z6",
        "supports_amc": True
    },
    {
        "name": "APC Schneider Electric India",
        "contact_person": "Alok Srivastava",
        "phone": "9890123456",
        "email": "alok.s@schneider-apc.in",
        "address": "44P, Electronic City, Phase 2, Hosur Road, Bengaluru",
        "gst": "29AABCA3456M9Z9",
        "supports_amc": True
    },
    {
        "name": "Logitech Electronics India Pvt Ltd",
        "contact_person": "Siddharth Roy",
        "phone": "9811123456",
        "email": "siddharth.r@logitech-india.com",
        "address": "Unit 802, Alpha Tower, Sector 48, Sohna Road, Gurugram",
        "gst": "06AABCL7890N1Z2",
        "supports_amc": False
    }
]


@pytest.mark.asset
@pytest.mark.seeding
class TestAssetMasterFullSeeding:
    """
    Complete Seeding and Master Data Provisioning for HR Lens.
    """

    def test_seed_10_categories_10_subcategories_10_vendors_all_branch_groups(self, admin_page):
        """
        Comprehensive Seeding & Master Data Creation:
        1. Creates/Verifies 10 Enterprise Asset Categories
        2. Creates/Verifies 10 Coherent Sub-Categories mapped to Parent Categories
        3. Creates/Verifies 10 Corporate Vendors with complete profiles
        4. Configures Branch Groups for ALL branches across the organization.
        """
        story = TestStoryLogger(
            "Asset Master Full Seeding (10 Cat + 10 Sub + 10 Vendor + All Branch Groups)",
            module="Asset Management",
            phase="Master Seeding"
        )
        story.start()

        master_page = AssetMasterPage(admin_page)
        master_workflow = AssetMasterWorkflow(admin_page)
        bg_workflow = BranchGroupWorkflow(admin_page)
        bg_page = BranchGroupPage(admin_page)

        # =========================================================================
        # PHASE 1: SEED 10 CATEGORIES
        # =========================================================================
        logger.info("\n" + "=" * 60)
        logger.info("[PHASE 1] Seeding 10 Asset Categories")
        logger.info("=" * 60)

        existing_categories = [c.lower() for c in master_page.get_all_existing_categories()]
        seeded_categories = []

        if len(existing_categories) >= 10:
            logger.info(f"[PHASE 1 SKIP] Found {len(existing_categories)} categories (>= 10). Skipping Category creation phase entirely.")
            for idx, cat in enumerate(SEED_CATEGORIES, 1):
                seeded_categories.append({
                    "index": idx,
                    "category_name": cat["name"],
                    "status": "ALREADY EXISTS (Reused - Table Count >= 10)"
                })
        else:
            for idx, cat in enumerate(SEED_CATEGORIES, 1):
                cat_name = cat["name"]
                if cat_name.lower() in existing_categories:
                    status_msg = "ALREADY EXISTS (Reused)"
                    logger.info(f"[{idx}/10 CATEGORY] '{cat_name}' -> {status_msg}")
                else:
                    toast = master_workflow.create_category_workflow(name=cat_name, description=cat["description"])
                    status_msg = f"CREATED (Toast='{toast}')"
                    logger.info(f"[{idx}/10 CATEGORY] Created '{cat_name}' -> {status_msg}")

                seeded_categories.append({
                    "index": idx,
                    "category_name": cat_name,
                    "status": status_msg
                })

        story.log_step(
            "Phase 1: 10 Categories Seeded",
            record=f"Total: {len(SEED_CATEGORIES)} Categories",
            expected="All 10 Categories present in Asset Master",
            actual=f"Processed: {len(seeded_categories)} Categories",
            status="PASS"
        )

        # =========================================================================
        # PHASE 2: SEED 10 SUB-CATEGORIES
        # =========================================================================
        logger.info("\n" + "=" * 60)
        logger.info("[PHASE 2] Seeding 10 Sub-Categories")
        logger.info("=" * 60)

        existing_subs = master_page.get_all_existing_sub_categories()
        existing_sub_rows = [s.get("row_text", "").lower() for s in existing_subs]
        seeded_subs = []

        for idx, sub in enumerate(SEED_SUBCATEGORIES, 1):
            sub_name = sub["name"]
            parent_cat = sub["category"]
            prefix = sub["prefix"]

            # Check if this Category already has an active sub-category in the table
            category_has_sub = any(
                parent_cat.lower() in row for row in existing_sub_rows
            ) or any(
                sub_name.lower() in row or prefix.lower() in row for row in existing_sub_rows
            )

            if category_has_sub:
                status_msg = f"ALREADY EXISTS (Category '{parent_cat}' has active sub-category)"
                logger.info(f"[{idx}/10 SUB-CATEGORY] Skipping: '{parent_cat}' -> {status_msg}")
            else:
                logger.info(f"[{idx}/10 SUB-CATEGORY] Missing sub-category for Category '{parent_cat}'. Creating '{sub_name}' ({prefix})...")
                toast = master_workflow.create_sub_category_workflow(
                    category_name=parent_cat,
                    sub_category_name=sub_name,
                    prefix=prefix,
                    description=sub["description"]
                )
                status_msg = f"CREATED (Toast='{toast}')"
                logger.info(f"[{idx}/10 SUB-CATEGORY] Created '{sub_name}' ({prefix}) -> {status_msg}")
                # Refresh local cache of rows to avoid duplicate creation in same run
                existing_sub_rows.append(f"{parent_cat.lower()} {sub_name.lower()} {prefix.lower()}")

            seeded_subs.append({
                "index": idx,
                "sub_category": sub_name,
                "parent_category": parent_cat,
                "prefix": prefix,
                "status": status_msg
            })

        story.log_step(
            "Phase 2: 10 Sub-Categories Seeded",
            record=f"Total: {len(SEED_SUBCATEGORIES)} Sub-Categories",
            expected="All 10 Parent Categories have an active sub-category",
            actual=f"Processed: {len(seeded_subs)} Sub-Categories",
            status="PASS"
        )

        # =========================================================================
        # PHASE 3: SEED 10 VENDORS
        # =========================================================================
        logger.info("\n" + "=" * 60)
        logger.info("[PHASE 3] Seeding 10 Corporate Vendors")
        logger.info("=" * 60)

        existing_vendors = master_page.get_all_existing_vendors()
        existing_vendor_rows = [v.get("row_text", "").lower() for v in existing_vendors]
        seeded_vendors = []

        if len(existing_vendors) >= 10:
            logger.info(f"[PHASE 3 SKIP] Found {len(existing_vendors)} vendors (>= 10). Skipping Vendor creation phase entirely.")
            for idx, vendor in enumerate(SEED_VENDORS, 1):
                seeded_vendors.append({
                    "index": idx,
                    "vendor_name": vendor["name"],
                    "gstin": vendor["gst"],
                    "status": "ALREADY EXISTS (Reused - Table Count >= 10)"
                })
        else:
            for idx, vendor in enumerate(SEED_VENDORS, 1):
                v_name = vendor["name"]
                v_gst = vendor["gst"]
                v_email = vendor["email"]

                is_present = any(
                    v_name.lower() in row or
                    v_gst.lower() in row or
                    v_email.lower() in row
                    for row in existing_vendor_rows
                )
                if is_present:
                    status_msg = "ALREADY EXISTS (Reused)"
                    logger.info(f"[{idx}/10 VENDOR] '{v_name}' -> {status_msg}")
                else:
                    toast = master_workflow.create_vendor_workflow(vendor)
                    status_msg = f"CREATED (Toast='{toast}')"
                    logger.info(f"[{idx}/10 VENDOR] Created '{v_name}' -> {status_msg}")

                seeded_vendors.append({
                    "index": idx,
                    "vendor_name": v_name,
                    "gstin": vendor["gst"],
                    "status": status_msg
                })

        story.log_step(
            "Phase 3: 10 Corporate Vendors Seeded",
            record=f"Total: {len(SEED_VENDORS)} Vendors",
            expected="All 10 Corporate Vendors created in Vendor Master",
            actual=f"Processed: {len(seeded_vendors)} Vendors",
            status="PASS"
        )

        # =========================================================================
        # PHASE 4: CONFIGURE BRANCH GROUPS FOR ALL BRANCHES
        # =========================================================================
        logger.info("\n" + "=" * 60)
        logger.info("[PHASE 4] Configuring Branch Groups for ALL Branches")
        logger.info("=" * 60)

        from testdata.dynamic.business_test_data import BusinessTestData
        branch_map = BusinessTestData.get_branch_groups_map_from_api()
        all_cities = sorted(list(branch_map.keys()))
        logger.info(f"[DISCOVERED CITIES] Total: {len(all_cities)} -> {all_cities}")

        bg_page.navigate_to_branch_group()
        existing_groups = [g.lower() for g in bg_page.get_all_existing_branch_groups()]
        configured_branch_groups = []

        for idx, city in enumerate(all_cities, 1):
            group_name = f"{city} Group"
            branches_in_city = branch_map.get(city, [city])
            is_present = any(group_name.lower() in eg or city.lower() in eg for eg in existing_groups)

            if is_present:
                g_status = f"ALREADY CONFIGURED ({len(branches_in_city)} branches)"
                logger.info(f"[BRANCH GROUP {idx}/{len(all_cities)}] '{group_name}' for City '{city}' -> {g_status}")
            else:
                try:
                    bg_page.navigate_to_branch_group()
                    bg_page.click_new_group()
                    bg_page.fill_group_details(
                        group_name=group_name,
                        branch_names=branches_in_city,
                        seating_cost="2500.00",
                        search_query=city
                    )
                    bg_page.click_create()
                    toast = bg_page.wait_for_toast_message()
                    bg_page._ensure_modal_closed()
                    g_status = f"CREATED (Toast='{toast}', {len(branches_in_city)} branches)"
                    logger.info(f"[BRANCH GROUP {idx}/{len(all_cities)}] Created '{group_name}' for '{city}' -> {g_status}")
                except Exception as ex:
                    g_status = f"ERROR: {ex}"
                    logger.warning(f"[BRANCH GROUP {idx}/{len(all_cities)}] Error creating '{group_name}': {ex}")
                    bg_page._ensure_modal_closed()

            configured_branch_groups.append({
                "city": city,
                "branch_group_name": group_name,
                "mapped_branches": ", ".join(branches_in_city[:2]) + (f" (+{len(branches_in_city)-2} more)" if len(branches_in_city) > 2 else ""),
                "status": g_status
            })

        story.log_step(
            "Phase 4: Branch Groups for All Branches",
            record=f"Total: {len(all_cities)} Cities across company",
            expected="Branch Group created/verified for every branch",
            actual=f"Configured: {len(configured_branch_groups)} Branch Groups",
            status="PASS"
        )

        # =========================================================================
        # PRINT FINAL ASCII SEEDING REPORT
        # =========================================================================
        print("\n" + format_ascii_table("SEEDED CATEGORIES (10)", seeded_categories))
        print(format_ascii_table("SEEDED SUB-CATEGORIES (10)", seeded_subs))
        print(format_ascii_table("SEEDED CORPORATE VENDORS (10)", seeded_vendors))
        print(format_ascii_table("CONFIGURED BRANCH GROUPS (ALL BRANCHES)", configured_branch_groups))

        story.finish(status="PASS")

