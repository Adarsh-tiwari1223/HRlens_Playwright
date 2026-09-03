"""
HRlens Portal — IT Person Resignation Flow Test Suite (Test Tier).
Contains test cases for IT Person-side offboarding clearance, asset recovery inspection, and IT clearance approval.
"""

import pytest
import logging
from core.config import settings
from workflows.hrlense_portal.resignation.it_resignation_workflow import ItResignationWorkflow

logger = logging.getLogger(__name__)


@pytest.fixture
def get_it_resignation_workflow(logged_in_page):
    """Factory fixture to initialize ItResignationWorkflow for a Branch IT Person account."""
    def _create_workflow(user_key: str = "it_varanasi_ashutosh"):
        page, _ = logged_in_page(user_key)
        return ItResignationWorkflow(page)
    return _create_workflow


@pytest.mark.ui
@pytest.mark.it_clearance
@pytest.mark.resignation
def test_it_person_asset_clearance_inspection(get_it_resignation_workflow):
    """
    IT Person Asset Clearance Flow:
    1. IT Person logs in (it_varanasi_ashutosh / it_varanasi_tejasav)
    2. Navigates Offboarding -> IT Clearance / Asset Clearance tab
    3. Searches resigning employee (e.g. Abhishek Singh / Adarsh Tiwari)
    4. Inspects assigned assets and verifies IT clearance status
    """
    it_wf = get_it_resignation_workflow("it_varanasi_ashutosh")
    target_employee_name = "Abhishek Singh"

    result = it_wf.inspect_and_clear_employee_assets_workflow(
        employee_name=target_employee_name,
        asset_condition="Good Condition"
    )

    logger.info(f"[PASS IT] IT Asset Clearance inspection executed for '{target_employee_name}'! Result: {result}")

