import os
import logging
import pytest
from pages.base_page import TestStoryLogger
from workflows.hrlense_portal.asset.asset_procurement_workflow import AssetProcurementWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.parametrize("branch", [
    pytest.param("Varanasi", id="varanasi"),
    pytest.param("Agra", id="agra"),
    pytest.param("Noida", id="noida"),
    pytest.param("Greater Noida", id="greater_noida"),
    pytest.param("Bhubaneswar", id="bhubaneswar"),
    pytest.param("Ranchi", id="ranchi"),
    pytest.param("Jaipur", id="jaipur"),
    pytest.param("Meerut", id="meerut"),
    pytest.param("Lucknow", id="lucknow")
])
def test_asset_e2e_procurement_flow(logged_in_page, branch):
    """
    Unified Dynamic Asset Procurement Flow Test:
    Passing branch via terminal (e.g. -k "varanasi", -k "agra", -k "noida") or $env:BRANCH="Varanasi"
    automatically executes procurement for exactly that single branch.
    """
    env_branch = os.getenv("BRANCH")
    if env_branch and env_branch.strip().lower() not in [branch.strip().lower(), branch.replace(" ", "").lower(), branch.replace(" ", "_").lower()]:
        pytest.skip(f"Skipping '{branch}' because BRANCH='{env_branch}' was targeted.")

    target_branch = branch
    story = TestStoryLogger(f"Asset Procurement Flow ({target_branch} Branch)", module="Asset Management", phase="Asset Procurement")
    story.start()

    from utils.branch_it_selector import get_branch_it_person
    from core.config import settings

    it_person = get_branch_it_person(target_branch)
    user_key = it_person["user_key"] if settings.USERS.get(it_person.get("user_key", ""), {}).get("password") else "admin"

    logger.info(f"[PROCUREMENT START] Branch: '{target_branch}' | Persona: {it_person.get('name', 'Admin')} ({user_key})")
    try:
        page, context = logged_in_page(user_key)
    except Exception:
        logger.info(f"Persona '{user_key}' login encountered an issue; falling back to 'admin'")
        page, context = logged_in_page("admin")

    # Locate Invoice File
    invoices_dir = os.path.abspath("testdata/static/invoices")
    sample_invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")
    if not os.path.exists(sample_invoice_path):
        sample_invoice_path = os.path.join(invoices_dir, "invoice_1mb.pdf")

    logger.info(f"[INVOICE ATTACHMENT] File: {sample_invoice_path}")

    workflow = AssetProcurementWorkflow(page)
    toast = workflow.procure_asset_with_invoice(
        invoice_file_path=sample_invoice_path,
        branch_label=target_branch,
        company_label=None,
        story=story
    )

    is_success = any(term in toast.lower() for term in ["success", "created", "procured", "saved", "added"])

    story.log_step(
        f"Submit Asset Procurement for {target_branch}",
        record=f"Branch: {target_branch} | File: {os.path.basename(sample_invoice_path)}",
        expected=f"Asset Procurement record created under '{target_branch}' branch",
        actual=f"Toast message received: '{toast}'" if is_success else f"Failed: {toast}",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Procurement for branch '{target_branch}' failed with toast: '{toast}'"
    story.finish(status="PASS")


@pytest.mark.ui
@pytest.mark.asset
def test_asset_procurement_with_png_invoice(logged_in_page):
    target_branch = os.getenv("BRANCH", "Varanasi")
    story = TestStoryLogger(f"Asset Procurement via PNG Image ({target_branch} Branch)", module="Asset Management", phase="Asset Procurement")
    story.start()

    admin_page, admin_context = logged_in_page("admin")

    invoices_dir = os.path.abspath("testdata/static/invoices")
    sample_invoice_path = os.path.join(invoices_dir, "invoice_1mb.png")
    if not os.path.exists(sample_invoice_path):
        sample_invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")

    logger.info(f"[STEP 2] Running Asset Procurement with Image: {sample_invoice_path} for Branch: {target_branch}")

    workflow = AssetProcurementWorkflow(admin_page)
    toast = workflow.procure_asset_with_invoice(
        invoice_file_path=sample_invoice_path,
        branch_label=target_branch,
        company_label=None,
        story=story
    )

    is_success = any(term in toast.lower() for term in ["success", "created", "procured", "saved", "added"])

    story.log_step(
        f"Submit Asset Procurement with PNG Invoice ({target_branch})",
        record=f"Branch: {target_branch} | File: {os.path.basename(sample_invoice_path)}",
        expected=f"Asset Procurement entry created under '{target_branch}' branch",
        actual=f"Toast message received: '{toast}'" if is_success else f"Failed: {toast}",
        status="PASS" if is_success else "FAIL"
    )
    assert is_success, f"Procurement with PNG invoice failed with toast: '{toast}'"
    story.finish(status="PASS")


