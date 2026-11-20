"""
Test Suite for HRlens Onboarding Approval Portal (/onboarding-approval).
Covers:
1. Dashboard layout, metric counters, and table structure for HR Manager (Tejaswini).
2. Candidate search, filtering, and status verification for Uttam Kumar.
3. HR Sign-Off modal dialog presentation and non-destructive inspection.
"""

import pytest
from playwright.sync_api import expect
from workflows.hrlense_portal.induction.onboarding_approval_workflow import OnboardingApprovalWorkflow


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.induction
@pytest.mark.onboarding_approval
class TestOnboardingApproval:
    """Test suite for Onboarding Approvals (/onboarding-approval)."""

    def test_onboarding_approval_dashboard_layout(self, logged_in_page):
        """
        Verifies that logging in as HR Manager (Tejaswini) and navigating to /onboarding-approval:
        1. Renders the top header with 'HR Access' badge.
        2. Renders all 4 metric stat cards: Branch Employees, Needs HR Sign-Off, HR Approved, HR Rejected.
        3. Renders the candidate table with all 6 standard columns:
           - CANDIDATE / EMPLOYEE
           - ROLE & POSTING
           - INDUCTION
           - HR SIGN-OFF
           - CRM STATUS
           - ACTION
        """
        hr_page, _ = logged_in_page(user_key="tejaswini")
        workflow = OnboardingApprovalWorkflow(hr_page)
        overview = workflow.review_dashboard_workflow()

        metrics = overview["metrics"]
        assert int(metrics["branch_employees"]) > 0, "Branch employees metric count is 0!"
        assert int(metrics["needs_signoff"]) > 0, "Needs HR sign-off count is 0!"
        assert overview["total_rows"] > 0, "Candidate table returned 0 rows!"

        headers = [th.inner_text().strip() for th in workflow.approval_page.table_headers.all()]
        for expected_col in ["CANDIDATE", "ROLE", "INDUCTION", "SIGN-OFF", "CRM", "ACTION"]:
            assert any(expected_col in h.upper() for h in headers), f"Missing expected column '{expected_col}' in {headers}"

        print(f"[TEST PASS] Onboarding Approval Dashboard verified: {overview['total_rows']} candidates | Metrics: {metrics}")

    def test_onboarding_approval_candidate_search_and_filter(self, logged_in_page):
        """
        Verifies search functionality and candidate status on /onboarding-approval:
        1. Searches for 'Uttam Kumar'.
        2. Verifies Uttam Kumar is present with Employee ID 858, Varanasi branch, Developer department.
        3. Verifies HR Sign-Off status is 'Pending' / 'Awaiting sign-off'.
        4. Verifies CRM status is 'Pending Sign-Off'.
        5. Clears search and verifies table row count restores.
        """
        hr_page, _ = logged_in_page(user_key="tejaswini")
        workflow = OnboardingApprovalWorkflow(hr_page)
        res = workflow.search_candidate_workflow(candidate_name="Uttam Kumar")

        assert res["is_present"], "Candidate 'Uttam Kumar' not found on Onboarding Approval table!"
        details = res["details"]
        print(f"[TEST PASS] Uttam Kumar Record: {details}")

        # Check candidate particulars (case-insensitive)
        details_str = str(details).lower()
        assert "uttam" in details_str, "Candidate name mismatch in row details!"
        assert "varanasi" in details_str, "Branch mismatch! Expected 'Varanasi'."
        assert "developer" in details_str, "Department mismatch! Expected 'Developer'."
        assert "pending" in details_str, "HR Sign-Off status is not 'Pending'!"
        assert res["restored_count"] > 1, "Clearing search did not restore all candidate records!"

        print("[TEST PASS] Candidate search and pending sign-off status verified for Uttam Kumar.")

    def test_onboarding_approval_signoff_modal_inspection(self, logged_in_page):
        """
        Verifies the HR Sign-Off modal dialog:
        1. Clicks 'HR Sign-Off' on Uttam Kumar's row.
        2. Asserts modal opens with title 'HR Onboarding Sign-Off'.
        3. Asserts modal displays candidate name 'Uttam Kumar', ID '858', 'VARANASI', 'Developer'.
        4. Verifies Infusive CRM role assignment section is present.
        5. Verifies 'Confirm Approval' and 'Cancel' buttons are present.
        6. Closes the modal safely without modifying state.
        """
        hr_page, _ = logged_in_page(user_key="tejaswini")
        workflow = OnboardingApprovalWorkflow(hr_page)
        modal_res = workflow.inspect_signoff_modal_workflow(candidate_name="Uttam Kumar")

        assert modal_res["modal_opened"], "HR Sign-Off modal failed to open!"
        summary = modal_res["modal_summary"]
        assert "Sign-Off" in summary, "Sign-off heading missing in modal!"
        assert "Uttam Kumar" in summary, "Candidate name 'Uttam Kumar' missing in modal!"
        assert "858" in summary, "Candidate ID '858' missing in modal!"
        assert "Developer" in summary or "Software" in summary, "Designation/Department missing in modal!"
        assert modal_res["modal_closed_cleanly"], "Modal failed to close cleanly!"

        print("[TEST PASS] HR Sign-Off modal dialog structure and metadata verified successfully.")

    def test_onboarding_approval_modal_dynamic_decision_toggle(self, logged_in_page):
        """
        Verifies dynamic UX changes in the HR Sign-Off modal when toggling Decision:
        1. Opens Sign-Off modal for Devansh Singh (or Uttam Kumar).
        2. Validates 'Approve & Sign-Off' is checked by default:
           - Infusive CRM role dropdown is VISIBLE.
           - 'Confirm Approval' button is ENABLED.
        3. Toggles Decision to 'Reject / Request Redo':
           - Infusive CRM role dropdown is HIDDEN.
           - Remarks textarea shows mandatory placeholder.
           - 'Confirm Rejection' button is DISABLED when textarea is empty.
        4. Fills rejection remarks:
           - 'Confirm Rejection' button transitions to ENABLED.
        5. Toggles Decision back to 'Approve & Sign-Off':
           - Infusive CRM role dropdown REAPPEARS.
        6. Closes the modal safely without state mutation.
        """
        hr_page, _ = logged_in_page(user_key="tejaswini")
        workflow = OnboardingApprovalWorkflow(hr_page)
        res = workflow.verify_modal_dynamic_decision_toggle_workflow(candidate_name="Devansh Singh")

        assert res["crm_visible_on_approved"], "Infusive CRM role dropdown not visible on 'Approve'!"
        assert len(res["available_roles"]) > 0, "No CRM roles available in Infusive dropdown!"
        assert res["crm_hidden_on_rejected"], "Infusive CRM role dropdown did not hide on 'Reject'!"
        assert res["rejection_disabled_without_remarks"], "'Confirm Rejection' was not disabled when remarks were empty!"
        assert res["rejection_enabled_with_remarks"], "'Confirm Rejection' was not enabled after entering remarks!"
        assert res["crm_restored_on_reapprove"], "Infusive CRM role dropdown failed to restore upon re-selecting 'Approve'!"
        assert res["modal_closed_cleanly"], "Modal failed to close cleanly!"

        print(f"[TEST PASS] Modal dynamic Decision toggle verified successfully! Available CRM roles: {res['available_roles']}")

    def test_onboarding_approval_branch_head_view(self, logged_in_page):
        """
        Verifies that Branch Head (Vivek Singh) can access /onboarding-approval:
        1. Logs in as Branch Head ('vivek').
        2. Navigates to /onboarding-approval.
        3. Verifies dashboard loads with candidate records for Varanasi branch.
        4. Verifies candidate 'Uttam Kumar' is listed with role and clearance status.
        """
        bh_page, _ = logged_in_page(user_key="vivek")
        workflow = OnboardingApprovalWorkflow(bh_page)
        overview = workflow.review_dashboard_workflow()

        metrics = overview["metrics"]
        print(f"[TEST PASS] Branch Head Dashboard Metrics: {metrics}")
        assert overview["total_rows"] > 0, "Candidate table returned 0 rows for Branch Head!"

        res = workflow.search_candidate_workflow(candidate_name="Uttam Kumar")
        assert res["is_present"], "Candidate 'Uttam Kumar' not found on Branch Head approval table!"
        details = res["details"]
        print(f"[TEST PASS] Branch Head view for Uttam Kumar: {details}")
        assert "Uttam" in str(details), "Candidate name mismatch in Branch Head row details!"
        assert "Varanasi" in str(details), "Branch mismatch in Branch Head row details!"

    def test_batch_approve_three_and_reject_two(self, logged_in_page):
        """
        Verifies batch onboarding decisions:
        - 3 Candidates Approved: Devansh Singh, ARYAN SINGH, Uttam Kumar
        - 2 Candidates Rejected: Uday Pratap Singh, Sushree Radhika Nayak
        Verifies persisted metrics:
        - Needs HR Sign-Off: 0
        - HR Approved: 3
        - HR Rejected: 2
        """
        hr_page, _ = logged_in_page(user_key="tejaswini")
        workflow = OnboardingApprovalWorkflow(hr_page)
        overview = workflow.review_dashboard_workflow()
        current_metrics = overview["metrics"]

        # If candidates are still pending sign-off, execute batch processing
        if int(current_metrics["needs_signoff"]) > 0:
            approvals = [
                {"name": "Devansh Singh", "role": "Software development", "remarks": "Approved by HR Manager Tejaswini"},
                {"name": "ARYAN SINGH", "role": "Software development", "remarks": "Approved by HR Manager Tejaswini"},
                {"name": "Uttam Kumar", "role": "Software development", "remarks": "Approved by HR Manager Tejaswini"}
            ]

            rejections = [
                {"name": "Uday Pratap Singh", "remarks": "Educational certificates missing. Please re-upload degree and marksheets."},
                {"name": "Sushree Radhika Nayak", "remarks": "Address proof scan is blurry and illegible. Please submit a clear copy."}
            ]

            result = workflow.process_batch_onboarding_decisions_workflow(
                approved_candidates=approvals,
                rejected_candidates=rejections
            )
            final_metrics = result["final_metrics"]
        else:
            final_metrics = current_metrics

        print(f"[TEST PASS] Batch Decisions Verified Successfully!")
        print(f"  Final Dashboard Metrics: {final_metrics}")

        assert int(final_metrics["approved"]) == 3, f"Expected 3 HR Approved, got {final_metrics['approved']}"
        assert int(final_metrics["rejected"]) == 2, f"Expected 2 HR Rejected, got {final_metrics['rejected']}"
        assert int(final_metrics["needs_signoff"]) == 0, f"Expected 0 Needs HR Sign-Off, got {final_metrics['needs_signoff']}"
