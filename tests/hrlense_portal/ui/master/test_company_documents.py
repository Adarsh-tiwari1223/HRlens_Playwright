"""
UI Test Suite for Company Documents Module (HR Lens Portal).
Follows strict 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Validates Multiple Delete (Bulk Delete) checkbox functionality (Rashi's Report S.No 4).
"""

import pytest
from pages.login_page import LoginPage
from workflows.hrlense_portal.master.company_documents_workflow import CompanyDocumentsWorkflow
from core.config import settings
from utils.logger import log_test_start, log_pass, log_skip, log_debug


@pytest.fixture
def admin_page(page):
    """Logs in as Admin user."""
    page.goto(f"{settings.BASE_URL}/login", timeout=60000)
    creds = settings.USERS["admin"]
    LoginPage(page).login(creds["username"], creds["password"])
    return page


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.company_documents
def test_bulk_delete_company_documents(admin_page):
    """
    S.No 4: Multiple Delete option in Company Documents module.
    Validates selecting multiple document checkboxes and deleting them in bulk.
    """
    log_test_start(module="Company Documents", phase="S.No 4", test="Validate Multiple Delete (Bulk Delete)")

    workflow = CompanyDocumentsWorkflow(admin_page)
    initial_count, post_count, selected_names, toast = workflow.bulk_delete_company_documents_workflow(delete_count=2)

    if toast == "NO_DOCUMENTS_TO_DELETE":
        log_skip("No existing company documents in repository to perform bulk deletion.")
        pytest.skip("No company documents available for bulk deletion.")

    assert toast and ("success" in toast.lower() or "deleted" in toast.lower() or "removed" in toast.lower()), f"Bulk delete failed! Toast: '{toast}'"

    # Verify bulk deletion result
    is_removed = workflow.verify_documents_deleted(toast)
    assert is_removed, f"Bulk deletion verification failed for toast: '{toast}'!"

    log_pass()
