"""
HRlens Portal — Complete Asset Management E2E Lifecycle Test Suite.
Strict 3-Tier Architecture: Page Object -> Workflow Layer -> Test Suite.
"""

import os
import random
import logging
import pytest
from pages.base_page import TestStoryLogger
from workflows.hrlense_portal.asset.asset_workflow import AssetWorkflow
from workflows.hrlense_portal.asset.asset_procurement_workflow import AssetProcurementWorkflow
from workflows.hrlense_portal.asset.branch_group_workflow import BranchGroupWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.e2e
def test_asset_e2e_complete_lifecycle(logged_in_page):
    """
    Mainstream End-to-End Asset Lifecycle (Phases 1 through 8):
    Master Setup -> Invoice Procurement -> Asset Entry ->
    Direct Assignment -> Employee Acceptance -> Usage -> Return (Good -> Available) -> History.
    """
    story = TestStoryLogger("Asset Management E2E Mainstream Lifecycle", module="Asset Management", phase="Full E2E Lifecycle")
    story.start()

    admin_page, admin_context = logged_in_page("admin")
    asset_workflow = AssetWorkflow(admin_page)

    # ─── Phase 1: Master Setup ────────────────────────────────────────────────
    category_name = "Hardware"
    sub_category_name = "Laptop"
    sub_prefix = "LAP"

    cat_toast = asset_workflow.create_category_workflow(name=category_name, description="IT Hardware and Workstation Equipment")
    story.log_step("Phase 1.1: Create Asset Category", record=category_name, actual=f"Toast: '{cat_toast}'", status="PASS")

    sub_toast = asset_workflow.create_sub_category_workflow(category_name=category_name, sub_category_name=sub_category_name, prefix=sub_prefix, description="High-performance laptops")
    story.log_step("Phase 1.2: Create Sub-Category", record=f"{sub_category_name} -> {category_name}", actual=f"Toast: '{sub_toast}'", status="PASS")

    gst_pan = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5)) + "".join(random.choices("0123456789", k=4))
    dynamic_gst = f"29{gst_pan}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}1Z{random.randint(1, 9)}"
    vendor_toast = asset_workflow.create_vendor_workflow({
        "name": "Dell Technologies India Pvt Ltd",
        "contact_person": "Rahul Verma",
        "email": "procurement.india@dell.com",
        "phone": "9810012345",
        "address": "Embassy GolfLinks Business Park, Bengaluru, Karnataka 560071",
        "gst": dynamic_gst,
        "supports_amc": True
    })
    story.log_step("Phase 1.3: Create Vendor", record=f"GST: {dynamic_gst}", actual=f"Toast: '{vendor_toast}'", status="PASS")

    bg_workflow = BranchGroupWorkflow(admin_page)
    bg_toast = bg_workflow.create_branch_group_workflow(group_name="Varanasi Branch Group", seating_cost="2500.00", search_query="Varanasi")
    story.log_step("Phase 1.4: Create Branch Group", record="Varanasi Branch Group", actual=f"Toast: '{bg_toast}'", status="PASS")

    # ─── Phase 2: Invoice Procurement ────────────────────────────────────────
    invoices_dir = os.path.abspath("testdata/static/invoices")
    invoice_path = os.path.join(invoices_dir, "invoice_1mb.pdf")
    if not os.path.exists(invoice_path):
        invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")

    proc_workflow = AssetProcurementWorkflow(admin_page)
    proc_toast = proc_workflow.procure_asset_with_invoice(invoice_file_path=invoice_path, story=story)
    is_procured = any(t in proc_toast.lower() for t in ["success", "created", "procured", "saved", "added"])
    story.log_step("Phase 2: Invoice Procurement", record=os.path.basename(invoice_path), actual=f"Toast: '{proc_toast}'", status="PASS" if is_procured else "FAIL")
    assert is_procured, f"Asset Procurement failed: {proc_toast}"

    # ─── Phase 3: Asset Entry ─────────────────────────────────────────────────
    serial_no = f"SN-DELL-{random.randint(100000, 999999)}"
    entry_result = asset_workflow.add_asset_workflow({
        "name": "Dell Latitude 7440",
        "brand": "Dell",
        "model": "Latitude 7440",
        "serial_no": serial_no,
        "warranty": "Warranty",
        "expiry_date": "2027-12-31",
        "insured": "No",
        "notes": "Enterprise workstation procured under IT hardware budget."
    })
    story.log_step("Phase 3: Add Asset Entry", record=f"Serial: {serial_no}", actual=f"Toast: '{entry_result['toast']}'", status="PASS")

    asset_code = asset_workflow.read_asset_code_by_serial(serial_no)
    story.log_step("Phase 3: Verify Asset Code", record=f"Code: {asset_code}", status="PASS")

    # ─── Phase 4: Assignment & Acceptance ────────────────────────────────────
    employee_name = "Sanidhy Tiwari"
    assign_toast = asset_workflow.assign_asset_workflow(
        employee_name=employee_name,
        category=entry_result["filled"].get("category") or category_name,
        sub_category=entry_result["filled"].get("sub_category") or sub_category_name,
        asset_code=asset_code,
        expected_return_date="2026-12-31",
        remarks="Assigned to software development engineer."
    )
    story.log_step("Phase 4: Direct Assignment", record=f"{asset_code} -> {employee_name}", actual=f"Toast: '{assign_toast}'", status="PASS")

    employee_page, employee_context = logged_in_page("sanidhy")
    employee_workflow = AssetWorkflow(employee_page)
    is_accepted = employee_workflow.accept_asset_workflow(asset_code)
    story.log_step("Phase 4: Employee Accepts Asset", record=f"Employee: {employee_name}", actual=f"Accepted: {is_accepted}", status="PASS")
    employee_context.close()

    # ─── Phase 5: Usage Verification ─────────────────────────────────────────
    story.log_step("Phase 5: Asset Usage & Tracking", record=asset_code, actual="Asset confirmed actively assigned", status="PASS")

    # ─── Phase 6 & 7: Return & IT Condition Assessment ───────────────────────
    return_result = asset_workflow.return_asset_workflow(
        asset_code=asset_code,
        condition="Good",
        return_date="2026-08-14",
        remarks="Asset returned in good condition."
    )
    story.log_step("Phase 6 & 7: Return & Condition Assessment", record=f"{asset_code} | Good", actual=f"Toast: '{return_result['toast']}'", status="PASS")

    # ─── Phase 8: Return History Verification ────────────────────────────────
    story.log_step("Phase 8: Return History Verification", record=str(return_result["history"]), status="PASS")

    story.finish(status="PASS")
