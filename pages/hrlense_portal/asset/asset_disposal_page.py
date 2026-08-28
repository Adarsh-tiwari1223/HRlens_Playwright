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
            # Select Disposal Type (Scrap / Sell / Write-Off) from radio group
            try:
                # 1. Try exact radio input by value
                radio_in = dialog.locator(f"input[type='radio'][value*='{disposal_type}' i]").first
                if radio_in.is_visible(timeout=500):
                    radio_in.click(force=True)
                    logger.info(f"Checked Disposal Type radio: '{disposal_type}'")
                else:
                    # 2. Click radio label or badge element with matching text
                    radio_btn = dialog.locator("label.chakra-radio, div.chakra-radio, span.chakra-radio__label, button, label").filter(has_text=re.compile(f"^{re.escape(disposal_type)}$", re.I)).last
                    if radio_btn.is_visible(timeout=1000):
                        radio_btn.click(force=True)
                        logger.info(f"Clicked Disposal Type element: '{disposal_type}'")
            except Exception as ex:
                logger.warning(f"Disposal type note: {ex}")

            # Fill Disposal Date * (defaults to today)
            try:
                disposal_date = kwargs.get("disposal_date", datetime.date.today().strftime("%Y-%m-%d"))
                date_in = dialog.locator("//div[./label[contains(text(), 'Disposal Date')]]//input, input[type='date']").first
                if date_in.is_visible(timeout=1000):
                    date_in.fill(disposal_date)
                    logger.info(f"Filled Disposal Date: '{disposal_date}'")
            except Exception as e:
                logger.warning(f"Disposal date fill note: {e}")

            # Recovery Value
            if recovery_value:
                try:
                    val_in = dialog.locator("input[placeholder*='0.00' i], input[type='number'], input[name*='recovery' i]").first
                    if val_in.is_visible(timeout=500):
                        val_in.fill(str(recovery_value))
                        logger.info(f"Filled Recovery Value: '{recovery_value}'")
                except Exception:
                    pass

            # Remarks / Reason
            if remarks:
                try:
                    rem_in = dialog.locator("textarea[placeholder*='detail' i], textarea.chakra-textarea, textarea").first
                    if rem_in.is_visible(timeout=500):
                        rem_in.fill(remarks)
                        logger.info(f"Filled Remarks: '{remarks}'")
                except Exception:
                    pass

            # Submit Disposal Action
            submit_btn = dialog.get_by_role("button", name=re.compile(r"(Submit|Confirm|Dispose|Save|Complete)", re.I)).first
            if not submit_btn.is_visible(timeout=1000):
                submit_btn = dialog.locator("button.chakra-button, button[type='submit']").filter(has_text=re.compile(r"Dispose|Submit|Confirm", re.I)).first

            if submit_btn.is_visible(timeout=2000):
                submit_btn.scroll_into_view_if_needed()
                submit_btn.click()
                self.page.wait_for_timeout(1000)
                toast = self.wait_for_toast_message()
                logger.info(f"Disposal confirmation toast: '{toast}'")
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
