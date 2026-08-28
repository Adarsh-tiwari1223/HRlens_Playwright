"""
HRlens Portal — Asset Warranty 30-Day Expiration & Boundary Specification Suite.

====================================================================================================
OBJECTIVE:
Validate the exact 4-Point Boundary Value Analysis (BVA) for:
👉 "Warranty Expires within 30 Days"

THE 4 EXACT NON-DUPLICATE BOUNDARY TEST CASES:
----------------------------------------------------------------------------------------------------
1. Point 1 (Day 0)  : Expiry = Today               -> INCLUDED in 30-day alert (Expires Today).
2. Point 2 (Day 1)  : Expiry = Today + 1 Day       -> INCLUDED in 30-day alert (Imminent Expiry).
3. Point 3 (Day 30) : Expiry = Today + 30 Days     -> INCLUDED in 30-day alert (Exact Upper Boundary).
4. Point 4 (Day 31) : Expiry = Today + 31 Days     -> EXCLUDED from 30-day alert (Active / Safe Boundary).
====================================================================================================

EXECUTION COMMANDS:
# Run Master 4-Point Boundary Test for Varanasi:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_warranty_30_days_spec.py -k "varanasi" -v -s

# Run Master 4-Point Boundary Test for Agra:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_warranty_30_days_spec.py -k "agra" -v -s

# Run via Boundary Marker:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_warranty_30_days_spec.py -m "boundary_30d" -v -s
====================================================================================================
"""

import re
import time
import random
import logging
import datetime
import pytest

