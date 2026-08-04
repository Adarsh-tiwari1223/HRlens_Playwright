"""
UI Tests for Payroll Company Master Module.
Follows 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
"""

import logging
import pytest
from pages.hrlense_portal.master.payroll_company_page import PayrollCompanyPage
from workflows.hrlense_portal.master.payroll_company_workflow import PayrollCompanyWorkflow
from testdata.dynamic.business_test_data import DirectorTestData

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.payroll_company
def test_payroll_company_add_manual_director_and_verify_api(admin_page):
    """
    Verify adding a manual director during Payroll Company creation/edit
    and verifying the posted director record in API.
    """
    logger.info("Verify manual director addition in Payroll Company and API verification")
    d_data = DirectorTestData.generate_manual_director()

    payroll_page = PayrollCompanyPage(admin_page)
    payroll_page.open_add_payroll_company_modal()

    workflow = PayrollCompanyWorkflow(admin_page)
    res = workflow.add_manual_director_workflow(
        name=d_data["name"],
        email=d_data["email"],
        phone=d_data["phone"]
    )

    assert res["posted_record"], "Posted director record should be retrieved from Payroll Company form"
    assert res["api_verified"], f"Newly added manual director '{d_data['name']}' should be verified in backend API"

    # Close modal
    admin_page.get_by_role("button", name="Cancel").click()
