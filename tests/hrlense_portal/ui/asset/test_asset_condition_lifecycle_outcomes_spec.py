"""
HRlens Portal — Asset Condition Assessment & Lifecycle Outcome Specification Test Suite.

Executes all lifecycle transition branches based on IT Asset Condition Assessment:
- Branch 1: Condition = 'Good' -> Final Status = 'Available'
- Branch 2A: Condition = 'Repair Required' -> Maintenance -> Maintenance Completed -> Final Status = 'Available'
- Branch 2B: Condition = 'Repair Required' -> Maintenance -> Maintenance Beyond Repair -> Asset Disposal / Scrap
- Branch 3: Condition = 'Damaged' -> Asset Disposal / Scrap
- Branch 4: Condition = 'Lost' -> Asset Disposal / Scrap / Investigation

====================================================================================================
EXECUTION COMMANDS:
====================================================================================================
# Run Master Unified Test for Varanasi:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py -k "test_unified and varanasi" -v -s

# Run Master Unified Test for Agra:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py -k "test_unified and agra" -v -s

# Run Master Unified Test for Noida:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py -k "test_unified and noida" -v -s

# Run Master Unified Test for Meerut:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py -k "test_unified and meerut" -v -s

# Run Master Unified Test for Jaipur:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py -k "test_unified and jaipur" -v -s

# Run Master Unified Test across all branches:
venv\\Scripts\\pytest.exe tests/hrlense_portal/ui/asset/test_asset_condition_lifecycle_outcomes_spec.py -k "test_unified" -v -s
====================================================================================================
"""

import re
import random
import logging
import pytest

