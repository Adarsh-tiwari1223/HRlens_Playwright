import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetLostInvestigationPage(BasePage):
    """
    Page Object Model for Lost Asset Investigation & PM Approval (Phase 10).
    Handles investigation initiation, outcome recording (Found / Not Found), and PM write-off.
    """
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_lost_investigation(self):
        """Navigates to Lost Asset Investigation page or tab."""
        logger.info("Navigating to Lost Asset Investigation page")
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-lost-investigation", timeout=15000)
            self.page.wait_for_load_state("domcontentloaded")
            return
        except Exception:
            pass

        try:
            link = self.page.locator("a:has-text('Lost'), a:has-text('Investigation')").first
            if link.is_visible(timeout=2000):
                link.click()
                self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass

    def start_investigation(self, asset_code: str, officer_name: str = "IT Security", remarks: str = "Investigation started"):
        """Initiates a formal investigation for a lost asset."""
        logger.info(f"Starting investigation for lost asset: {asset_code}")
        search_input = self.page.locator("input[placeholder*='Search']").first
        if search_input.is_visible(timeout=1000):
            search_input.fill(asset_code)
            self.page.wait_for_timeout(1000)

        row = self.page.locator("table tbody tr").filter(has_text=asset_code).first
        if row.is_visible(timeout=3000):
            btn = row.get_by_role("button", name=re.compile(r"(Investigate|Start Investigation|Action)", re.I)).first
            if btn.is_visible():
                btn.click()

        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if dialog.is_visible(timeout=3000):
            try:
                dialog.locator("textarea, input[placeholder*='Remarks' i]").first.fill(remarks)
            except Exception:
                pass
            btn = dialog.get_by_role("button", name=re.compile(r"(Submit|Start|Proceed)", re.I)).first
            if btn.is_visible():
                btn.click()

    def record_investigation_outcome(
        self,
        asset_code: str,
        is_found: bool = False,
        condition_if_found: str = "Good",
        pm_approval_remarks: str = "PM approved write-off after formal investigation"
    ):
        """
        Records the final outcome of the lost asset investigation:
        - If Found: Recovers asset and evaluates condition.
        - If Not Found: Requests PM approval for write-off and closes asset as Lost.
        """
        outcome_str = "Found" if is_found else "Not Found (Write-Off)"
        logger.info(f"Recording investigation outcome for asset {asset_code}: {outcome_str}")

        search_input = self.page.locator("input[placeholder*='Search']").first
        if search_input.is_visible(timeout=1000):
            search_input.fill(asset_code)
            self.page.wait_for_timeout(1000)

        row = self.page.locator("table tbody tr").filter(has_text=asset_code).first
        if row.is_visible(timeout=3000):
            btn = row.get_by_role("button", name=re.compile(r"(Resolve|Outcome|Close|Approve)", re.I)).first
            if btn.is_visible():
                btn.click()

        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if dialog.is_visible(timeout=3000):
            # Select Found / Not Found
            try:
                outcome_select = dialog.get_by_label("Outcome", exact=False).first
                if not outcome_select.is_visible():
                    outcome_select = dialog.locator("select").first
                if outcome_select.is_visible():
                    outcome_select.select_option(label="Asset Found" if is_found else "Asset Not Found")
            except Exception:
                try:
                    dialog.get_by_text("Found" if is_found else "Not Found", exact=False).first.click()
                except Exception:
                    pass

            if is_found:
                try:
                    cond_select = dialog.get_by_label("Condition", exact=False).first
                    if cond_select.is_visible():
                        cond_select.select_option(label=condition_if_found)
                except Exception:
                    pass
            else:
                # PM Approval remarks
                try:
                    remarks_input = dialog.locator("textarea, input[placeholder*='Remarks' i], input[placeholder*='Approval' i]").first
                    if remarks_input.is_visible():
                        remarks_input.fill(pm_approval_remarks)
                except Exception:
                    pass

            # Submit resolution
            submit_btn = dialog.get_by_role("button", name=re.compile(r"(Submit|Close Case|Approve|Save)", re.I)).first
            if submit_btn.is_visible():
                submit_btn.click()

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
