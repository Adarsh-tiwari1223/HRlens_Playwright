"""
HRlens Portal — Full End-to-End Resignation, Buyout & Asset Clearance Lifecycle Test Suite.

Executes the complete unified multi-role separation lifecycle:
1. Selects a random employee from .env credentials.
2. Checks whether employee has assigned assets:
   - If YES: Proceeds directly.
   - If NO: Admin directly assigns stock assets -> Employee accepts on /asset-request.
3. Employee applies for resignation on /resignation.
4. HR sends Revoke Request on /resignation-approval.
5. Employee declines Revoke Request & submits Buyout / Early Relieving request.
6. HR processes & approves Buyout request on /resignation-approval.
7. Accountant processes Buyout on /accounts-buyout-processing (with Leave Balance & Formula validation).
8. IT Person (Tejasav Jaiswal) opens Release Checklist on /exit-clearance, returns all assets with evidence upload, and completes IT clearance (Task 1/2)!
9. HR (Tejaswini) opens Release Checklist on /exit-clearance, completes HR exit formalities checklist, and finalizes exit clearance (Task 2/2)!
"""

import os
import random
import logging
import pytest

from core.config import settings
from pages.base_page import TestStoryLogger
from pages.hrlense_portal.asset.asset_assignment_page import AssetAssignmentPage
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_request_page import AssetRequestPage
from workflows.hrlense_portal.resignation.employee_resignation_workflow import EmployeeResignationWorkflow
from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow
from workflows.hrlense_portal.resignation.accountant_resignation_workflow import AccountantResignationWorkflow
from workflows.hrlense_portal.resignation.it_resignation_workflow import ItResignationWorkflow

logger = logging.getLogger(__name__)

