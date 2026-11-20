"""
End-to-End Test Suite for Centralized Induction Scoped Control Workflow.
Validates:
1. Master Induction Policy Scoping Matrix (/master/induction-policy):
   - Multi-scope filtering by Company, Branch, and Department.
   - Correctness of the TARGET AUDIENCE tag ('ALL' vs specific entity).
   - Scoping isolation (e.g. Developer vs Accounts).
2. Employee-Facing Scoped Content Enforcement (/induction):
   - Real employee ('adarsh' -> TEK Inspirations LLC / Varanasi / Developer).
   - Validation that slides and chapters dynamically load the in-scope content.
3. Induction AI Guide (Sufi) Scoped Knowledge:
   - Verifies Sufi's conversational guidance reflects organizational policies.
"""

import pytest
from workflows.hrlense_portal.induction.induction_scoping_e2e_workflow import InductionScopingE2EWorkflow


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.induction
@pytest.mark.scoped_control
class TestInductionScopedWorkflow:
    """Test suite for Centralized Induction Scoped Control Workflow."""

    def test_induction_master_scoped_matrix_filtering(self, admin_page):
        """
        Verifies Admin centralized scoping controls in /master/induction-policy:
        1. Confirms Company, Branch, and Department options are populated.
        2. Filters the content table by Department ('Developer').
        3. Asserts every displayed row's TARGET AUDIENCE contains 'DEVELOPER' or 'ALL'.
        4. Verifies clearing filters restores full organizational content.
        """
        workflow = InductionScopingE2EWorkflow(admin_page)
        scoping_res = workflow.verify_master_centralized_scoping_matrix(
            company_name="TEK Inspirations LLC",
            branch_name="Varanasi",
            department_name="Developer"
        )

        assert len(scoping_res["available_companies"]) > 0, "No Company options in scoping dropdown!"
        assert len(scoping_res["available_departments"]) > 0, "No Department options in scoping dropdown!"
        assert scoping_res["developer_count"] > 0, "No content records matched Developer scope!"
        assert scoping_res["restored_count"] == scoping_res["baseline_count"], "Restoring scopes did not return baseline rows!"

        print(
            f"[TEST PASS] Centralized Scoping Matrix verified: "
            f"Baseline={scoping_res['baseline_count']}, "
            f"Developer Scoped={scoping_res['developer_count']}, "
            f"Restored={scoping_res['restored_count']}"
        )

    def test_employee_induction_scoped_content_enforcement(self, logged_in_page):
        """
        Verifies Employee-facing scoped content resolution in /induction:
        1. Authenticates as employee 'adarsh' (TEK Inspirations LLC / Varanasi / Developer).
        2. Navigates to /induction, completes welcome slides, and enters Chapter View.
        3. Verifies interactive chapters are loaded and accessible.
        4. Validates that chapter structure matches in-scope policies.
        """
        employee_page, _ = logged_in_page(user_key="adarsh")
        workflow = InductionScopingE2EWorkflow(employee_page)

        journey_res = workflow.verify_employee_scoped_induction_journey(
            expected_employee_name="Adarsh Tiwari",
            expected_company="TEK Inspirations LLC",
            expected_department="Developer"
        )

        assert journey_res["chapter_view_active"], "Employee failed to reach active Chapter View in /induction!"
        chapter = journey_res["first_chapter"]
        assert bool(chapter["title"] or chapter["badge"] or chapter["body"]), "Initial chapter loaded with empty content!"

        print(
            f"[TEST PASS] Employee Scoped Induction Journey verified for Adarsh Tiwari: "
            f"Chapter Title='{chapter.get('title')}', Badge='{chapter.get('badge')}'"
        )

    def test_induction_sufi_chatbot_scoped_knowledge(self, logged_in_page):
        """
        Verifies Induction AI Guide (Sufi) scoped knowledge:
        1. Authenticates as employee 'adarsh'.
        2. Navigates to /induction and opens Sufi AI Guide drawer.
        3. Queries Sufi regarding office timings and leave policy.
        4. Validates that Sufi generates a substantive, policy-relevant response.
        """
        employee_page, _ = logged_in_page(user_key="adarsh")
        workflow = InductionScopingE2EWorkflow(employee_page)

        # Ensure chapter view is open before querying Sufi
        workflow.induction_page.navigate_to_induction()
        if workflow.induction_page.is_welcome_slide_visible():
            workflow.induction_page.advance_welcome_slides(selected_guide="Sufi")

        query = "What are the office timings and leave policy?"
        chat_res = workflow.verify_sufi_ai_guide_scoped_responses(query=query)

        assert chat_res["is_valid"], f"Sufi AI Guide returned an invalid or empty response: '{chat_res['bot_reply']}'"
        print(f"[TEST PASS] Sufi AI Guide responded with scoped guidance: '{chat_res['bot_reply'][:120]}...'")
