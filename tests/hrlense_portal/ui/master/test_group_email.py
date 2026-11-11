"""
UI Test Suite for Group Email Master (HR Lens Portal -> Master Module).
Target URL: /master/group-email

Architecture:
Tests (test_group_email.py)
  ↓
Workflows (GroupEmailWorkflow)
  ↓
Page Objects (GroupEmailPage)
  ↓
BasePage / Core Infrastructure
"""

import os
import shutil
import time
import pytest
from playwright.sync_api import expect
from pages.hrlense_portal.master.group_email_page import GroupEmailPage
from workflows.hrlense_portal.master.group_email_workflow import GroupEmailWorkflow
from utils.logger import log_test_start, log_step, log_pass

# Screenshot output directories
PROJECT_SCREENSHOT_DIR = os.path.join(os.getcwd(), "reports", "screenshots")
ARTIFACT_DIR = r"C:\Users\User\.gemini\antigravity\brain\64b80c08-6b00-4518-a5fa-6ec128c13e30"

os.makedirs(PROJECT_SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)


def _save_screenshot_pair(page, filename: str) -> str:
    """Saves screenshot to both project reports/screenshots and artifact directory."""
    proj_path = os.path.join(PROJECT_SCREENSHOT_DIR, filename)
    art_path = os.path.join(ARTIFACT_DIR, filename)
    page.screenshot(path=proj_path)
    try:
        shutil.copy2(proj_path, art_path)
    except Exception:
        pass
    return proj_path


