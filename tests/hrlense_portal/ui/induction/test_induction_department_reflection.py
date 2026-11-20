"""
Test Suite for Phase 1: Department Induction Policy Content Editing & Live Reflection Verification.
Covers:
1. Inspection of all Department Induction Policies in /master/induction-policy (STEP 4: Department).
2. Editing Department policy content as Admin, verifying table update.
3. Verifying that the edited department content dynamically reflects into the Employee Induction module (/induction).
4. Safe, non-destructive rollback of all edited policy content.
"""

import pytest
from workflows.hrlense_portal.induction.induction_department_workflow import InductionDepartmentWorkflow


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.induction
@pytest.mark.induction_department
class TestInductionDepartmentReflection:
    """Test suite for Induction Master Department editing and /induction reflection."""

    def test_inspect_all_department_induction_policies(self, admin_page):
        """
        Verifies that navigating to /master/induction-policy and selecting STEP 4: Department:
        1. Renders the content table for Step 4.
        2. Retrieves all department-specific policy rows.
        3. Asserts standard headers (#, CATEGORY TAG, TITLE / HEADING, TARGET AUDIENCE, CONTENT SNIPPET, ACTIVE, ACTIONS).
        4. Logs all available department policies and target audiences.
        """
        workflow = InductionDepartmentWorkflow(admin_page)
        department_policies = workflow.get_all_department_policies()

        assert len(department_policies) > 0, "No Department policies found in STEP 4: Department!"
        print(f"\n[TEST PASS] Retrieved {len(department_policies)} Department Policy rows in Step 4:")
        for idx, row in enumerate(department_policies):
            print(f"  [{idx}] Title: {row.get('TITLE / HEADING')} | Audience: {row.get('TARGET AUDIENCE')} | Snippet: {row.get('CONTENT SNIPPET', '')[:60]}...")

        # Assert mandatory columns
        headers = workflow.policy_page.get_table_headers()
        for col in ["CATEGORY", "TITLE", "TARGET", "CONTENT", "ACTIVE", "ACTIONS"]:
            assert any(col in h.upper() for h in headers), f"Column '{col}' missing from headers: {headers}"

    def test_edit_department_content_and_verify_reflection_on_induction(self, admin_page, logged_in_page):
        """
        Phase 1 Verification Flow:
        1. Admin Persona: Selects STEP 4: Department in /master/induction-policy.
        2. Identifies the policy row for 'Developer' department.
        3. Edits the content snippet, appending a unique test verification marker: '[Auto-Verified-Reflected-2026]'.
        4. Saves and verifies the content is updated in the master policy table.
        5. Employee Persona: Logs in as an employee belonging to the Developer department ('adarsh').
        6. Navigates to /induction, completes the welcome journey, and inspects slides & chapters.
        7. Asserts that the test marker is successfully reflected on the employee's induction screen.
        8. Rollback: Restores the original department content in /master/induction-policy.
        """
        workflow = InductionDepartmentWorkflow(admin_page)
        dept_rows = workflow.get_all_department_policies()
        assert len(dept_rows) > 0, "No department policy rows found to edit!"

        # Identify Developer or first available department row
        target_index = 0
        for idx, row in enumerate(dept_rows):
            audience = row.get("TARGET AUDIENCE", "").upper()
            title = row.get("TITLE / HEADING", "").upper()
            if "DEVELOPER" in audience or "DEVELOPER" in title:
                target_index = idx
                break

        target_row = dept_rows[target_index]
        print(f"\n[TEST INFO] Selected target department row [{target_index}]: '{target_row.get('TITLE / HEADING')}' (Audience: {target_row.get('TARGET AUDIENCE')})")

        test_marker = "[Auto-Verified-Reflected-2026]"
        edit_result = None

        try:
            # 1. Edit Department Content as Admin
            edit_result = workflow.edit_department_content(row_index=target_index, test_marker=test_marker)
            print(f"[TEST PASS] Successfully edited Department policy row {target_index} with test marker.")

            # 2. Employee Persona verifies reflection on /induction
            emp_page, _ = logged_in_page(user_key="employee")
            reflection_result = workflow.verify_content_reflection_on_induction(
                test_marker=test_marker,
                employee_page=emp_page
            )

            print(f"[TEST RESULT] Live Reflection Status: {reflection_result['reflected']} | Location: {reflection_result['matched_location']}")
            assert reflection_result["reflected"], (
                f"Edited department policy marker '{test_marker}' was NOT reflected on employee /induction! "
                f"Checked {reflection_result['total_slides_checked']} slides and all interactive chapters."
            )

            print(f"[TEST PASS] Live Reflection Confirmed in: {reflection_result['matched_location']}")

        finally:
            # 3. Guaranteed Rollback to preserve staging data
            if edit_result and edit_result.get("original_content"):
                print("[TEST CLEANUP] Rolling back department content to original state...")
                workflow.revert_department_content(
                    row_index=target_index,
                    original_title=edit_result["original_title"],
                    original_content=edit_result["original_content"]
                )
                print("[TEST CLEANUP] Rollback completed successfully.")
