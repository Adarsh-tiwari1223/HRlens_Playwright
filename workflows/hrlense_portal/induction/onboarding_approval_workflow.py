"""
Workflow for HRlens Onboarding Approval.
URL: /onboarding-approval

Orchestrates:
1. Review of Onboarding Approval Dashboard (metrics, tabs, candidates).
2. Candidate search and status verification.
3. Sign-off modal inspection (pre-approval verification).
4. End-to-end HR and Branch Head candidate onboarding approval.
"""

import logging
from typing import Dict, Any, Optional, List
from playwright.sync_api import Page
from pages.hrlense_portal.induction.onboarding_approval_page import OnboardingApprovalPage

logger = logging.getLogger(__name__)


class OnboardingApprovalWorkflow:
    """Orchestrates Onboarding Approval business processes."""

    def __init__(self, page: Page):
        self.page = page
        self.approval_page = OnboardingApprovalPage(page)

    def review_dashboard_workflow(self) -> Dict[str, Any]:
        """
        Navigates to /onboarding-approval and extracts full dashboard state:
        - Top metric cards
        - Total row count
        - Sample row data
        """
        logger.info("[WORKFLOW] Reviewing Onboarding Approval Dashboard...")
        self.approval_page.navigate_to_onboarding_approval()
        metrics = self.approval_page.get_metrics()
        total_rows = self.approval_page.get_row_count()
        sample_row = self.approval_page.get_candidate_details("Uttam") if self.approval_page.is_candidate_present("Uttam") else {}

        logger.info(f"[WORKFLOW] Metrics: {metrics} | Total Rows: {total_rows}")
        return {
            "metrics": metrics,
            "total_rows": total_rows,
            "sample_candidate": sample_row
        }

    def search_candidate_workflow(self, candidate_name: str = "Uttam Kumar") -> Dict[str, Any]:
        """
        Filters candidates by name and extracts row details.
        """
        logger.info(f"[WORKFLOW] Searching for candidate: '{candidate_name}'...")
        self.approval_page.navigate_to_onboarding_approval()
        self.approval_page.search_candidate(candidate_name)

        is_present = self.approval_page.is_candidate_present(candidate_name)
        candidate_data = {}
        if is_present:
            candidate_data = self.approval_page.get_candidate_details(candidate_name)

        self.approval_page.clear_search()
        restored_count = self.approval_page.get_row_count()

        return {
            "candidate_name": candidate_name,
            "is_present": is_present,
            "details": candidate_data,
            "restored_count": restored_count
        }

    def inspect_signoff_modal_workflow(self, candidate_name: str = "Uttam Kumar") -> Dict[str, Any]:
        """
        Opens the Sign-Off modal for candidate, verifies modal details,
        and closes it cleanly to avoid unexpected state change.
        """
        logger.info(f"[WORKFLOW] Inspecting Sign-Off modal for: '{candidate_name}'...")
        self.approval_page.navigate_to_onboarding_approval()
        self.approval_page.open_signoff_modal(candidate_name)

        is_open = self.approval_page.is_signoff_modal_open()
        modal_text = self.approval_page.modal.inner_text().strip().replace("\n", " | ")
        logger.info(f"[WORKFLOW] Modal Content: {modal_text[:250]}...")

        # Close without submitting to keep test non-destructive
        self.approval_page.close_signoff_modal()
        is_closed = not self.approval_page.is_signoff_modal_open()

        return {
            "candidate_name": candidate_name,
            "modal_opened": is_open,
            "modal_closed_cleanly": is_closed,
            "modal_summary": modal_text
        }

    def verify_modal_dynamic_decision_toggle_workflow(self, candidate_name: str = "Devansh Singh") -> Dict[str, Any]:
        """
        Validates dynamic modal behavior when toggling Decision between 'Approved' and 'Rejected':
        1. Opens Sign-Off modal for candidate.
        2. Asserts Default State:
           - 'Approve & Sign-Off' is checked.
           - Infusive CRM role dropdown is visible.
           - Remarks are optional.
           - 'Confirm Approval' is enabled.
        3. Toggles to 'Reject / Request Redo':
           - Infusive CRM role dropdown is HIDDEN.
           - Remarks are marked Mandatory ('Remarks *').
           - 'Confirm Rejection' is DISABLED while remarks are empty.
           - When remarks are filled, 'Confirm Rejection' becomes ENABLED.
        4. Toggles back to 'Approve & Sign-Off':
           - Infusive CRM role dropdown REAPPEARS.
        5. Closes modal cleanly without submitting changes.
        """
        logger.info(f"[WORKFLOW] Verifying dynamic Decision toggle in Sign-Off modal for '{candidate_name}'...")
        self.approval_page.navigate_to_onboarding_approval()
        self.approval_page.open_signoff_modal(candidate_name)

        # 1. Default Approved State
        crm_visible_approved = self.approval_page.is_crm_section_visible()
        available_roles = self.approval_page.get_available_crm_roles()
        approval_btn_enabled = self.approval_page.modal_confirm_approval_button.is_enabled()

        # 2. Toggle to Rejected
        self.approval_page.select_decision("Rejected")
        crm_visible_rejected = self.approval_page.is_crm_section_visible()
        rejection_btn_disabled_initially = self.approval_page.is_confirm_rejection_disabled()

        # Type remarks to test validation enablement
        self.approval_page.enter_remarks("Document verification incomplete; please re-upload clear Aadhaar scan.")
        rejection_btn_enabled_with_text = not self.approval_page.is_confirm_rejection_disabled()

        # 3. Toggle back to Approved
        self.approval_page.select_decision("Approved")
        crm_visible_restored = self.approval_page.is_crm_section_visible()

        # 4. Clean close
        self.approval_page.close_signoff_modal()
        modal_closed = not self.approval_page.is_signoff_modal_open()

        logger.info(
            f"[WORKFLOW] Decision Toggle Verified: "
            f"CRM visible on approve={crm_visible_approved}, "
            f"CRM hidden on reject={not crm_visible_rejected}, "
            f"Rejection disabled without remarks={rejection_btn_disabled_initially}, "
            f"Rejection enabled with remarks={rejection_btn_enabled_with_text}"
        )

        return {
            "candidate_name": candidate_name,
            "available_roles": available_roles,
            "crm_visible_on_approved": crm_visible_approved,
            "crm_hidden_on_rejected": not crm_visible_rejected,
            "rejection_disabled_without_remarks": rejection_btn_disabled_initially,
            "rejection_enabled_with_remarks": rejection_btn_enabled_with_text,
            "crm_restored_on_reapprove": crm_visible_restored,
            "modal_closed_cleanly": modal_closed
        }

    def execute_approval_workflow(self, candidate_name: str, crm_role: Optional[str] = "Software development", remarks: Optional[str] = "Approved onboarding") -> bool:
        """
        Executes live HR approval sign-off for a specific candidate.
        """
        logger.info(f"[WORKFLOW] Approving onboarding for: '{candidate_name}' (Role: {crm_role})...")
        self.approval_page.navigate_to_onboarding_approval()
        self.approval_page.open_signoff_modal(candidate_name)
        self.approval_page.confirm_approval(crm_role=crm_role, remarks=remarks)
        return True

    def execute_rejection_workflow(self, candidate_name: str, mandatory_remarks: str) -> bool:
        """
        Executes live HR rejection for a specific candidate.
        """
        logger.info(f"[WORKFLOW] Rejecting onboarding for: '{candidate_name}'...")
        self.approval_page.navigate_to_onboarding_approval()
        self.approval_page.open_signoff_modal(candidate_name)
        self.approval_page.confirm_rejection(mandatory_remarks=mandatory_remarks)
        return True

    def process_batch_onboarding_decisions_workflow(
        self,
        approved_candidates: List[Dict[str, str]],
        rejected_candidates: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Processes a batch of candidate approvals (e.g. 3) and rejections (e.g. 2):
        1. Executes approvals with Infusive CRM role assignment.
        2. Executes rejections with mandatory reason remarks.
        3. Extracts final updated metric card counts.
        """
        self.approval_page.navigate_to_onboarding_approval()
        initial_metrics = self.approval_page.get_metrics()
        logger.info(f"[WORKFLOW] Starting Batch Decisions. Initial Metrics: {initial_metrics}")

        # Process Approvals
        approved_results = []
        for item in approved_candidates:
            c_name = item["name"]
            role = item.get("role", "Software development")
            rem = item.get("remarks", "Approved by HR Manager")
            logger.info(f"[WORKFLOW] [1/2] Processing Approval for '{c_name}'...")
            self.approval_page.open_signoff_modal(c_name)
            self.approval_page.confirm_approval(crm_role=role, remarks=rem)
            approved_results.append(c_name)

        # Process Rejections
        rejected_results = []
        for item in rejected_candidates:
            c_name = item["name"]
            rem = item.get("remarks", "Document verification failed. Please re-upload required documents.")
            logger.info(f"[WORKFLOW] [2/2] Processing Rejection for '{c_name}'...")
            self.approval_page.open_signoff_modal(c_name)
            self.approval_page.confirm_rejection(mandatory_remarks=rem)
            rejected_results.append(c_name)

        # Refresh dashboard and get final metrics
        if self.approval_page.refresh_button.is_visible():
            self.approval_page.refresh_button.click()
            self.page.wait_for_timeout(2000)

        final_metrics = self.approval_page.get_metrics()
        logger.info(f"[WORKFLOW] Batch Decisions Complete. Final Metrics: {final_metrics}")

        return {
            "initial_metrics": initial_metrics,
            "final_metrics": final_metrics,
            "approved": approved_results,
            "rejected": rejected_results
        }
