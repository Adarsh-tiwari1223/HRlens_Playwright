"""
HRlens Portal — Released Employee Exit Letters Dispatch & Live Preview Verification Test Suite.

Scope:
1. HR logs in and navigates to /released-employee.
2. Locates an eligible released employee (e.g. Sanidhy Tiwari).
3. For Relieving Letter:
   - Opens letter preview via Actions (≡) menu.
   - Edits content in left-side SunEditor.
   - Asserts dynamic synchronization into right-side Live Preview.
   - Selects Signatory (Vivekanand Singh — Default).
   - Sends letter to employee and captures confirmation toast.
   - Clicks Back button to return to table.
4. For Experience Letter:
   - Opens letter preview via Actions (≡) menu.
   - Edits content in left-side SunEditor.
   - Asserts dynamic synchronization into right-side Live Preview.
   - Selects Signatory (Vivekanand Singh — Default).
   - Sends letter to employee and captures confirmation toast.
   - Clicks Back button to return to table.
5. For Full & Final Settlement Letter:
   - Opens letter preview via Actions (≡) menu.
   - Selects Signatory (Vivekanand Singh — Default).
   - Sends letter to employee and captures confirmation toast.
   - Clicks Back button to return to table.
6. Validates letter statuses on /released-employee table.
"""

import logging
import pytest
from playwright.sync_api import Page

from pages.base_page import TestStoryLogger
from workflows.hrlense_portal.resignation.hr_resignation_workflow import HrResignationWorkflow

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.resignation
@pytest.mark.released_employee
def test_released_employee_letters_dispatch_and_sync(logged_in_page, request):
    """
    Test HR Letter Dispatch on /released-employee with left-to-right live preview sync verification.
    """
    story = TestStoryLogger(request, "HR Released Employee Letter Dispatch & Sync")
    target_employee = "Sanidhy Tiwari"
    hr_key = "tejaswini"

    # Step 1: HR Session Login via session pool
    logger.info(f"Obtaining HR ({hr_key}) session for released letters dispatch...")
    hr_page, _ = logged_in_page(hr_key)
    hr_wf = HrResignationWorkflow(hr_page)
    story.log_step("HR Session Setup", record=f"HR Key: {hr_key}", expected="HR session ready", actual="Ready", status="PASS")

    # Step 2: Custom contents to verify left-side editor synchronization to right-side Live Preview
    custom_content = {
        "Relieving Letter": f"[Verified Live Relieving Note for {target_employee} by HR]",
        "Experience Letter": f"[Verified Live Experience Endorsement for {target_employee} by HR]"
    }

    # Step 3: Execute letter dispatch and preview sync verification workflow
    logger.info(f"Executing letter dispatch workflow for '{target_employee}'...")
    result = hr_wf.execute_send_released_employee_letters_workflow(
        employee_name=target_employee,
        letters=["Relieving Letter", "Experience Letter", "Full & Final Settlement"],
        custom_content_map=custom_content,
        verify_sync=True,
        signatory_index=1
    )

    logger.info(f"Released Letters Dispatch Result: {result}")
    story.log_step(
        "Dispatch Released Letters",
        record=f"Dispatches: {result.get('dispatches')} | Sync: {result.get('sync_verifications')}",
        expected="All 3 letters dispatched and live previews synchronized",
        actual=str(result),
        status="PASS" if result.get("success") else "FAIL"
    )

    # Assertions
    assert result.get("success"), f"Released employee letter dispatch failed: {result}"
    for letter, synced in result.get("sync_verifications", {}).items():
        assert synced, f"Live preview failed to synchronize edits for '{letter}'"
        story.log_step(f"Sync Verification: {letter}", record=f"Synced: {synced}", expected="Live Preview matches Editor", actual="Matches", status="PASS")