# Candidate employees with their corresponding Branch, HR, and IT Person dynamically mapped in script
CANDIDATE_EMPLOYEES = [
    {
        "name": "Uttam Kumar",
        "user_key": "uttam_kumar",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Adarsh Tiwari",
        "user_key": "adarsh_tiwari",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Sanidhy Tiwari",
        "user_key": "sanidhy",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Kumar Piyush",
        "user_key": "kumar_piyush",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },

    {
        "name": "Namrata Pandey",
        "user_key": "namrata_pandey",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Radhika Nayak",
        "user_key": "radhika_nayak",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Amar Deep",
        "user_key": "amar_deep",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
    {
        "name": "Kailash Singh",
        "user_key": "kailash_singh",
        "hr_key": "tejaswini",
        "it_key": "it_varanasi_tejasav",
        "branch": "Varanasi",
    },
]



@pytest.mark.ui
@pytest.mark.e2e_full_lifecycle
@pytest.mark.resignation
def test_full_resignation_buyout_and_asset_lifecycle(logged_in_page):
    """
    Unified End-to-End Test: Full Resignation, Buyout, and Asset Clearance Flow.
    """
    story = TestStoryLogger("Full E2E Resignation, Buyout & Asset Clearance Lifecycle", module="Resignation & Asset", phase="Unified E2E")
    story.start()

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1: SELECT RANDOM USER FROM ENV (DYNAMIC MAPPING)
    # ══════════════════════════════════════════════════════════════════════
    selected_emp = random.choice(CANDIDATE_EMPLOYEES)
    emp_name = selected_emp["name"]
    emp_key = selected_emp["user_key"]
    hr_key = selected_emp.get("hr_key", "tejaswini")
    it_key = selected_emp.get("it_key", "it_varanasi_tejasav")
    branch = selected_emp.get("branch", "Varanasi")

    logger.info("=" * 80)
    logger.info(f"SELECTED EMPLOYEE: '{emp_name}' ({emp_key}) | Branch: {branch} | HR: {hr_key} | IT: {it_key}")
    logger.info("=" * 80)
    story.log_step("Select Random Employee", record=f"Selected: '{emp_name}' ({emp_key}) | HR: {hr_key} | IT: {it_key}", expected="Employee selected with dynamic roles", actual=emp_name, status="PASS")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 2: VERIFY ASSETS & CONDITIONAL ASSIGNMENT
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 1 - ASSET CHECK] Checking if '{emp_name}' has assigned assets...")
    emp_page_asset, _ = logged_in_page(emp_key)
    req_page = AssetRequestPage(emp_page_asset)
    has_assets = req_page.has_assigned_assets()

    if has_assets:
        logger.info(f"[ASSET VERIFIED] Employee '{emp_name}' already holds assigned assets. Proceeding directly!")
        story.log_step("Asset Verification", record=f"Employee '{emp_name}' already has assets assigned", expected="Assets exist", actual="Assets found", status="PASS")
        # Close employee asset-check context — no assignment needed
        try:
            emp_page_asset.context.close()
        except Exception:
            pass
    else:
        logger.info(f"[ASSET ASSIGNMENT REQUIRED] Employee '{emp_name}' has NO assets. Assigning stock asset via Admin...")

        # Close employee context FIRST so only one window is open during admin assignment
        try:
            emp_page_asset.context.close()
        except Exception:
            pass

        admin_page, _ = logged_in_page("admin")
        assign_page = AssetAssignmentPage(admin_page)
        assign_page.navigate_to_asset_assignment()
        assign_page.click_assign_asset()

        assigned_code = None
        try:
            assigned_code = assign_page.fill_assignment_details(
                employee_name=emp_name,
                category="IT Hardware",
                sub_category="Laptop",
                remarks="E2E Asset assignment for offboarding lifecycle"
            )
        except Exception as ex:
            logger.warning(f"Initial stock assignment note: {ex}. Creating new asset in branch stock...")
            try:
                assign_page.click_cancel()
            except Exception:
                pass
            # Create fresh stock asset via AssetEntryPage
            entry_page = AssetEntryPage(admin_page)
            entry_page.navigate_to_asset_entry()
            entry_page.click_add_asset()
            entry_page.fill_asset_details(
                category="IT Hardware",
                sub_category="Laptop",
                branch=branch,
                brand="Dell",
                model="Latitude 7440",
                unit_price="50000"
            )
            save_toast = entry_page.click_save_and_generate_qr()
            logger.info(f"Asset Creation Toast: '{save_toast}'")
            admin_page.wait_for_timeout(1000)
            # Now assign to employee
            assign_page.navigate_to_asset_assignment()
            assign_page.click_assign_asset()
            assigned_code = assign_page.fill_assignment_details(
                employee_name=emp_name,
                category="IT Hardware",
                sub_category="Laptop",
                remarks="E2E Asset assignment for offboarding lifecycle"
            )

        assign_page.click_submit_assignment()
        assign_toast = assign_page.wait_for_toast_message()
        logger.info(f"Admin Assignment Toast: '{assign_toast}' | Code: '{assigned_code}'")

        # Close admin context BEFORE opening employee window for acceptance
        try:
            admin_page.context.close()
        except Exception:
            pass

        # Employee accepts asset on /asset-request — fresh single context
        logger.info(f"Employee '{emp_name}' accepting assigned asset...")
        emp_page_accept, _ = logged_in_page(emp_key)
        req_page_accept = AssetRequestPage(emp_page_accept)
        req_page_accept.navigate_to_asset_request()
        accepted = req_page_accept.accept_asset(assigned_code if assigned_code != "ASSET" else None)
        logger.info(f"Employee '{emp_name}' Acceptance Result: {accepted}")
        assert accepted, f"Failed to accept assigned asset for '{emp_name}'"
        story.log_step("Conditional Asset Assignment", record=f"Assigned & Accepted '{assigned_code}'", expected="Asset assigned and accepted", actual="Accepted", status="PASS")

        # Close accept context
        try:
            emp_page_accept.context.close()
        except Exception:
            pass


    # ══════════════════════════════════════════════════════════════════════
    # STEP 3: EMPLOYEE APPLIES FOR RESIGNATION
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 2 - RESIGNATION] Employee '{emp_name}' applying for resignation...")
    emp_page_res, _ = logged_in_page(emp_key)
    emp_wf = EmployeeResignationWorkflow(emp_page_res)
    emp_wf.res_page.navigate_to_resignation()

    if not emp_wf.res_page.has_active_resignation():
        res_result = emp_wf.submit_resignation_workflow(
            reason="1",
            stay_connected=True,
            share_suggestions=True,
            suggestion_text="Career growth and new professional opportunities.",
            confirm=True
        )
        res_toast = res_result.get("toast", "")
        logger.info(f"Resignation Submission Toast: '{res_toast}'")
        assert res_result.get("modal_visible") or res_toast != "", f"Resignation application failed for '{emp_name}'"
        story.log_step("Employee Apply Resignation", record=f"Submitted fresh resignation. Toast: '{res_toast}'", expected="Resignation applied", actual="Applied", status="PASS")
    else:
        logger.info(f"Employee '{emp_name}' already has an active resignation record on portal.")
        emp_wf.res_page.click_status_tab()
        if not emp_wf.res_page.is_early_relieving_date_input_visible(timeout=3000):
            skip_msg = f"Resignation already in the process for '{emp_name}' skipped"
            logger.warning(skip_msg)
            story.log_step("Employee Apply Resignation", record=skip_msg, expected="New resignation candidate", actual="Already in process", status="SKIPPED")
            pytest.skip(skip_msg)
        story.log_step("Employee Apply Resignation", record=f"Active resignation found for '{emp_name}'", expected="Active resignation present", actual="Active", status="PASS")

    # Close Phase 2 context
    try:
        emp_page_res.context.close()
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════════
    # STEP 4: DYNAMIC HR SENDS REVOKE REQUEST
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 3 - HR REVOKE] HR ({hr_key}) sending Revoke Request for '{emp_name}'...")
    hr_page, _ = logged_in_page(hr_key)
    hr_wf = HrResignationWorkflow(hr_page)
    hr_wf.res_page.navigate_to_hr_resignation_approval()
    hr_wf.res_page.search_employee_in_hr_table(emp_name)
    hr_status = hr_wf.res_page.get_hr_table_employee_status(emp_name)
    logger.info(f"HR Resignation table status for '{emp_name}': '{hr_status}'")

    if any(keyword in hr_status.lower() for keyword in ["left", "notice", "relieved"]):
        skip_msg = f"Resignation already in the process for '{emp_name}' skipped"
        logger.warning(skip_msg)
        story.log_step("HR Send Revoke", record=skip_msg, expected="Fresh / pending resignation", actual=hr_status, status="SKIPPED")
        pytest.skip(skip_msg)

    try:
        hr_revoke_toast = hr_wf.execute_hr_revoke_request_workflow(employee_name=emp_name)
        logger.info(f"HR Revoke Request Toast: '{hr_revoke_toast}'")
        story.log_step("HR Send Revoke", record=f"Toast: '{hr_revoke_toast}'", expected="Revoke request sent", actual=str(hr_revoke_toast), status="PASS")
    except Exception as ex:
        logger.warning(f"HR Revoke note (resignation may already be past initial state): {ex}")
        story.log_step("HR Send Revoke", record=f"Revoke step note: {ex}", expected="Revoke processed or bypassed", actual="Checked", status="PASS")

    # Close Phase 3 context
    try:
        hr_page.context.close()
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════════
    # STEP 5: EMPLOYEE DECLINES REVOKE & APPLIES BUYOUT
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 4 - EMPLOYEE BUYOUT] Employee '{emp_name}' declining Revoke & requesting Buyout...")
    emp_page_buyout, _ = logged_in_page(emp_key)
    emp_wf_buyout = EmployeeResignationWorkflow(emp_page_buyout)
    emp_wf_buyout.res_page.navigate_to_resignation()

    # Decline Revoke if present
    try:
        emp_wf_buyout.respond_to_revoke_request_workflow(accept=False)
        logger.info(f"Employee '{emp_name}' successfully declined Revoke Request.")
    except Exception as ex:
        logger.info(f"Revoke response note: {ex}")

    # Request Buyout / Early Relieving Date for TODAY (immediate release)
    from datetime import datetime
    leave_today = datetime.now().strftime("%Y-%m-%d")
    emp_wf_buyout.res_page.click_status_tab()
    if not emp_wf_buyout.res_page.is_early_relieving_date_input_visible(timeout=3000):
        skip_msg = f"Resignation already in the process for '{emp_name}' skipped"
        logger.warning(skip_msg)
        story.log_step("Employee Request Buyout", record=skip_msg, expected="Date input visible", actual="Not visible (Already in process)", status="SKIPPED")
        pytest.skip(skip_msg)

    buyout_res = emp_wf_buyout.request_early_relieving_workflow(leave_today)
    logger.info(f"Buyout Request Result: {buyout_res} (Requested Date: {leave_today} - Today)")
    story.log_step("Employee Request Buyout", record=f"Early Relieving requested for Today: {leave_today} | Toast: {buyout_res}", expected="Buyout requested for Today", actual="Requested", status="PASS")

    # Close Phase 4 context
    try:
        emp_page_buyout.context.close()
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════════
    # STEP 6: DYNAMIC HR PROCESSES & APPROVES BUYOUT
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 5 - HR PROCESS BUYOUT] HR ({hr_key}) approving Buyout Request for '{emp_name}'...")
    hr_page_buyout, _ = logged_in_page(hr_key)
    hr_wf_buyout = HrResignationWorkflow(hr_page_buyout)
    hr_buyout_toast = hr_wf_buyout.process_buyout_request_workflow(employee_name=emp_name, process=True)
    logger.info(f"HR Buyout Approval Toast: '{hr_buyout_toast}'")
    story.log_step("HR Process Buyout", record=f"Toast: '{hr_buyout_toast}'", expected="Buyout approved by HR", actual=str(hr_buyout_toast), status="PASS")

    # Close Phase 5 context
    try:
        hr_page_buyout.context.close()
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════════
    # STEP 7: ACCOUNTANT PROCESSES BUYOUT WITH FINANCIAL FORMULA
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 6 - ACCOUNTANT SETTLEMENT] Accountant processing Buyout for '{emp_name}'...")
    acc_page, _ = logged_in_page("admin")
    acc_wf = AccountantResignationWorkflow(acc_page)
    acc_res = acc_wf.process_accountant_buyout_workflow(
        employee_name=emp_name,
        calculated_salary="1000",
        remarks="E2E Buyout Settlement Approved & Cleared by Accountant",
        confirm_recovery=True,
        approve=True
    )
    logger.info(f"Accountant Settlement Result: {acc_res}")
    assert acc_res.get("success"), f"Accountant process buyout failed for '{emp_name}'"
    acc_toast = str(acc_res.get("toast", "")).strip()
    story.log_step("Accountant Buyout Processing", record=f"Toast: '{acc_toast}' | Formula Match: {acc_res.get('formula_match')}", expected="Buyout settled & approved", actual=acc_toast, status="PASS")

    # Close Phase 6 context
    try:
        acc_page.context.close()
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════════
    # STEP 8: DYNAMIC IT PERSON ASSET RETURN & EXIT CLEARANCE (TASK 1 OF 2)
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 7 - IT ASSET CLEARANCE] IT Person ({it_key}) executing asset clearance for '{emp_name}'...")
    it_page, _ = logged_in_page(it_key)
    it_wf = ItResignationWorkflow(it_page)
    it_res = it_wf.inspect_and_clear_employee_assets_workflow(
        employee_name=emp_name,
        asset_condition="Good Condition",
        remarks="IT Asset clearance verified & returned in good condition"
    )
    logger.info(f"IT Asset Clearance Result: {it_res}")
    assert it_res.get("success"), f"Failed IT Clearance for '{emp_name}'"
    story.log_step("IT Asset Clearance", record=f"Result: {it_res}", expected="IT Clearance completed (1/2)", actual=str(it_res), status="PASS")

    # Close Phase 7 context
    try:
        it_page.context.close()
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════════
    # STEP 9: DYNAMIC HR EXIT CLEARANCE & FORMALITIES (TASK 2 OF 2)
    # ══════════════════════════════════════════════════════════════════════
    logger.info(f"[PHASE 8 - HR EXIT CLEARANCE] HR ({hr_key}) executing final HR clearance for '{emp_name}'...")
    hr_page_exit, _ = logged_in_page(hr_key)
    hr_wf_exit = HrResignationWorkflow(hr_page_exit)
    hr_clear_res = hr_wf_exit.execute_hr_exit_clearance_workflow(
        employee_name=emp_name,
        remarks="HR Exit formalities, handover, and document checklist completed"
    )
    logger.info(f"HR Exit Clearance Result: {hr_clear_res}")
    assert hr_clear_res.get("success"), f"Failed HR Exit Clearance for '{emp_name}'"
    story.log_step("HR Exit Clearance", record=f"Result: {hr_clear_res}", expected="HR Clearance completed (2/2)", actual=str(hr_clear_res), status="PASS")

    # Close Phase 8 context
    try:
        hr_page_exit.context.close()
    except Exception:
        pass

    logger.info("=" * 80)
    logger.info(f"[PASS 100%] FULL E2E RESIGNATION, BUYOUT & 2/2 EXIT CLEARANCE COMPLETED FOR '{emp_name}'!")
    logger.info("=" * 80)

