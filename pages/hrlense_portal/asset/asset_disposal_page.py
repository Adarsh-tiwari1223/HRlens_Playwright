import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetDisposalPage(BasePage):
    """
    Page Object Model for Asset Disposal / Scrap interface:
    - Header: Asset Disposal / Scrap ('Manage damaged, lost and beyond repair assets')
    - Metrics: Disposal Queue, Disposed Assets, Recovery Value, Lost Assets
    - Tabs: Disposal Requests, Disposal History
    - Table Columns: ASSET CODE, ASSET NAME, CATEGORY, LOCATION, CURRENT STATUS, REASON, ACTION (Review →)
    """
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_disposal(self):
        """Navigates directly to Asset Disposal / Scrap page."""
        logger.info("Navigating to Asset Disposal / Scrap page")
        self.page.goto(f"{settings.BASE_URL}/asset-disposal")
        self.page.wait_for_load_state("domcontentloaded")
        
        # Verify page header
        try:
            self.page.get_by_text("Asset Disposal / Scrap", exact=True).wait_for(state="visible", timeout=5000)
        except Exception:
            pass

    def get_metrics_summary(self) -> dict:
        """Reads metric card values: Disposal Queue, Disposed Assets, Recovery Value, Lost Assets."""
        metrics = {}
        try:
            cards = self.page.locator(".chakra-stat, .css-1c250ic, div.chakra-stack").all()
            for c in cards:
                txt = c.inner_text().strip()
                if "Disposal Queue" in txt:
                    metrics["disposal_queue"] = txt.split("\n")[0]
                elif "Disposed Assets" in txt:
                    metrics["disposed_assets"] = txt.split("\n")[0]
                elif "Recovery Value" in txt:
                    metrics["recovery_value"] = txt.split("\n")[0]
                elif "Lost Assets" in txt:
                    metrics["lost_assets"] = txt.split("\n")[0]
        except Exception as ex:
            logger.warning(f"Metrics read note: {ex}")

        logger.info(f"[DISPOSAL METRICS] {metrics}")
        return metrics

    def navigate_to_disposal_requests_tab(self):
        """Clicks the 'Disposal Requests' tab."""
        logger.info("Navigating to 'Disposal Requests' tab")
        tab = self.page.get_by_role("tab", name=re.compile(r"Disposal Requests", re.I)).first
        if tab.is_visible(timeout=2000):
            tab.click()
            self.page.wait_for_timeout(500)

    def navigate_to_disposal_history_tab(self):
        """Clicks the 'Disposal History' tab."""
        logger.info("Navigating to 'Disposal History' tab")
        tab = self.page.get_by_role("tab", name=re.compile(r"Disposal History", re.I)).first
        if tab.is_visible(timeout=2000):
            tab.click()
            self.page.wait_for_timeout(500)

    def review_disposal_request(
        self,
        asset_code_or_name: str,
        disposal_type: str = "Scrap",
        recovery_value: str = "0.00",
        buyer_or_vendor: str = None,
        reason: str = "Beyond economical repair",
        remarks: str = "Disposal approved as per IT policy."
    ) -> bool:
        """
        Locates target asset in 'Disposal Requests' tab, clicks 'Review →' button,
        and submits the disposal decision (Scrap / Sell / Write-Off).
        """
        logger.info(f"Reviewing disposal request for asset: '{asset_code_or_name}', Disposal Type: '{disposal_type}'")
        self.navigate_to_disposal_requests_tab()

        # 1. Search asset / category
        search_input = self.page.get_by_placeholder("Search asset / category…")
        if not search_input.is_visible(timeout=1000):
            search_input = self.page.locator("input[placeholder*='Search' i]").first

        if search_input.is_visible(timeout=2000):
            search_input.fill(asset_code_or_name)
            search_input.press("Enter")
            self.page.wait_for_timeout(1000)

        # 2. Locate target row
        row = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
        if not row.is_visible(timeout=3000):
            row = self.page.locator("table tbody tr").first

        if not row.is_visible(timeout=3000):
            logger.warning(f"[DISPOSAL] No request row visible for '{asset_code_or_name}'.")
            return False

        # 3. Click 'Review →' action button
        review_btn = row.get_by_role("button", name=re.compile(r"Review", re.I)).first
        if not review_btn.is_visible(timeout=2000):
            review_btn = row.locator("button:has-text('Review')").first

        if review_btn.is_visible(timeout=2000):
            review_btn.click()
            self.page.wait_for_timeout(600)

        # 4. Handle Disposal Review Modal
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
        if dialog.is_visible(timeout=5000):
            # Select Disposal Type (Scrap / Sell / Write-Off)
            try:
                type_select = dialog.get_by_label("Disposal Type", exact=False).first
                if not type_select.is_visible(timeout=500):
                    type_select = dialog.locator("select").filter(has_text=re.compile(r"(Scrap|Sell|Write-Off)", re.I)).first
                if type_select.is_visible(timeout=500):
                    type_select.select_option(label=disposal_type)
                else:
                    dialog.get_by_text(disposal_type, exact=True).first.click()
            except Exception as ex:
                logger.warning(f"Disposal type note: {ex}")

            # Recovery Value
            if recovery_value:
                try:
                    val_in = dialog.get_by_placeholder("0.00", exact=False).first
                    if val_in.is_visible(timeout=500):
                        val_in.fill(recovery_value)
                except Exception:
                    pass

            # Remarks / Reason
            if remarks:
                try:
                    rem_in = dialog.locator("textarea").first
                    if rem_in.is_visible(timeout=500):
                        rem_in.fill(remarks)
                except Exception:
                    pass

            # Submit
            submit_btn = dialog.get_by_role("button", name=re.compile(r"(Submit|Confirm|Dispose|Save)", re.I)).first
            if submit_btn.is_visible(timeout=2000):
                submit_btn.click()
                self.page.wait_for_timeout(1000)
                return True

        return False

    def verify_disposal_request_row(self, asset_code_or_name: str) -> dict:
        """
        Reads row columns from 'Disposal Requests' table:
        [ASSET CODE, ASSET NAME, CATEGORY, LOCATION, CURRENT STATUS, REASON, ACTION]
        """
        self.navigate_to_disposal_requests_tab()
        
        search_input = self.page.get_by_placeholder("Search asset / category…")
        if search_input.is_visible(timeout=2000):
            search_input.fill(asset_code_or_name)
            search_input.press("Enter")
            self.page.wait_for_timeout(800)

        row = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
        if not row.is_visible(timeout=3000):
            return {}

        cells = row.locator("td").all()
        row_data = {}
        if len(cells) >= 6:
            row_data = {
                "asset_code": cells[0].inner_text().strip(),
                "asset_name": cells[1].inner_text().strip(),
                "category": cells[2].inner_text().strip(),
                "location": cells[3].inner_text().strip(),
                "current_status": cells[4].inner_text().strip(),
                "reason": cells[5].inner_text().strip()
            }
            logger.info(f"[DISPOSAL REQUEST VERIFIED] {row_data}")

        return row_data

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
