"""
Page Object for HRlens Onboarding Approval Portal.
URL: /onboarding-approval

Owns:
- Locators for Header, Access Badge, Refresh button.
- Stat Metric Cards (Branch Employees, Needs HR Sign-Off, HR Approved, HR Rejected).
- Filter Tabs (All Candidates, Needs HR Sign-Off, Approved by HR, Rejected).
- Candidate Table (Columns, Rows, Status Badges, Action Buttons).
- HR / Branch Head Sign-Off Modal (Details, Infusive Role, Confirm Approval, Cancel).
"""

import re
import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class OnboardingApprovalPage(BasePage):
    """Page Object for /onboarding-approval."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{settings.BASE_URL}/onboarding-approval"

        # ----------------- Top Header Section -----------------
        self.header_title = self.page.locator("p.chakra-text:has-text('Onboarding Approvals')").first
        self.access_badge = self.page.locator("span.chakra-badge:has-text('Access')").first
        self.header_description = self.page.locator("p.chakra-text:has-text('Review and record')").first
        self.refresh_button = self.page.locator("button:has-text('Refresh')").first

        # ----------------- Metric Stat Cards -----------------
        self.stat_cards = self.page.locator(".stat-card")
        self.stat_branch_employees = self.page.locator(".stat-card:has-text('Branch Employees') p.chakra-text").last
        self.stat_needs_signoff = self.page.locator(".stat-card:has-text('Needs') p.chakra-text").last
        self.stat_approved = self.page.locator(".stat-card:has-text('Approved') p.chakra-text").last
        self.stat_rejected = self.page.locator(".stat-card:has-text('Rejected') p.chakra-text").last

        # ----------------- Filter Tabs & Search Bar -----------------
        self.tab_all = self.page.locator("button.filter-tab-btn:has-text('All Candidates')").first
        self.tab_needs_signoff = self.page.locator("button.filter-tab-btn:has-text('Needs')").first
        self.tab_approved = self.page.locator("button.filter-tab-btn:has-text('Approved')").first
        self.tab_rejected = self.page.locator("button.filter-tab-btn:has-text('Rejected')").first
        self.search_input = self.page.locator("input[placeholder*='Search candidate' i]").first

        # ----------------- Candidate Table -----------------
        self.table = self.page.locator("table.chakra-table").first
        self.table_headers = self.page.locator("table.chakra-table thead th")
        self.table_rows = self.page.locator("table.chakra-table tbody tr")
        self.table_record_counter = self.page.locator("p.chakra-text:has-text('Showing')").first

        # ----------------- Sign-Off Modal Dialog -----------------
        self.modal = self.page.locator("section.chakra-modal__content:has-text('Onboarding Sign-Off'), section.chakra-modal__content").first
        self.modal_title = self.page.locator("section.chakra-modal__content header, section.chakra-modal__content h2, section.chakra-modal__content p").filter(has_text=re.compile(r"Sign-Off", re.I)).first
        self.modal_candidate_name = self.modal.locator("p.chakra-text, h3").first
        
        # Modal Decisions: Approve & Sign-Off vs Reject / Request Redo
        self.modal_radio_approve = self.modal.locator("label.chakra-radio:has-text('Approve & Sign-Off')").first
        self.modal_radio_approve_input = self.modal.locator("input[value='Approved']").first
        self.modal_radio_reject = self.modal.locator("label.chakra-radio:has-text('Reject / Request Redo')").first
        self.modal_radio_reject_input = self.modal.locator("input[value='Rejected']").first
        
        # Modal Dynamic Sections
        self.modal_crm_section = self.modal.locator("div.css-ocle3l, div:has-text('Assign Role in Infusive')").first
        self.modal_role_select = self.modal.locator("select.chakra-select").first
        self.modal_remarks_section = self.modal.locator(".chakra-textarea").locator("xpath=..").first
        self.modal_remarks_label = self.modal.locator("p.chakra-text:has-text('Remarks')").first
        self.modal_remarks_textarea = self.modal.locator("textarea.chakra-textarea").first
        
        # Modal Footer Buttons
        self.modal_confirm_approval_button = self.modal.locator("button:has-text('Confirm Approval')").first
        self.modal_confirm_rejection_button = self.modal.locator("button:has-text('Confirm Rejection')").first
        self.modal_cancel_button = self.modal.locator("button:has-text('Cancel')").first

    def navigate_to_onboarding_approval(self):
        """Navigates directly to /onboarding-approval."""
        logger.info(f"[UI] Navigating to Onboarding Approval: {self.url}")
        if "/onboarding-approval" not in self.page.url:
            self.page.goto(self.url, wait_until="domcontentloaded", timeout=35000)
        self.table.wait_for(state="visible", timeout=20000)
        self.page.wait_for_timeout(1000)
        assert "/onboarding-approval" in self.page.url, f"Failed to load /onboarding-approval. Current URL: {self.page.url}"
        logger.info("[UI] Onboarding Approval dashboard loaded successfully.")

    def get_metrics(self) -> Dict[str, str]:
        """Extracts top stat metric card numbers."""
        metrics = {
            "branch_employees": self.stat_branch_employees.inner_text().strip() if self.stat_branch_employees.is_visible() else "0",
            "needs_signoff": self.stat_needs_signoff.inner_text().strip() if self.stat_needs_signoff.is_visible() else "0",
            "approved": self.stat_approved.inner_text().strip() if self.stat_approved.is_visible() else "0",
            "rejected": self.stat_rejected.inner_text().strip() if self.stat_rejected.is_visible() else "0",
        }
        logger.info(f"[UI] Onboarding Approval Metrics: {metrics}")
        return metrics

    def select_filter_tab(self, tab_label: str):
        """Clicks one of the filter tabs (All Candidates, Needs HR Sign-Off, Approved, Rejected)."""
        logger.info(f"[UI] Selecting filter tab: '{tab_label}'...")
        tab_btn = self.page.locator(f"button.filter-tab-btn:has-text('{tab_label}')").first
        tab_btn.wait_for(state="visible", timeout=5000)
        tab_btn.click()
        self.page.wait_for_timeout(1000)

    def search_candidate(self, query: str):
        """Searches candidates using the search input."""
        logger.info(f"[UI] Searching candidates with query: '{query}'...")
        self.search_input.wait_for(state="visible", timeout=5000)
        self.search_input.fill(query)
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        """Clears the search input."""
        logger.info("[UI] Clearing candidate search...")
        self.search_input.fill("")
        self.page.wait_for_timeout(1000)

    def get_row_count(self) -> int:
        """Returns the number of candidate rows in the table."""
        return self.table_rows.count()

    def get_candidate_row(self, candidate_name: str) -> Locator:
        """Returns the Locator for the row containing candidate_name."""
        return self.table_rows.filter(has_text=candidate_name).first

    def is_candidate_present(self, candidate_name: str) -> bool:
        """Checks if a candidate is present in the table."""
        row = self.get_candidate_row(candidate_name)
        return row.is_visible()

    def get_candidate_details(self, candidate_name: str) -> Dict[str, str]:
        """Extracts structured data for a candidate row."""
        row = self.get_candidate_row(candidate_name)
        row.wait_for(state="visible", timeout=7000)
        cells = row.locator("td").all_inner_texts()
        headers = [th.inner_text().strip() for th in self.table_headers.all()]
        return dict(zip(headers, [c.strip().replace("\n", " | ") for c in cells]))

    def open_signoff_modal(self, candidate_name: str):
        """Clicks the Sign-Off action button (or View Dossier for approved candidate) to open the modal."""
        logger.info(f"[UI] Opening Sign-Off / Dossier modal for candidate: '{candidate_name}'...")
        row = self.get_candidate_row(candidate_name)
        action_btn = row.locator("button:has-text('Sign-Off'), button:has-text('View Dossier')").first
        action_btn.wait_for(state="visible", timeout=7000)
        action_btn.click()
        self.modal.wait_for(state="visible", timeout=7000)
        logger.info("[UI] Modal opened successfully.")

    def is_signoff_modal_open(self) -> bool:
        """Returns True if the Sign-Off modal dialog is visible."""
        return self.modal.is_visible()

    def close_signoff_modal(self):
        """Closes the Sign-Off modal without approving."""
        logger.info("[UI] Cancelling / Closing Sign-Off modal...")
        if self.modal_cancel_button.is_visible():
            self.modal_cancel_button.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(1000)

    def select_decision(self, decision: str):
        """
        Toggles the Decision radio button inside the modal:
        - 'Approved' / 'Approve & Sign-Off'
        - 'Rejected' / 'Reject / Request Redo'
        """
        decision_clean = decision.strip().lower()
        if "reject" in decision_clean:
            logger.info("[UI] Modal Decision: Selecting 'Reject / Request Redo'...")
            self.modal_radio_reject.click()
        else:
            logger.info("[UI] Modal Decision: Selecting 'Approve & Sign-Off'...")
            self.modal_radio_approve.click()
        self.page.wait_for_timeout(800)

    def is_crm_section_visible(self) -> bool:
        """Checks if the 'Assign Role in Infusive' section is visible (present only on Approval)."""
        return self.modal_crm_section.is_visible()

    def get_available_crm_roles(self) -> List[str]:
        """Returns the list of selectable CRM roles in Infusive (e.g. Admin, Pre-Sales, Software development)."""
        if self.modal_role_select.is_visible():
            return [o.inner_text().strip() for o in self.modal_role_select.locator("option").all()]
        return []

    def select_crm_role(self, role_name: str):
        """Selects target CRM role in Infusive."""
        logger.info(f"[UI] Assigning Infusive CRM role: '{role_name}'...")
        self.modal_role_select.wait_for(state="visible", timeout=5000)
        self.modal_role_select.select_option(label=role_name)
        self.page.wait_for_timeout(500)

    def enter_remarks(self, remarks: str):
        """Fills remarks or rejection reason in the textarea."""
        logger.info(f"[UI] Entering remarks: '{remarks[:60]}'...")
        self.modal_remarks_textarea.wait_for(state="visible", timeout=5000)
        self.modal_remarks_textarea.fill(remarks)
        self.page.wait_for_timeout(500)

    def is_confirm_rejection_disabled(self) -> bool:
        """Checks if 'Confirm Rejection' button is disabled (mandatory remarks validation)."""
        return self.modal_confirm_rejection_button.is_disabled()

    def confirm_approval(self, crm_role: Optional[str] = None, remarks: Optional[str] = None):
        """
        Submits 'Approve & Sign-Off' decision:
        1. Ensures 'Approve & Sign-Off' is selected.
        2. Optionally selects CRM role.
        3. Optionally enters remarks.
        4. Clicks 'Confirm Approval'.
        """
        self.select_decision("Approved")
        if crm_role:
            self.select_crm_role(crm_role)
        if remarks:
            self.enter_remarks(remarks)
        logger.info("[UI] Clicking 'Confirm Approval'...")
        self.modal_confirm_approval_button.wait_for(state="visible", timeout=5000)
        self.modal_confirm_approval_button.click()
        self.page.wait_for_timeout(2500)

    def confirm_rejection(self, mandatory_remarks: str):
        """
        Submits 'Reject / Request Redo' decision:
        1. Selects 'Reject / Request Redo'.
        2. Fills mandatory rejection remarks.
        3. Clicks 'Confirm Rejection'.
        """
        self.select_decision("Rejected")
        assert len(mandatory_remarks) > 0, "Rejection remarks are mandatory!"
        self.enter_remarks(mandatory_remarks)
        logger.info("[UI] Clicking 'Confirm Rejection'...")
        self.modal_confirm_rejection_button.wait_for(state="visible", timeout=5000)
        assert not self.is_confirm_rejection_disabled(), "'Confirm Rejection' button is unexpectedly disabled!"
        self.modal_confirm_rejection_button.click()
        self.page.wait_for_timeout(2500)