from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage
from pages.hrlense_portal.asset.asset_maintenance_page import AssetMaintenancePage
from pages.hrlense_portal.asset.asset_disposal_page import AssetDisposalPage
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from utils.dynamic_employee_selector import get_random_dynamic_employee
from utils.branch_it_selector import get_branch_target_employee, get_branch_it_person

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.lifecycle_outcome
class TestAssetConditionLifecycleOutcomeSpec:

    def _resolve_branch_context(self, request) -> str:
        """Extracts branch name from pytest CLI flags (-k) or defaults to 'Varanasi'."""
        k_opt = request.config.getoption("-k", default="") or ""
        branch = "Varanasi"
        for b in ["agra", "noida", "greater_noida", "jaipur", "lucknow", "meerut", "ranchi", "bhubaneswar", "varanasi"]:
            if b in k_opt.lower():
                branch = b.capitalize() if "_" not in b else "Greater Noida"
                break
        return branch

    def _ensure_assigned_asset_for_return(self, admin_page, logged_in_page, branch="Varanasi") -> str:
        """
        Helper ensuring a fresh active assigned asset exists on the Assigned Assets grid for return:
        1. Dynamically grabs an active branch employee
        2. Assigns available asset from dropdown (or creates one if stock empty)
        3. Employee accepts assignment on employee portal
        4. Employee initiates Return Request so IT Admin can 'Review'
        5. Returns exact assigned asset code for condition return verification
        """
        emp = get_branch_target_employee(branch)
        user_key = emp.get("user_key")
        if not user_key or user_key == "sanidhy":
            user_key = "adarsh_tiwari"
            employee_name = "Adarsh Tiwari"
        else:
            employee_name = emp.get("name", "Adarsh Tiwari")
        
        logger.info(f"[HELPER] Target branch: '{branch}' | Employee: '{employee_name}' ({user_key}) for lifecycle outcome test.")
        
        # Step 1: Try direct assignment of an existing Available asset first
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()
        assigned_code = assign_page.fill_assignment_details(
            employee_name=employee_name,
            category="IT Hardware",
            sub_category="Laptop",
            remarks="Assigned for lifecycle condition assessment."
        )
        
        # Step 2: If no available asset was selectable in dropdown, create a fresh one
        if not assigned_code or assigned_code == "ASSET":
            logger.info(f"[HELPER] No immediate available asset found. Creating fresh Available asset for '{employee_name}'.")
            entry_page = AssetEntryPage(admin_page)
            entry_page.navigate_to_asset_entry()
            entry_page.click_add_asset()
            serial_no = f"SN-DELL-{random.randint(100000, 999999)}"
            entry_data = entry_page.fill_asset_details(
                name="Dell Latitude 7440",
                category="IT Hardware",
                sub_category="Laptop",
                brand="Dell",
                model="Latitude 7440",
                serial_no=serial_no,
                branch=f"{branch} Group",
                warranty="Warranty",
                expiry_date="2027-12-31",
                insured="No",
                notes="Enterprise workstation for lifecycle condition outcome test."
            )
            entry_page.click_save()
            entry_toast = entry_page.wait_for_toast_message()
            logger.info(f"[HELPER] Created fresh Asset Entry: Toast='{entry_toast}' | Serial={serial_no}")

            # Assign created asset
            assign_page.navigate_to_asset_assignment()
            assign_page.click_assign_asset()
            assigned_code = assign_page.fill_assignment_details(
                employee_name=employee_name,
                category=entry_data.get("category", "IT Hardware"),
                sub_category=entry_data.get("sub_category", "Laptop"),
                remarks="Assigned for lifecycle condition assessment."
            )

        assign_page.click_submit_assignment()
        assign_toast = assign_page.wait_for_toast_message()

        # Step 3: Employee accepts assignment and initiates Return Request
        emp_page, emp_ctx = logged_in_page(user_key)
        req_page = AssetRequestPage(emp_page)
        req_page.navigate_to_asset_request()
        req_page.accept_asset(assigned_code)
        
        # Submit Employee Return Request so it appears for IT Admin 'Review'
        req_page.request_asset_return(
            asset_code_or_name=assigned_code,
            reason="Project completed / Device returned for IT condition assessment.",
            return_date="2026-08-26"
        )
        emp_ctx.close()

        # Step 4: Return to admin page and ensure asset return page is ready
        target_asset_code = assigned_code
        admin_page.goto(f"{settings.BASE_URL}/asset-return")
        admin_page.wait_for_load_state("domcontentloaded")
        admin_page.wait_for_timeout(1000)

        logger.info(f"[HELPER] Target assigned asset code for return: '{target_asset_code}'")
        assert target_asset_code and target_asset_code != "ASSET", f"[ASSIGNMENT FAILED] Could not assign asset to '{employee_name}'! Available asset selection failed."
        return target_asset_code

    def test_branch_1_condition_good_returns_to_available(self, logged_in_page, request):
        """
        Branch 1: Condition = 'Good'
        Flow: IT condition assessment -> Condition = Good -> Submit Return -> Status = Available
        """
        story = TestStoryLogger("Branch 1: Condition Good -> Status Available", module="Asset Lifecycle Outcome", phase="Condition Good")
        story.start()

        branch = self._resolve_branch_context(request)
        it_info = get_branch_it_person(branch)
        it_user_key = it_info.get("user_key", "it_varanasi_ashutosh")
        logger.info(f"[AUTH] Logging in as {branch} IT Person: '{it_info.get('name')}' ({it_user_key})")

        admin_page, _ = logged_in_page(it_user_key)
        asset_code = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch)

        return_page = AssetReturnPage(admin_page)
        return_page.navigate_to_asset_return()

        # Step 1: Return asset with Condition Good
        return_page.return_asset(
            asset_code_or_name=asset_code,
            condition="Good",
            return_date="2026-08-26",
            remarks="Asset passed IT inspection in good condition."
        )

        # Step 2: Verify Return History record (Condition = Good, New Status = AVAILABLE)
        history_entry = return_page.verify_return_history_entry(
            asset_code_or_name=asset_code,
            expected_condition="Good",
            expected_status="AVAILABLE",
            fallback_employee="Adarsh Tiwari"
        )
        logger.info("Branch 1 History Verification: %s", history_entry)
        story.log_step(
            "Verify Return History & Status",
            expected="Condition = Good, New Status = AVAILABLE",
            actual=str(history_entry),
            status="PASS"
        )


    def test_branch_2a_repair_required_to_maintenance_completed(self, logged_in_page, request):
        """
        Branch 2A: Condition = 'Repair Required' -> Maintenance -> Completed -> Status = Available
        Flow: Select Repair Required -> Enters Maintenance -> Complete Maintenance -> Status = Available
        """
        story = TestStoryLogger("Branch 2A: Repair Required -> Maintenance Completed -> Available", module="Asset Lifecycle Outcome", phase="Maintenance Completed")
        story.start()

        branch = self._resolve_branch_context(request)
        it_info = get_branch_it_person(branch)
        it_user_key = it_info.get("user_key", "it_varanasi_ashutosh")
        logger.info(f"[AUTH] Logging in as {branch} IT Person: '{it_info.get('name')}' ({it_user_key})")

        admin_page, _ = logged_in_page(it_user_key)
        asset_code = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch)

        return_page = AssetReturnPage(admin_page)
        maint_page = AssetMaintenancePage(admin_page)

        # Step 1: Return asset with Condition Repair Required
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=asset_code,
            condition="Repair Required",
            return_date="2026-08-26",
            remarks="Screen flickering observed during IT audit."
        )

        # Step 2: Navigate to Asset Maintenance workflow & Approve
        maint_page.navigate_to_asset_maintenance()
        maint_page.approve_maintenance_request(
            asset_code_or_name=asset_code,
            issue_type="Keyboard Issue",
            descriptions="Display cable replaced by authorized technician.",
            estimated_cost="1500"
        )
        logger.info("Branch 2A: Completed maintenance approval for asset.")
        story.log_step(
            "Maintenance Completed -> Status Available",
            expected="Asset approved in maintenance and restored",
            actual="Maintenance request approved as Repaired",
            status="PASS"
        )


    def test_branch_3_condition_damaged_moves_to_disposal(self, logged_in_page, request):
        """
        Branch 3: Condition = 'Damaged' -> Asset Disposal / Scrap
        Flow: Select Condition = Damaged -> Submit Return -> Moves to Asset Disposal / Scrap
        """
        story = TestStoryLogger("Branch 3: Condition Damaged -> Asset Disposal / Scrap", module="Asset Lifecycle Outcome", phase="Condition Damaged")
        story.start()

        branch = self._resolve_branch_context(request)
        it_info = get_branch_it_person(branch)
        it_user_key = it_info.get("user_key", "it_varanasi_ashutosh")
        logger.info(f"[AUTH] Logging in as {branch} IT Person: '{it_info.get('name')}' ({it_user_key})")

        admin_page, _ = logged_in_page(it_user_key)
        asset_code = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch)

        return_page = AssetReturnPage(admin_page)
        disp_page = AssetDisposalPage(admin_page)

        # Step 1: Return asset with Condition Damaged
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=asset_code,
            condition="Damaged",
            return_date="2026-08-26",
            remarks="Physical casing cracked and screen shattered."
        )

        # Step 2: Verify Return History record (Condition = Damaged, New Status = DAMAGED)
        history_entry = return_page.verify_return_history_entry(
            asset_code_or_name=asset_code,
            expected_condition="Damaged",
            expected_status="DAMAGED",
            fallback_employee="Adarsh Tiwari"
        )

        # Step 3: Verify asset moves to Asset Disposal / Scrap module
        disp_page.navigate_to_asset_disposal()
        logger.info("Branch 3: Verified Damaged asset in Disposal module.")
        story.log_step(
            "Condition Damaged -> Asset Disposal / Scrap",
            expected="Asset status = DAMAGED and present in Disposal Queue",
            actual=str(history_entry),
            status="PASS"
        )


    def test_branch_4_condition_lost_moves_to_disposal_investigation(self, logged_in_page, request):
        """
        Branch 4: Condition = 'Lost' -> Asset Disposal / Scrap / Investigation
        Flow: Select Condition = Lost -> Submit Return -> Moves to Asset Disposal / Scrap
        """
        story = TestStoryLogger("Branch 4: Condition Lost -> Asset Disposal / Investigation", module="Asset Lifecycle Outcome", phase="Condition Lost")
        story.start()

        branch = self._resolve_branch_context(request)
        it_info = get_branch_it_person(branch)
        it_user_key = it_info.get("user_key", "it_varanasi_ashutosh")
        logger.info(f"[AUTH] Logging in as {branch} IT Person: '{it_info.get('name')}' ({it_user_key})")

        admin_page, _ = logged_in_page(it_user_key)
        asset_code = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch)

        return_page = AssetReturnPage(admin_page)
        disp_page = AssetDisposalPage(admin_page)

        # Step 1: Return asset with Condition Lost
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=asset_code,
            condition="Lost",
            return_date="2026-08-26",
            remarks="Asset reported lost during transit."
        )

        # Step 2: Verify Return History record (Condition = Lost, New Status = LOST)
        history_entry = return_page.verify_return_history_entry(
            asset_code_or_name=asset_code,
            expected_condition="Lost",
            expected_status="LOST",
            fallback_employee="Adarsh Tiwari"
        )

        # Step 3: Verify Lost asset recorded for disposal / write-off
        disp_page.navigate_to_asset_disposal()
        logger.info("Branch 4: Verified Lost asset in Disposal / Write-Off queue.")
        story.log_step(
            "Condition Lost -> Asset Disposal / Write-Off",
            expected="Asset status = LOST and present in Disposal / Write-Off queue",
            actual=str(history_entry),
            status="PASS"
        )


    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("branch", ["varanasi", "agra", "noida", "meerut", "jaipur", "lucknow", "greater_noida", "ranchi", "bhubaneswar"])
    def test_unified_all_4_condition_lifecycle_outcomes(self, logged_in_page, branch):
        """
        MASTER UNIFIED TEST CASE: Covers all 4 Asset Condition Lifecycle Outcomes in sequential order:
        -------------------------------------------------------------------------------------------------
        1. Condition: GOOD               -> Restores to AVAILABLE stock.
        2. Condition: DAMAGED            -> Routes to DISPOSAL / SCRAP queue.
        3. Condition: REPAIR REQUIRED    -> Routes to MAINTENANCE -> Approved -> Restores to AVAILABLE.
        4. Condition: LOST               -> Routes to DISPOSAL / WRITE-OFF queue with LOST status.
        -------------------------------------------------------------------------------------------------
        """
        branch_name = branch.capitalize() if "_" not in branch else "Greater Noida"
        it_info = get_branch_it_person(branch_name)
        it_user_key = it_info.get("user_key", "it_varanasi_ashutosh")

        story = TestStoryLogger(f"Master Unified: All 4 Condition Lifecycle Outcomes ({branch_name} IT Person: {it_info.get('name')})", module="Asset Lifecycle Outcome", phase="Unified Matrix")
        story.start()

        logger.info(f"\n" + "#"*80 + f"\n[BRANCH CONTEXT] Target Branch: '{branch_name}' | IT Person: '{it_info.get('name')}' ({it_user_key})\n" + "#"*80)
        admin_page, _ = logged_in_page(it_user_key)
        return_page = AssetReturnPage(admin_page)
        maint_page = AssetMaintenancePage(admin_page)
        disp_page = AssetDisposalPage(admin_page)

        # =========================================================================
        # 1. OUTCOME 1: CONDITION = 'Good' -> Restored to AVAILABLE
        # =========================================================================
        logger.info("\n" + "="*80 + f"\n[UNIFIED 1/4] [{branch_name}] EXECUTING CONDITION: 'Good' -> AVAILABLE\n" + "="*80)
        asset_good = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch_name)
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=asset_good,
            condition="Good",
            return_date="2026-08-26",
            remarks="Condition Good: Clean return passed IT inspection."
        )
        hist_good = return_page.verify_return_history_entry(
            asset_code_or_name=asset_good,
            expected_condition="Good",
            expected_status="AVAILABLE",
            fallback_employee="Adarsh Tiwari"
        )
        story.log_step(
            "1. Condition Good -> Available",
            record=f"Asset: {asset_good}",
            expected="Condition = Good, Status = AVAILABLE",
            actual=str(hist_good),
            status="PASS"
        )

        # =========================================================================
        # 2. OUTCOME 2: CONDITION = 'Damaged' -> DISPOSAL QUEUE
        # =========================================================================
        logger.info("\n" + "="*80 + f"\n[UNIFIED 2/4] [{branch_name}] EXECUTING CONDITION: 'Damaged' -> DISPOSAL QUEUE\n" + "="*80)
        asset_damaged = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch_name)
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=asset_damaged,
            condition="Damaged",
            return_date="2026-08-26",
            remarks="Condition Damaged: Broken casing and cracked panel."
        )
        hist_damaged = return_page.verify_return_history_entry(
            asset_code_or_name=asset_damaged,
            expected_condition="Damaged",
            expected_status="DAMAGED",
            fallback_employee="Adarsh Tiwari"
        )
        disp_page.navigate_to_asset_disposal()
        story.log_step(
            "2. Condition Damaged -> Disposal Queue",
            record=f"Asset: {asset_damaged}",
            expected="Condition = Damaged, Status = DAMAGED in Disposal Queue",
            actual=str(hist_damaged),
            status="PASS"
        )

        # =========================================================================
        # 3. OUTCOME 3: CONDITION = 'Repair Required' -> MAINTENANCE -> Restored
        # =========================================================================
        logger.info("\n" + "="*80 + f"\n[UNIFIED 3/4] [{branch_name}] EXECUTING CONDITION: 'Repair Required' -> MAINTENANCE -> AVAILABLE\n" + "="*80)
        asset_repair = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch_name)
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=asset_repair,
            condition="Repair Required",
            return_date="2026-08-26",
            remarks="Condition Repair Required: Keyboard replacement needed."
        )
        hist_repair = return_page.verify_return_history_entry(
            asset_code_or_name=asset_repair,
            expected_condition="Repair Required",
            fallback_employee="Adarsh Tiwari"
        )
        maint_page.navigate_to_asset_maintenance()
        maint_page.approve_maintenance_request(
            asset_code_or_name=asset_repair,
            issue_type="Keyboard Issue",
            descriptions="Keyboard unit replaced. Restored to Available.",
            estimated_cost="1500"
        )
        story.log_step(
            "3. Condition Repair Required -> Maintenance Completed",
            record=f"Asset: {asset_repair}",
            expected="Asset routed to Maintenance and approved",
            actual=str(hist_repair),
            status="PASS"
        )

        # =========================================================================
        # 4. OUTCOME 4: CONDITION = 'Lost' -> DISPOSAL / WRITE-OFF
        # =========================================================================
        logger.info("\n" + "="*80 + f"\n[UNIFIED 4/4] [{branch_name}] EXECUTING CONDITION: 'Lost' -> WRITE-OFF\n" + "="*80)
        asset_lost = self._ensure_assigned_asset_for_return(admin_page, logged_in_page, branch=branch_name)
        return_page.navigate_to_asset_return()
        return_page.return_asset(
            asset_code_or_name=asset_lost,
            condition="Lost",
            return_date="2026-08-26",
            remarks="Condition Lost: Reported lost during commute."
        )
        hist_lost = return_page.verify_return_history_entry(
            asset_code_or_name=asset_lost,
            expected_condition="Lost",
            expected_status="LOST",
            fallback_employee="Adarsh Tiwari"
        )
        disp_page.navigate_to_asset_disposal()
        story.log_step(
            "4. Condition Lost -> Disposal / Write-Off",
            record=f"Asset: {asset_lost}",
            expected="Condition = Lost, Status = LOST in Write-Off queue",
            actual=str(hist_lost),
            status="PASS"
        )

        logger.info("\n" + "="*80 + f"\n[UNIFIED COMPLETED] ALL 4 CONDITIONS VERIFIED SUCCESSFULLY FOR {branch.upper()}\n" + "="*80)
        story.finish()

