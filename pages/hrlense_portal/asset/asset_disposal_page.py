import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetDisposalPage(BasePage):
    """
    Page Object Model for Asset Damage & Disposal management (Phase 9).
    Supports Scrap, Sell, and Write-Off disposal decisions.
    """
    NEW_DISPOSAL_BTN = "role=button[name='New Disposal']"
    DISPOSE_BTN = "role=button[name='Dispose Asset']"
    SUBMIT_DISPOSAL_BTN = "role=button[name='Submit']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_disposal(self):
        """Navigates to Asset Disposal page via direct URL or side menu."""
        logger.info("Navigating to Asset Disposal page")
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-disposal", timeout=15000)
            self.page.wait_for_load_state("domcontentloaded")
            return
        except Exception:
            pass

        try:
            link = self.page.locator("a:has-text('Disposal'), a:has-text('Scrap')").first
            if link.is_visible(timeout=2000):
                link.click()
                self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass

    def open_disposal_modal(self, asset_code_or_name: str = None):
        """Opens disposal modal/drawer."""
        logger.info(f"Opening disposal modal for asset: {asset_code_or_name or 'New'}")
        if asset_code_or_name:
            search_input = self.page.locator("input[placeholder*='Search']").first
            if search_input.is_visible():
                search_input.fill(asset_code_or_name)
                self.page.wait_for_timeout(1000)
            row = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
            if row.is_visible(timeout=3000):
                btn = row.get_by_role("button", name=re.compile(r"(Dispose|Scrap|Action)", re.I)).first
                if btn.is_visible():
                    btn.click()
                    return

        btn = self.page.locator("button:has-text('New Disposal'), button:has-text('Dispose Asset'), button:has-text('Add Disposal')").first
        if btn.is_visible(timeout=3000):
            btn.click()

    def fill_disposal_details(
        self,
        asset_code_or_name: str = None,
        disposal_type: str = "Scrap",
        disposal_date: str = None,
        recovery_value: str = None,
        buyer_or_vendor: str = None,
        reason: str = "Beyond economical repair",
        remarks: str = "Disposal approved as per IT policy."
    ):
        """Fills disposal details form (Scrap / Sell / Write-Off)."""
        logger.info(f"Filling disposal form: Asset={asset_code_or_name}, Type={disposal_type}")
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if not dialog.is_visible():
            dialog = self.page

        # Asset selection if not pre-populated
        if asset_code_or_name:
            try:
                asset_input = dialog.get_by_placeholder("Search by asset code or name...").first
                if asset_input.is_visible(timeout=1000):
                    asset_input.fill(asset_code_or_name)
                    self.page.wait_for_timeout(1000)
                    self.page.locator(".chakra-portal, [role='listbox']").get_by_text(asset_code_or_name, exact=False).first.click()
            except Exception:
                pass

        # Disposal Type (Scrap / Sell / Write-Off)
        try:
            type_select = dialog.get_by_label("Disposal Type", exact=False).first
            if not type_select.is_visible(timeout=500):
                type_select = dialog.locator("select").filter(has_text=re.compile(r"(Scrap|Sell|Write-Off)", re.I)).first
            if type_select.is_visible(timeout=500):
                type_select.select_option(label=disposal_type)
        except Exception:
            try:
                dialog.get_by_text(disposal_type, exact=True).first.click()
            except Exception:
                pass

        # Disposal Date
        if disposal_date:
            try:
                date_input = dialog.locator("input[type='date']").first
                if date_input.is_visible():
                    date_input.fill(disposal_date)
            except Exception:
                pass

        # Recovery Value (for Sell/Scrap)
        if recovery_value:
            try:
                val_input = dialog.get_by_placeholder("0.00", exact=False).first
                if val_input.is_visible():
                    val_input.fill(recovery_value)
            except Exception:
                pass

        # Buyer / Vendor
        if buyer_or_vendor:
            try:
                buyer_input = dialog.locator("input[placeholder*='Buyer' i], input[placeholder*='Vendor' i]").first
                if buyer_input.is_visible():
                    buyer_input.fill(buyer_or_vendor)
            except Exception:
                pass

        # Reason
        if reason:
            try:
                reason_input = dialog.locator("textarea, input[placeholder*='Reason' i]").first
                if reason_input.is_visible():
                    reason_input.fill(reason)
            except Exception:
                pass

        # Remarks
        if remarks:
            try:
                rem_input = dialog.locator("textarea, input[placeholder*='Remarks' i]").last
                if rem_input.is_visible():
                    rem_input.fill(remarks)
            except Exception:
                pass

    def submit_disposal(self):
        """Submits disposal form."""
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if not dialog.is_visible():
            dialog = self.page

        btn = dialog.get_by_role("button", name=re.compile(r"(Submit|Confirm|Save|Dispose)", re.I)).first
        if btn.is_visible(timeout=3000):
            btn.click()

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
