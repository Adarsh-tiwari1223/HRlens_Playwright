"""
HRlens Portal — Internal Mail Composer Test Suite.
Route: /internal-mail-composer

Scenarios Covered:
1. test_internal_mail_empty_recipient_validation
   - Validates validation toast when sending without recipient.
2. test_internal_mail_cascading_dropdown_dependency_states
   - Validates Company -> Branch -> Department disabled-to-enabled state transitions.
3. test_internal_mail_send_for_all_unfiltered
   - 'for all': Unfiltered global employee search and mail dispatch.
4. test_internal_mail_send_company_wise
   - 'company': Company-filtered employee search and mail dispatch.
5. test_internal_mail_send_company_plus_branch_wise
   - 'company + branch': Company + Branch filtered employee search and mail dispatch.
6. test_internal_mail_send_group_broadcast
   - Group broadcast mailing flow.
"""

import time
import pytest
import logging
from workflows.hrlense_portal.internal_mail.internal_mail_composer_workflow import (
    InternalMailComposerWorkflow,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def composer_workflow(logged_in_page) -> InternalMailComposerWorkflow:
    page, _ = logged_in_page("admin")
    workflow = InternalMailComposerWorkflow(page)
    workflow.open_fresh_composer()
    return workflow


@pytest.mark.regression
@pytest.mark.internal_mail
def test_internal_mail_empty_recipient_validation(
    composer_workflow: InternalMailComposerWorkflow,
):
    """
    Validates that attempting to send an internal mail without selecting a recipient
    triggers the validation toast: 'Select at least one recipient'.
    """
    logger.info("Executing Test: Empty recipient validation...")
    toast = composer_workflow.verify_empty_recipient_validation(
        subject="[Automation Test] Validation Check - No Recipient",
        body="This message should not be sent without a recipient.",
    )

    logger.info(f"Validation Toast Result: '{toast}'")
    assert "recipient" in toast.lower() or "select" in toast.lower(), (
        f"Expected recipient validation warning toast, but received: '{toast}'"
    )


@pytest.mark.regression
@pytest.mark.internal_mail
def test_internal_mail_cascading_dropdown_dependency_states(
    composer_workflow: InternalMailComposerWorkflow,
):
    """
    Validates the cascading filter dependency chain in Individual mode:
    1. Initial State:
       - Company: Enabled ('Select Company')
       - Branch: Disabled ('Select Company First')
       - Department: Disabled ('Select Branch First')
    2. After Company selected:
       - Branch: Enabled ('Select Branch')
    3. After Branch selected:
       - Department: Enabled ('Select Department')
    """
    logger.info("Executing Test: Cascading dropdown dependency states...")

    states = composer_workflow.verify_cascading_dropdown_dependency_states(
        company_name="TEK Inspirations LLC",
        branch_name="Varanasi",
    )

    # 1. Assert Initial State
    initial = states["initial"]
    assert "Company" in initial["company_text"], f"Unexpected initial company text: {initial['company_text']}"
    assert initial["branch_enabled"] is False, "Branch dropdown must be disabled before company selection"
    assert "Company First" in initial["branch_text"], f"Unexpected branch placeholder: {initial['branch_text']}"
    assert initial["dept_enabled"] is False, "Department dropdown must be disabled before branch selection"
    assert "Branch First" in initial["dept_text"], f"Unexpected department placeholder: {initial['dept_text']}"

    # 2. Assert After Company Selected
    after_company = states["after_company"]
    assert after_company["branch_enabled"] is True, "Branch dropdown must be enabled after company selection"
    assert "Select Branch" in after_company["branch_text"], f"Branch button should prompt 'Select Branch', got: {after_company['branch_text']}"

    # 3. Assert After Branch Selected
    after_branch = states["after_branch"]
    assert after_branch["dept_enabled"] is True, "Department dropdown must be enabled after branch selection"
    assert "Select Department" in after_branch["dept_text"], f"Department button should prompt 'Select Department', got: {after_branch['dept_text']}"


@pytest.mark.regression
@pytest.mark.internal_mail
def test_internal_mail_send_for_all_unfiltered(
    composer_workflow: InternalMailComposerWorkflow,
):
    """
    Scenario 1: 'for all'
    Validates global employee search (without Company or Branch filter)
    and sends internal mail to recipient with success toast assertion.
    """
    logger.info("Executing Test: Send mail 'for all' (unfiltered global employee search)...")
    screenshot_path = "reports/screenshots/composer_send_for_all_unfiltered.png"
    timestamp = int(time.time())
    subject = f"[Automation Test] Mail For All - {timestamp}"
    body = (
        f"Hello Sanidhy,<br><br>"
        f"This is an automated test verifying the 'for all' (global unfiltered) "
        f"employee search and mail sending flow.<br>"
        f"Timestamp: {timestamp}."
    )

    toast = composer_workflow.send_mail_for_all_unfiltered(
        employee_name="Sanidhy Tiwari",
        subject=subject,
        body=body,
        screenshot_path=screenshot_path,
    )

    logger.info(f"Send For All Toast: '{toast}'")
    assert "success" in toast.lower() or "sent" in toast.lower(), (
        f"Expected success toast when sending mail for all, got: '{toast}'"
    )


@pytest.mark.regression
@pytest.mark.internal_mail
def test_internal_mail_send_company_wise(
    composer_workflow: InternalMailComposerWorkflow,
):
    """
    Scenario 2: 'company'
    Validates company-filtered employee search (under 'TEK Inspirations LLC')
    and sends internal mail to recipient with success toast assertion.
    """
    logger.info("Executing Test: Send mail 'company' wise...")
    screenshot_path = "reports/screenshots/composer_send_company_wise.png"
    timestamp = int(time.time())
    subject = f"[Automation Test] Mail Company Wise - {timestamp}"
    body = (
        f"Hello Sanidhy,<br><br>"
        f"This is an automated test verifying the Company-filtered "
        f"employee search and mail sending flow.<br>"
        f"Timestamp: {timestamp}."
    )

    toast = composer_workflow.send_mail_company_wise(
        company_name="TEK Inspirations LLC",
        employee_name="Sanidhy Tiwari",
        subject=subject,
        body=body,
        screenshot_path=screenshot_path,
    )

    logger.info(f"Send Company Wise Toast: '{toast}'")
    assert "success" in toast.lower() or "sent" in toast.lower(), (
        f"Expected success toast when sending company-wise mail, got: '{toast}'"
    )


@pytest.mark.regression
@pytest.mark.internal_mail
def test_internal_mail_send_company_plus_branch_wise(
    composer_workflow: InternalMailComposerWorkflow,
):
    """
    Scenario 3: 'company + branch'
    Validates Company + Branch cascading filtered employee search
    ('TEK Inspirations LLC' -> 'Varanasi') and sends internal mail with success toast assertion.
    """
    logger.info("Executing Test: Send mail 'company + branch' wise...")
    screenshot_path = "reports/screenshots/composer_send_company_plus_branch_wise.png"
    timestamp = int(time.time())
    subject = f"[Automation Test] Mail Company+Branch Wise - {timestamp}"
    body = (
        f"Hello Sanidhy,<br><br>"
        f"This is an automated test verifying Company + Branch cascading "
        f"employee search and mail sending flow.<br>"
        f"Timestamp: {timestamp}."
    )

    toast = composer_workflow.send_mail_company_plus_branch_wise(
        company_name="TEK Inspirations LLC",
        branch_name="Varanasi",
        employee_name="Sanidhy Tiwari",
        subject=subject,
        body=body,
        screenshot_path=screenshot_path,
    )

    logger.info(f"Send Company+Branch Wise Toast: '{toast}'")
    assert "success" in toast.lower() or "sent" in toast.lower(), (
        f"Expected success toast when sending company+branch wise mail, got: '{toast}'"
    )


@pytest.mark.regression
@pytest.mark.internal_mail
def test_internal_mail_send_group_broadcast(
    composer_workflow: InternalMailComposerWorkflow,
):
    """
    Scenario 4: Group Broadcast
    Validates Group recipient selection and broadcast dispatch with success toast assertion.
    """
    logger.info("Executing Test: Send mail Group broadcast...")
    screenshot_path = "reports/screenshots/composer_send_group_broadcast.png"
    timestamp = int(time.time())
    subject = f"[Automation Test] Mail Group Broadcast - {timestamp}"
    body = (
        f"Team,<br><br>"
        f"This is an automated test verifying the Group / Branch broadcast mail flow.<br>"
        f"Timestamp: {timestamp}."
    )

    toast = composer_workflow.send_mail_group_wise(
        target_name="Varanasi",
        subject=subject,
        body=body,
        screenshot_path=screenshot_path,
    )

    logger.info(f"Send Group Broadcast Toast: '{toast}'")
    assert "success" in toast.lower() or "sent" in toast.lower(), (
        f"Expected success toast when sending group broadcast mail, got: '{toast}'"
    )
