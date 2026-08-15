import os
import logging
import pytest
from pages.base_page import TestStoryLogger
from workflows.hrlense_portal.asset.asset_procurement_workflow import AssetProcurementWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
def test_asset_e2e_procurement_flow(logged_in_page):
    story = TestStoryLogger("Asset Procurement Form Submission Test", module="Asset Management", phase="Asset Procurement")
    story.start()

    # Step 1: Admin login
    admin_page, admin_context = logged_in_page("admin")

    # Step 2: Locate Invoice File
    invoices_dir = os.path.abspath("testdata/static/invoices")
    sample_invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")
    if not os.path.exists(sample_invoice_path):
        sample_invoice_path = os.path.join(invoices_dir, "invoice_1mb.pdf")

    logger.info(f"[STEP 2] Running Asset Procurement Workflow with Invoice: {sample_invoice_path}")

    # Step 3: Execute Asset Procurement Workflow with step-by-step reporting
    workflow = AssetProcurementWorkflow(admin_page)
    toast = workflow.procure_asset_with_invoice(
        invoice_file_path=sample_invoice_path,
        story=story
    )

    is_success = any(term in toast.lower() for term in ["success", "created", "procured", "saved", "added"])

    story.log_step(
        "Submit Asset Procurement Form",
        record=f"Invoice File: {os.path.basename(sample_invoice_path)}",
        expected="Asset Procurement entry should be created successfully",
        actual=f"Toast message received: '{toast}'" if is_success else f"Failed: {toast}",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Procurement failed with toast message: '{toast}'"


@pytest.mark.ui
@pytest.mark.asset
def test_asset_procurement_with_png_invoice(logged_in_page):
    story = TestStoryLogger("Asset Procurement via PNG Image Invoice Test", module="Asset Management", phase="Asset Procurement")
    story.start()

    admin_page, admin_context = logged_in_page("admin")

    invoices_dir = os.path.abspath("testdata/static/invoices")
    sample_invoice_path = os.path.join(invoices_dir, "invoice_1mb.png")
    if not os.path.exists(sample_invoice_path):
        sample_invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")

    logger.info(f"[STEP 2] Running Asset Procurement Workflow with Image Invoice: {sample_invoice_path}")

    workflow = AssetProcurementWorkflow(admin_page)
    toast = workflow.procure_asset_with_invoice(
        invoice_file_path=sample_invoice_path,
        story=story
    )

    is_success = any(term in toast.lower() for term in ["success", "created", "procured", "saved", "added"])

    story.log_step(
        "Submit Asset Procurement Form with PNG Invoice",
        record=f"Invoice File: {os.path.basename(sample_invoice_path)}",
        expected="Asset Procurement entry should be created successfully via uploaded PNG invoice",
        actual=f"Toast message received: '{toast}'" if is_success else f"Failed: {toast}",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Procurement with PNG invoice failed with toast message: '{toast}'"

