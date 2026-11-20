import logging
import re
from typing import Optional
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class CandidateAcceptancePage(BasePage):
    """
    Page Object for the Candidate Acceptance & OTP Verification flow.
    URL pattern: https://stg-hrlense.jobvritta.com/otp-verification?email=...&job=...
    """

    def __init__(self, page: Page):
        super().__init__(page)
        # Locators based on the Chakra UI DOM structure
        self.title = self.page.locator("p.title:has-text('Verify Your Acceptance'), p:has-text('Verify Your Acceptance')")
        self.subtitle = self.page.locator("p.subtitle:has-text('sent an OTP'), p:has-text('sent an OTP')")
        self.pin_inputs = self.page.locator(".chakra-pin-input, input[data-index]")
        self.verify_button = self.page.locator("button.verify_btn, button:has-text('Verify')")
        self.cancel_button = self.page.locator("button.cancel_btn, button:has-text('Cancel')")
        self.resend_otp_btn = self.page.locator("span:has-text('Resend OTP'), button:has-text('Resend OTP')")

        # Locators for Offer Review & Decision screen (after OTP verification)
        self.offer_card = self.page.locator(".offer_card")
        self.offer_heading = self.page.locator("p.offer_heading, p:has-text('Your Offer from')")
        self.offer_details = self.page.locator("ul.offer_list li, .offer_list li")
        self.accept_offer_btn = self.page.locator("button:has-text('Accept Offer')")
        self.reject_offer_btn = self.page.locator("button:has-text('Reject Offer')")

    def navigate_to_verification_url(self, verification_url: str):
        """Navigates directly to the Candidate Verification URL."""
        logger.info(f"[UI] Navigating to Candidate Verification URL: {verification_url}")
        self.page.goto(verification_url, wait_until="domcontentloaded")
        self.title.first.wait_for(state="visible", timeout=15000)
        logger.info("[UI] Candidate Acceptance & Verification page loaded.")

    def is_verification_card_visible(self) -> bool:
        """Returns True if the 'Verify Your Acceptance' OTP card is visible."""
        return self.title.first.is_visible()

    def get_recipient_email(self) -> str:
        """Extracts the email displayed on the OTP card."""
        try:
            return self.subtitle.first.locator("span").first.inner_text().strip()
        except Exception:
            return ""

    def fill_otp(self, otp_code: str):
        """
        Fills the 6-digit OTP into the Chakra pin inputs (indices 0 to 5).
        """
        code = str(otp_code).strip()
        digits = list(code)
        logger.info(f"[UI] Entering {len(digits)}-digit OTP into verification inputs...")
        pin0 = self.page.locator("input[data-index='0'], #pin-input-_r_0_-0").first
        pin0.wait_for(state="visible", timeout=7000)
        pin0.click()
        self.page.keyboard.type(code)
        self.page.wait_for_timeout(300)
        for idx, digit in enumerate(digits[:6]):
            pin_input = self.page.locator(f"input[data-index='{idx}']").first
            if pin_input.is_visible() and pin_input.input_value() != digit:
                pin_input.fill(digit)
        logger.info("[UI] OTP digits filled successfully.")

    def click_verify(self):
        """Clicks the Verify button to submit OTP."""
        logger.info("[UI] Clicking Verify button...")
        self.verify_button.first.click()
        self.page.wait_for_load_state("domcontentloaded")

    def click_resend_otp(self):
        """Clicks the Resend OTP action link."""
        logger.info("[UI] Clicking Resend OTP...")
        self.resend_otp_btn.first.click()
        self.page.wait_for_timeout(1000)

    def verify_otp_and_proceed(self, otp_code: str):
        """Full interaction: Enter 6-digit OTP and click Verify."""
        self.fill_otp(otp_code)
        self.click_verify()

    # ── Post-OTP: Offer Review & Acceptance Methods ────────────────────────────

    def is_offer_review_visible(self) -> bool:
        """Checks if the offer details card is displayed after OTP verification."""
        try:
            self.offer_card.wait_for(state="visible", timeout=10000)
            return True
        except Exception:
            return False

    def get_offer_summary(self) -> dict:
        """
        Extracts offer parameters: Joining Date, Location, and Offered Gross Salary.
        """
        summary = {}
        items = self.offer_details.all()
        for item in items:
            text = item.inner_text().strip()
            if ":" in text:
                k, v = text.split(":", 1)
                summary[k.strip()] = v.strip()
        logger.info(f"[UI] Extracted Candidate Offer Details: {summary}")
        return summary

    def accept_offer(self):
        """Clicks the 'Accept Offer' button."""
        logger.info("[UI] Candidate clicking 'Accept Offer'...")
        self.accept_offer_btn.first.wait_for(state="visible", timeout=8000)
        self.accept_offer_btn.first.click()
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("[UI] 'Accept Offer' clicked successfully.")

    def reject_offer(self):
        """Clicks the 'Reject Offer' button."""
        logger.info("[UI] Candidate clicking 'Reject Offer'...")
        self.reject_offer_btn.first.wait_for(state="visible", timeout=8000)
        self.reject_offer_btn.first.click()
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("[UI] 'Reject Offer' clicked.")