@pytest.mark.ui
@pytest.mark.master
@pytest.mark.group_email
@pytest.mark.regression
class TestGroupEmailMasterSpec:
    """Test scenarios for Group Email Master page using 3-Tier Architecture."""

    EXPECTED_TABS = [
        "Company",
        "Branch",
        "Branch + Department",
        "Branch Group",
        "Branch Group + Department",
        "Global",
    ]

    def test_group_email_overview_and_tabs(self, logged_in_page):
        """
        Validates core page overview via GroupEmailWorkflow:
        1. Navigates to /master/group-email.
        2. Asserts all 6 expected tabs are visible including newly added 'Global'.
        3. Asserts default active tab is 'Company'.
        4. Asserts grid headers match expected columns ('S.NO', 'COMPANY NAME', 'EMAIL').
        5. Asserts table rows are loaded.
        6. Captures full screenshot evidence.
        """
        log_test_start(module="Master", phase="Group Email", test="Verify Overview & Tabs")
        page, _ = logged_in_page("admin")
        workflow = GroupEmailWorkflow(page)

        log_step("Load Group Email Overview")
        overview = workflow.load_group_email_overview()

        # Validate Tabs
        for expected_tab in self.EXPECTED_TABS:
            assert any(expected_tab.lower() in t.lower() for t in overview["available_tabs"]), (
                f"Expected tab '{expected_tab}' not found in available tabs: {overview['available_tabs']}"
            )

        # Validate Active Tab
        assert "company" in overview["active_tab"].lower(), (
            f"Expected default active tab to be 'Company', but got '{overview['active_tab']}'"
        )

        # Validate Headers for Company Tab
        headers_upper = [h.upper() for h in overview["headers"]]
        assert any("S.NO" in h or "S. NO" in h or "SR" in h for h in headers_upper), (
            f"Expected S.NO column in headers: {overview['headers']}"
        )
        assert any("COMPANY" in h for h in headers_upper), (
            f"Expected COMPANY NAME column in headers: {overview['headers']}"
        )
        assert any("EMAIL" in h for h in headers_upper), (
            f"Expected EMAIL column in headers: {overview['headers']}"
        )

        # Validate Rows
        assert overview["row_count"] > 0, "Expected company rows to be displayed, but got 0"

        # Capture evidence screenshot
        _save_screenshot_pair(page, "group_email_test1_overview.png")

        log_pass()

    def test_group_email_tabs_switching(self, logged_in_page):
        """
        Validates navigation across all tabs on the Group Email page:
        Iterates through Branch, Branch + Department, Branch Group, Branch Group + Department, and Global,
        asserting column headers and table visibility for each.
        Captures screenshot evidence of tab switching.
        """
        log_test_start(module="Master", phase="Group Email", test="Verify Tab Switching")
        page, _ = logged_in_page("admin")
        workflow = GroupEmailWorkflow(page)

        # Ensure base page is loaded
        workflow.load_group_email_overview()

        tabs_to_verify = [
            "Branch",
            "Branch + Department",
            "Branch Group",
            "Branch Group + Department",
            "Global",
        ]

        for tab_name in tabs_to_verify:
            log_step(f"Switch to tab '{tab_name}'")
            tab_info = workflow.inspect_tab_structure(tab_name)

            headers_upper = [h.upper() for h in tab_info["headers"]]
            assert any("EMAIL" in h or "RECIPIENT" in h for h in headers_upper), (
                f"Expected EMAIL or RECIPIENTS column in headers for tab '{tab_name}', got: {tab_info['headers']}"
            )

        # Capture screenshot of the switched tabs (Global view)
        _save_screenshot_pair(page, "group_email_test2_tabs_global.png")

        log_pass()

    def test_group_email_global_tab_structure_and_records(self, logged_in_page):
        """
        Deep validation of the newly added 'Global' tab in Group Email Master:
        1. Navigates to /master/group-email and switches to 'Global' tab.
        2. Asserts active tab is 'Global'.
        3. Asserts required columns: 'S.NO', 'GROUP SCOPE', 'CONFIGURED RECIPIENTS', 'TOTAL RECIPIENTS', 'STATUS'.
        4. Asserts rows are populated and structured data exists.
        5. Captures screenshot evidence of the Global tab.
        """
        log_test_start(module="Master", phase="Group Email", test="Verify Global Tab Details")
        page, _ = logged_in_page("admin")
        workflow = GroupEmailWorkflow(page)

        workflow.load_group_email_overview()

        log_step("Switch to 'Global' tab and inspect structure")
        global_screenshot = os.path.join(PROJECT_SCREENSHOT_DIR, "group_email_global_tab_deep_view.png")
        global_info = workflow.inspect_global_tab_details(screenshot_path=global_screenshot)

        try:
            shutil.copy2(global_screenshot, os.path.join(ARTIFACT_DIR, "group_email_global_tab_deep_view.png"))
        except Exception:
            pass

        # Assert Active Tab
        active_tab = workflow.group_email_page.get_active_tab_name()
        assert "global" in active_tab.lower(), f"Expected active tab 'Global', but got '{active_tab}'"

        # Assert Expected Headers for Global tab
        headers_upper = [h.upper() for h in global_info["headers"]]
        expected_columns = ["S.NO", "GROUP SCOPE", "CONFIGURED RECIPIENTS", "TOTAL RECIPIENTS", "STATUS"]
        for col in expected_columns:
            assert any(col in h for h in headers_upper), (
                f"Expected column '{col}' in Global tab headers: {global_info['headers']}"
            )

        # Assert row count
        assert global_info["row_count"] > 0, "Expected at least 1 row in Global tab table"

        # Assert each row has group scope defined
        for row in global_info["rows_data"]:
            assert "group_scope" in row and row["group_scope"] != "", (
                f"Row {row.get('row_index')} missing group scope: {row}"
            )

        log_pass()

    def test_group_email_invalid_format_validation(self, logged_in_page):
        """
        Validates email format validation:
        1. Selects Company tab.
        2. Inputs an invalid email string ('invalid_email_no_domain').
        3. Presses Enter and verifies 'Invalid email format' toast notification.
        4. Captures screenshot evidence showing the toast message.
        5. Safely restores original email.
        """
        log_test_start(module="Master", phase="Group Email", test="Invalid Email Validation")
        page, _ = logged_in_page("admin")
        workflow = GroupEmailWorkflow(page)

        workflow.load_group_email_overview()

        log_step("Test invalid email format submission")
        screenshot_file = os.path.join(PROJECT_SCREENSHOT_DIR, "group_email_test3_invalid_toast.png")
        toast = workflow.validate_invalid_email_format(
            tab_name="Company",
            row_index=0,
            invalid_email="invalid_email_no_domain",
            screenshot_path=screenshot_file
        )

        try:
            shutil.copy2(screenshot_file, os.path.join(ARTIFACT_DIR, "group_email_test3_invalid_toast.png"))
        except Exception:
            pass

        assert "invalid email format" in toast.lower() or "invalid" in toast.lower(), (
            f"Expected invalid email format toast, but got: '{toast}'"
        )
        log_pass()

    def test_group_email_update_and_revert_lifecycle(self, logged_in_page):
        """
        Validates end-to-end update and safe data rollback:
        1. Reads current email of first record.
        2. Updates to a unique valid test email address.
        3. Captures screenshot evidence of the updated email.
        4. Asserts update toast / persisted input value.
        5. Reverts cleanly back to the original email to prevent test data pollution.
        """
        log_test_start(module="Master", phase="Group Email", test="Update & Rollback Lifecycle")
        page, _ = logged_in_page("admin")
        workflow = GroupEmailWorkflow(page)

        workflow.load_group_email_overview()

        unique_email = f"autotest_{int(time.time())}@jobvritta.com"
        log_step(f"Update email to '{unique_email}' and revert")

        screenshot_file = os.path.join(PROJECT_SCREENSHOT_DIR, "group_email_test4_updated_field.png")
        result = workflow.update_and_revert_email(
            tab_name="Company",
            row_index=0,
            new_email=unique_email,
            screenshot_path=screenshot_file
        )

        try:
            shutil.copy2(screenshot_file, os.path.join(ARTIFACT_DIR, "group_email_test4_updated_field.png"))
        except Exception:
            pass

        # Assert update succeeded or persisted
        assert result["persisted_email"] == unique_email or "success" in result["update_toast"].lower() or "updated" in result["update_toast"].lower(), (
            f"Expected email to update to '{unique_email}', got '{result['persisted_email']}', toast: '{result['update_toast']}'"
        )

        # Assert restored back to original
        assert result["restored_email"] == result["original_email"], (
            f"Expected restored email to match original '{result['original_email']}', got '{result['restored_email']}'"
        )

        log_pass()