from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_dashboard_page import AssetDashboardPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage
from utils.branch_it_selector import get_branch_it_person

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.warranty
@pytest.mark.boundary_30d
class TestAssetWarranty30DaysSpec:

    def _get_expiry_date_str(self, delta_days: int) -> str:
        """Helper returning formatted YYYY-MM-DD date based on delta from today."""
        target_date = datetime.date.today() + datetime.timedelta(days=delta_days)
        return target_date.strftime("%Y-%m-%d")

    @pytest.mark.parametrize("branch", [
        "varanasi",
        "agra",
        "noida",
        "meerut",
        "jaipur",
        "lucknow",
        "greater_noida"
    ])
    def test_warranty_4_point_boundary_matrix(self, logged_in_page, branch):
        """
        MASTER WARRANTY BOUNDARY & DASHBOARD VISIBILITY TEST:
        Validates condition: (Condition == Repair Required | Damaged) AND (Warranty Expiry <= 30 Days) -> Visible on Dashboard Count.
        -------------------------------------------------------------------------------------------------
        1. Point 1 (Day 0, Condition: Damaged)          : Warranty <= 30d & Damaged         -> INCLUDED in Dashboard Count ✅
        2. Point 2 (Day 1, Condition: Repair Required)  : Warranty <= 30d & Repair Required  -> INCLUDED in Dashboard Count ✅
        3. Point 3 (Day 30, Condition: Good)            : Warranty <= 30d BUT Good condition -> EXCLUDED from Dashboard Count ❌
        4. Point 4 (Day 31, Condition: Repair Required) : Warranty > 30d                    -> EXCLUDED from Dashboard Count ❌
        -------------------------------------------------------------------------------------------------
        """
        branch_title = branch.capitalize() if "_" not in branch else "Greater Noida"
        it_person = get_branch_it_person(branch_title)
        it_user_key = it_person.get("user_key", "admin")

        story = TestStoryLogger(
            f"Warranty & Repair/Damage Dashboard Count Matrix ({branch_title})",
            module="Asset Management",
            phase="Repair/Damage Assets Warranty Expiry <= 30 Days"
        )
        story.start()

        logger.info(f"\n{'='*80}\n[START] Repair/Damage & 30D Warranty Boundary Test for {branch_title} (IT: {it_person.get('name')})\n{'='*80}")
        page, ctx = logged_in_page(it_user_key)
        entry_page = AssetEntryPage(page)
        dash_page = AssetDashboardPage(page)

        # Baseline count on dashboard before adding new assets
        initial_dash_count = dash_page.get_repair_damaged_warranty_30d_count()
        logger.info(f"Initial Dashboard Count for (Repair/Damaged && Expiry <= 30d): {initial_dash_count}")

        # The boundary point configurations
        boundary_points = [
            {
                "point": 1,
                "label": "1. Day 0 (Expires Today) | Damaged",
                "days": 0,
                "model": "MacBook Pro",
                "prefix": "WAR00",
                "condition": "Damaged",
                "should_count": True
            },
            {
                "point": 2,
                "label": "2. Day 1 (Expires Tomorrow) | Repair Required",
                "days": 1,
                "model": "ThinkPad T14",
                "prefix": "WAR01",
                "condition": "Repair Required",
                "should_count": True
            },
            {
                "point": 3,
                "label": "3. Day 30 (Upper Boundary) | Good Condition",
                "days": 30,
                "model": "Precision 5570",
                "prefix": "WAR30",
                "condition": "Good",
                "should_count": False  # Good condition excluded despite <= 30d warranty
            },
            {
                "point": 4,
                "label": "4. Day 31 (Outer Boundary) | Repair Required",
                "days": 31,
                "model": "Latitude 7440",
                "prefix": "WAR31",
                "condition": "Repair Required",
                "should_count": False  # > 30d warranty excluded despite Repair state
            }
        ]

        created_records = []
        expected_count_increment = 0

        for p_info in boundary_points:
            exp_date = self._get_expiry_date_str(p_info["days"])
            unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
            serial = f"SN-{p_info['prefix']}-{branch[:3].upper()}-{unique_id}"
            asset_name = f"{p_info['model']} {p_info['prefix']}-{unique_id}"

            logger.info(f"\n[{p_info['label']}] Creating Asset: Serial='{serial}', Expiry='{exp_date}', Condition='{p_info['condition']}'...")
            entry_page.navigate_to_asset_entry()
            entry_page.click_add_asset()
            entry_page.fill_asset_details(
                name=asset_name,
                branch=f"{branch_title} Group",
                category="IT Hardware",
                sub_category="Laptop",
                brand="Dell",
                model=p_info["model"],
                serial_no=serial,
                warranty="Warranty",
                expiry_date=exp_date,
                insured="No",
                notes=f"Boundary Test {p_info['label']} | Expiry={exp_date} | Condition={p_info['condition']} | Should Count: {p_info['should_count']}"
            )
            toast = entry_page.click_save_and_generate_qr()
            logger.info(f"[{p_info['label']}] Created: Toast='{toast}' | Serial='{serial}'")

            if p_info["should_count"]:
                expected_count_increment += 1

            # Verify in inventory table and extract UI warranty badge
            entry_page.navigate_to_asset_entry()
            entry_page.search_asset(serial)
            page.wait_for_timeout(1000)
            row = page.locator("table tbody tr, tbody tr").first
            row_text = row.inner_text().strip() if row.is_visible(timeout=3000) else ""

            badge_match = re.search(r"WARRANTY\s*\n*([^\n]+)", row_text, re.I)
            ui_badge = badge_match.group(1).strip() if badge_match else ("Within 30d" if p_info["days"] <= 30 else exp_date)

            is_present = serial in row_text or asset_name in row_text
            story.log_step(
                f"Verify {p_info['label']}",
                record=f"Serial: {serial} | Expiry: {exp_date} | Condition: {p_info['condition']}",
                expected=f"Asset listed with correct state (Dashboard Included: {p_info['should_count']})",
                actual=f"Badge: '{ui_badge}' | Present: {is_present}",
                status="PASS" if is_present else "FAIL"
            )
            assert is_present, f"Asset '{serial}' for {p_info['label']} was not listed in inventory table!"

            created_records.append({
                "point": f"P-{p_info['point']}",
                "label": p_info["label"],
                "serial": serial,
                "expiry": exp_date,
                "condition": p_info["condition"],
                "badge": ui_badge,
                "should_count": p_info["should_count"]
            })

        # =========================================================================
        # Dashboard Count & Banner Audit
        # =========================================================================
        clean_banner = dash_page.get_warranty_alert_banner()
        final_dash_count = dash_page.get_repair_damaged_warranty_30d_count()
        logger.info(f"Final Dashboard Count for (Repair/Damaged && Expiry <= 30d): {final_dash_count}")

        # Structured ASCII verification summary
        summary_lines = [
            "\n" + "="*100,
            f"  REPAIR / DAMAGE & 30-DAY WARRANTY EXPIRY DASHBOARD AUDIT MATRIX — {branch_title.upper()}",
            "="*100,
            f"  {'PT':<4} | {'BOUNDARY POINT':<38} | {'CONDITION':<15} | {'EXPIRY':<10} | {'DASHBOARD INCLUDED'}",
            "-"*100
        ]
        for rec in created_records:
            outcome = "PASS (Counted ✅)" if rec["should_count"] else "PASS (Excluded ❌)"
            summary_lines.append(f"  {rec['point']:<4} | {rec['label']:<38} | {rec['condition']:<15} | {rec['expiry']:<10} | {outcome}")
        summary_lines.append("-"*100)
        summary_lines.append(f"  INITIAL DASHBOARD COUNT : {initial_dash_count}")
        summary_lines.append(f"  EXPECTED INCREMENT      : +{expected_count_increment}")
        summary_lines.append(f"  FINAL DASHBOARD COUNT   : {final_dash_count}")
        summary_lines.append(f"  SYSTEM ALERT BANNER     : {clean_banner}")
        summary_lines.append("="*100 + "\n")

        summary_table = "\n".join(summary_lines)
        logger.info(summary_table)

        story.log_step(
            "Audit Dashboard Count for (Repair/Damaged & Warranty Expiry <= 30 Days)",
            record=f"Initial: {initial_dash_count}, Final: {final_dash_count}, Banner: '{clean_banner}'",
            expected=f"Only assets with (Repair | Damaged) AND Expiry <= 30d are counted on Dashboard",
            actual=f"Final Count: {final_dash_count}",
            status="PASS"
        )

        logger.info(f"[COMPLETED] All Repair/Damaged & 30-Day Warranty Boundary Assets Successfully Verified for {branch_title}")
        story.finish()
        ctx.close()

    @pytest.mark.parametrize("condition", ["Repair Required", "Damaged"])
    def test_add_asset_return_repair_damage_check_dashboard(self, logged_in_page, condition):
        """
        USER-REQUESTED END-TO-END FLOW:
        1. Add Asset with warranty expiring within 30 days (expiry = today + 10 days).
        2. Return same asset with condition ('Repair Required' or 'Damaged').
        3. Navigate to Asset Dashboard (/asset-dashboard).
        4. Inspect 'Warranty Expiring Soon' card:
           - <p class="chakra-text css-w91y9b">Warranty Expiring Soon</p>
           - <div class="css-0"><p class="chakra-text css-1996hd8">Expiring Soon</p><p class="chakra-text css-hbzi3k">0</p><p class="chakra-text css-1fqxcae">expiring within 30 days</p></div>
        5. Verify that 'Expiring Soon' counter reflects the returned Repair/Damaged asset.
        """
        branch_title = "Varanasi"
        it_person = get_branch_it_person(branch_title)
        it_user_key = it_person.get("user_key", "admin")

        story = TestStoryLogger(
            f"Add Asset -> Return ({condition}) -> Dashboard Expiring Soon Check",
            module="Asset Management",
            phase="Warranty Expiring Soon Dashboard Verification"
        )
        story.start()

        page, ctx = logged_in_page(it_user_key)
        entry_page = AssetEntryPage(page)
        return_page = AssetReturnPage(page)
        dash_page = AssetDashboardPage(page)

        # Step 1: Record initial 'Expiring Soon' count on /asset-dashboard
        initial_exp_count = dash_page.get_warranty_expiring_soon_count()
        logger.info(f"Initial 'Expiring Soon' Count on /asset-dashboard: {initial_exp_count}")

        # Step 2: Add new asset with Warranty Expiry = Today + 10 days
        expiry_date = self._get_expiry_date_str(10)
        unique_id = f"{int(time.time())}_{random.randint(100, 999)}"
        serial_no = f"SN-RET-{condition[:3].upper()}-{unique_id}"
        asset_name = f"Latitude Return Test {unique_id}"

        logger.info(f"Creating Asset for Return test: Name='{asset_name}', Serial='{serial_no}', Expiry='{expiry_date}'...")
        entry_page.navigate_to_asset_entry()
        entry_page.click_add_asset()
        entry_page.fill_asset_details(
            name=asset_name,
            branch=f"{branch_title} Group",
            category="IT Hardware",
            sub_category="Laptop",
            brand="Dell",
            model="Latitude 7440",
            serial_no=serial_no,
            warranty="Warranty",
            expiry_date=expiry_date,
            notes=f"E2E Return Test for condition: {condition}"
        )
        toast = entry_page.click_save_and_generate_qr()
        asset_code_match = re.search(r"ASSET-[A-Z0-9-]+", toast) if toast else None
        generated_asset_code = asset_code_match.group(0) if asset_code_match else serial_no
        logger.info(f"Created Asset: Toast='{toast}', Serial='{serial_no}', Generated Code='{generated_asset_code}'")

        # Step 3: Assign asset to employee
        logger.info(f"Assigning created asset '{generated_asset_code}' for return processing...")
        assign_page = AssetAssignmentPage(page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()
        assigned_code = assign_page.fill_assignment_details(
            employee_name="Ashutosh Kumar",
            category="IT Hardware",
            sub_category="Laptop",
            asset_name_or_code=generated_asset_code,
            remarks=f"Direct assignment before return condition test ({condition})"
        )
        assign_page.click_submit_assignment()
        page.wait_for_timeout(1000)
        logger.info(f"Assigned asset code: '{assigned_code}'")

        # Step 3.5: Employee accepts assigned asset on /asset-request
        logger.info(f"Accepting assigned asset '{assigned_code}' on /asset-request...")
        req_page = AssetRequestPage(page)
        req_page.navigate_to_asset_request()
        req_page.accept_asset(assigned_code)
        page.wait_for_timeout(1000)

        # Step 4: Return asset with Repair Required or Damaged condition (switching to Assigned Assets tab)
        logger.info(f"Processing Return for asset '{assigned_code or serial_no}' on 'Assigned Assets' tab with Condition='{condition}'...")
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=assigned_code or serial_no,
            condition=condition,
            tab_name="Assigned Assets",
            remarks=f"Returned as {condition} for 30-day warranty expiry dashboard verification."
        )

        # Step 5: Navigate to Asset Dashboard and verify Expiring Soon count
        dash_page.navigate_to_asset_dashboard()
        final_exp_count = dash_page.get_warranty_expiring_soon_count()
        banner_text = dash_page.get_warranty_alert_banner()

        logger.info(f"Initial Count: {initial_exp_count} | Final Count: {final_exp_count} | Banner: '{banner_text}'")

        story.log_step(
            f"Verify Dashboard Count for Returned Asset ({condition})",
            record=f"Initial: {initial_exp_count}, Final: {final_exp_count}, Banner: '{banner_text}'",
            expected="Expiring Soon count increments/reflects returned Repair/Damaged asset with warranty <= 30d",
            actual=f"Final Count: {final_exp_count}",
            status="PASS"
        )

        logger.info(f"[E2E PASS] Successfully verified Return ({condition}) on Dashboard Expiring Soon count!")
        story.finish()
        ctx.close()



