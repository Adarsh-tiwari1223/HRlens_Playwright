"""
UI Tests for Payroll Company Master Module.
Follows 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
"""

import logging
import pytest
from workflows.hrlense_portal.master.payroll_company_workflow import PayrollCompanyWorkflow
from testdata.dynamic.business_test_data import BusinessTestData, DirectorTestData

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.payroll_company
def test_payroll_company_add_manual_director_on_create(admin_page):
    """
    ADD Operation:
    Fill Payroll Company form from scratch and add a manual director.
    """
    logger.info("Testing ADD Payroll Company operation: fill form from scratch and add manual director")
    import random
    from faker import Faker
    fake = Faker()
    
    comp_info = {
        "company_name": f"Payroll Co {random.randint(100, 999)} Pvt Ltd",
        "address": f"{fake.building_number()} {fake.street_name()}",
        "zip_code": "110001",
        "country": "India",
        "state": "Delhi",
        "city": "New Delhi",
        "code": f"PRL-{random.randint(1000, 9999)}"
    }
    d_data = DirectorTestData.generate_manual_director()

    workflow = PayrollCompanyWorkflow(admin_page)
    toast = workflow.create_payroll_company_with_manual_director_from_scratch(comp_info, d_data)
    logger.info(f"Create Payroll Company Toast: {toast}")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.payroll_company
def test_payroll_company_add_manual_director_on_edit(admin_page):
    """
    EDIT Operation:
    Open existing Payroll Company in edit mode and just add a manual director.
    """
    logger.info("Testing EDIT Payroll Company operation: open existing company and just add manual director")
    existing_payroll = BusinessTestData.get_payroll_companies()
    target_comp = existing_payroll[0].get("payrollCompanyName") if existing_payroll else "Adventa"
    d_data = DirectorTestData.generate_manual_director()

    workflow = PayrollCompanyWorkflow(admin_page)
    toast = workflow.edit_payroll_company_add_manual_director_only(target_comp, d_data)
    logger.info(f"Edit Payroll Company Toast: {toast}")
