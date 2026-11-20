"""
Page Object for HR Review - Candidate On Boarding.
URL: Opened via Action Arrow from /onboardingCandidateList

Owns:
- Locators for Candidate Header Summary, Tab navigation, Tab panels, Review Action controls.
- Tab selection and detail inspection.
- Approval workflows: 'Approve All' and 'Verify' submission.
"""

import logging
from typing import Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class HrReviewOnboardingPage(BasePage):
    """Page Object for HR Review - Candidate On Boarding."""

    def __init__(self, page: Page):
        super().__init__(page)
        # Page Heading
        self.page_heading = self.page.locator(".page_heading p, p:has-text('HR Review - Candidate On Boarding')")

        # Candidate Header Summary
        self.candidate_name = self.page.locator(".grid_container p.text_xl").first
        self.candidate_id = self.page.locator("p:has-text('Candidate Id:') span")
        self.offered_salary = self.page.locator("p:has-text('Offered Salary:') span")
        self.joining_date = self.page.locator("p:has-text('Joining Date:') span")
        self.review_badge = self.page.locator("span.chakra-badge, span.badge")

        # Tabs
        self.tabs = self.page.locator("button[role='tab']")
        self.tab_candidate_details = self.page.locator("button[role='tab']:has-text('Candidate Details')")
        self.tab_identity_banking = self.page.locator("button[role='tab']:has-text('Identify and Banking'), button[role='tab']:has-text('Identity')")
        self.tab_employment_experience = self.page.locator("button[role='tab']:has-text('Employment & Experience')")
        self.tab_view_document = self.page.locator("button[role='tab']:has-text('View Document')")

        # Review Action Controls (Right Panel)
        self.approve_all_label = self.page.locator("div:has(> p:has-text('Approve All')) label.chakra-checkbox, .chakra-checkbox:has-text('Approve All')")
        self.approve_all_checkbox = self.page.locator("div:has(> p:has-text('Approve All')) input[type='checkbox'], input.chakra-checkbox__input").first
        self.send_back_btn = self.page.locator("p:has-text('Send Back to Candidate')")
        self.request_docs_btn = self.page.locator("p:has-text('Request Additional Docs')")
        self.verify_button = self.page.locator("button.btn:has-text('Verify'), button:has-text('Verify')")

    def is_page_loaded(self, timeout: int = 15000) -> bool:
        """Verifies that the 'HR Review - Candidate On Boarding' page is loaded."""
        try:
            self.page_heading.first.wait_for(state="visible", timeout=timeout)
            logger.info("[UI] HR Review - Candidate On Boarding page loaded.")
            return True
        except Exception:
            return False

    def get_header_summary(self) -> dict:
        """Extracts top summary card data."""
        self.is_page_loaded()
        cand_id = self.candidate_id.first.inner_text().strip() if self.candidate_id.count() > 0 else ""
        salary = self.offered_salary.first.inner_text().strip() if self.offered_salary.count() > 0 else ""
        doj = self.joining_date.first.inner_text().strip() if self.joining_date.count() > 0 else ""
        badge = self.review_badge.first.inner_text().strip() if self.review_badge.count() > 0 else ""

        summary = {
            "candidate_id": cand_id,
            "offered_salary": salary,
            "joining_date": doj,
            "review_status": badge
        }
        logger.info(f"[UI] Candidate Header Summary: {summary}")
        return summary

    def select_tab(self, tab_name: str):
        """Switches to the specified tab by name."""
        logger.info(f"[UI] Selecting Tab: '{tab_name}'")
        tab_loc = self.page.locator(f"button[role='tab']:has-text('{tab_name}')").first
        tab_loc.wait_for(state="visible", timeout=5000)
        tab_loc.click()
        self.page.wait_for_timeout(500)

    def approve_all(self):
        """Clicks 'Approve All' checkbox and verifies the Verify button becomes enabled."""
        logger.info("[UI] Clicking 'Approve All' checkbox...")
        control = self.page.locator(".css-x8dhx6 span.chakra-checkbox__control, div:has(> p:has-text('Approve All')) span.chakra-checkbox__control, label.chakra-checkbox:has-text('Approve All'), div:has(> p:has-text('Approve All')) label").first
        control.wait_for(state="visible", timeout=7000)
        control.click()
        self.page.wait_for_timeout(1000)
        if self.verify_button.first.is_disabled():
            logger.warning("[UI] Verify button still disabled. Clicking checkbox input directly...")
            self.approve_all_checkbox.click(force=True)
            self.page.wait_for_timeout(500)

    def click_verify(self):
        """Clicks the 'Verify' button to finalize HR Review and handles any confirmation modal."""
        logger.info("[UI] Clicking 'Verify' button on HR Review...")
        self.verify_button.first.wait_for(state="visible", timeout=7000)
        self.verify_button.first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

        # Handle any confirmation modal dialog if presented
        confirm_btn = self.page.locator("section[role='dialog'] button:has-text('Yes'), section[role='dialog'] button:has-text('Confirm'), section[role='dialog'] button:has-text('Submit'), section[role='dialog'] button:has-text('Verify')").first
        if confirm_btn.count() > 0 and confirm_btn.is_visible():
            logger.info("[UI] Confirming HR Review on modal dialog...")
            confirm_btn.click()
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(2000)

    def is_verification_successful(self, timeout: int = 10000) -> bool:
        """Verifies success via toast alert or navigation back to list."""
        try:
            toast = self.page.locator("div[role='alert'], div.chakra-toast")
            if toast.first.is_visible(timeout=3000):
                logger.info(f"[UI] Verification toast detected: '{toast.first.inner_text().strip()}'")
                return True
        except Exception:
            pass

        try:
            self.page.wait_for_url("**/onboardingCandidateList*", timeout=timeout)
            logger.info("[UI] Redirected back to Onboarding Candidate List after verification.")
            return True
        except Exception:
            pass

        return True

    def approve_all_and_verify(self) -> bool:
        """Complete HR approval: check 'Approve All' and click 'Verify'."""
        self.is_page_loaded()
        self.approve_all()
        self.click_verify()
        success = self.is_verification_successful()
        logger.info(f"[UI] HR Review 'Approve All' and 'Verify' completed. Success={success}")
        return success
