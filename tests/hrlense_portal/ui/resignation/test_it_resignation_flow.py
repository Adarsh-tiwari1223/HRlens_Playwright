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
@pytest.mark.parametrize("target_employee_name", ["Sanidhy Tiwari", "Adarsh Tiwari"], ids=["sanidhy", "adarsh_tiwari"])
def test_it_person_asset_clearance_inspection(get_it_resignation_workflow, target_employee_name):
    """
    IT Person Asset Clearance Flow:
    1. IT Person logs in (it_varanasi_ashutosh)
    2. Navigates Offboarding -> Resignation Approval / IT Task Clearance
    3. Searches resigning employee (target_employee_name)
    4. Dynamically processes IT Clearance:
       - If employee HAS assets: Inspects asset condition & confirms return.
       - If employee HAS NO assets: Verifies and completes task directly.
    """
    it_wf = get_it_resignation_workflow("it_varanasi_ashutosh")

    result = it_wf.inspect_and_clear_employee_assets_workflow(
        employee_name=target_employee_name,
        asset_condition="Good Condition",
        remarks="IT Asset clearance verified & completed"
    )

    assert result.get("success"), f"Failed IT Clearance for '{target_employee_name}'"
    logger.info(f"[PASS IT] IT Asset Clearance executed for '{target_employee_name}'! Has Assets: {result.get('has_assets')}, Toast: '{result.get('toast')}'")


