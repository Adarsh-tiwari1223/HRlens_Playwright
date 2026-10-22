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
        """Navigates to Asset Disposal / Scrap page via submenu item if visible, otherwise directly redirects using URL."""
        logger.info("Navigating to Asset Disposal / Scrap page")
        target_url = f"{settings.BASE_URL}/asset-disposal"
        try:
            # 1. Look for submenu link directly
            link = self.page.locator("a.submenu_item[href*='/asset-disposal'], a[href*='/asset-disposal']").first
            if not link.is_visible(timeout=1000):
                # Expand parent Asset sidebar menu if present
                for parent_sel in ["Asset", "Assets", "Asset Management"]:
                    parent = self.page.locator(".sidebar, nav, aside").locator("div, p, a, button").filter(has_text=re.compile(rf"^{parent_sel}$", re.I)).first
                    if parent.is_visible(timeout=500):
                        parent.scroll_into_view_if_needed()
                        parent.click()
                        self.page.wait_for_timeout(500)
                        break

            link = self.page.locator("a.submenu_item[href*='/asset-disposal'], a[href*='/asset-disposal']").first
            if link.is_visible(timeout=1500):
                link.scroll_into_view_if_needed()
                link.click()
                logger.info("Clicked submenu item for /asset-disposal")
            else:
                logger.info("Submenu UI link hidden; directly redirecting to /asset-disposal using URL")
                self.page.goto(target_url, wait_until="domcontentloaded")
        except Exception as ex:
            logger.info(f"Submenu note ({ex}); directly redirecting to /asset-disposal using URL")
            self.page.goto(target_url, wait_until="domcontentloaded")

        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

        # Ensure page is on /asset-disposal
        if "/asset-disposal" not in self.page.url:
            logger.info("Page URL not /asset-disposal; executing direct URL redirect")
            self.page.goto(target_url, wait_until="domcontentloaded")
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1000)
        
        # Verify page header
        try:
            self.page.get_by_text("Asset Disposal / Scrap", exact=False).wait_for(state="visible", timeout=5000)
        except Exception:
            pass

    def get_metrics_summary(self) -> dict:
        """Reads metric card values: Disposal Queue, Disposed Assets, Recovery Value, Lost Assets."""
        metrics = {}
        try:
            self.page.wait_for_timeout(1000)
            for label_key, label_text in [
                ("disposal_queue", "Disposal Queue"),
                ("disposed_assets", "Disposed Assets"),
                ("recovery_value", "Recovery Value"),
                ("lost_assets", "Lost Assets"),
            ]:
                card = self.page.locator(f"div:has(> p:has-text('{label_text}'))").first
                if not card.is_visible(timeout=1000):
                    card = self.page.locator("div").filter(has_text=re.compile(rf"{label_text}", re.I)).first
                if card.is_visible(timeout=1000):
                    txt = card.inner_text().strip()
                    lines = [l.strip() for l in txt.split("\n") if l.strip()]
                    val = [l for l in lines if label_text.lower() not in l.lower()]
                    metrics[label_key] = val[0] if val else "0"
        except Exception as ex:
            logger.warning(f"Metrics read note: {ex}")

        # Fallback to general stat classes if empty
        if not metrics:
            try:
                cards = self.page.locator(".chakra-stat, .css-1c250ic, div.chakra-stack").all()
                for c in cards:
                    txt = c.inner_text().strip()
                    lines = [l.strip() for l in txt.split("\n") if l.strip()]
                    for label_key, label_text in [
                        ("disposal_queue", "Disposal Queue"),
                        ("disposed_assets", "Disposed Assets"),
                        ("recovery_value", "Recovery Value"),
                        ("lost_assets", "Lost Assets"),
                    ]:
                        if any(label_text in l for l in lines):
                            val = [l for l in lines if label_text not in l]
                            metrics[label_key] = val[0] if val else "0"
            except Exception as ex:
                logger.warning(f"General stat fallback note: {ex}")

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

    def has_disposal_requests_data(self) -> bool:
        """
        Checks whether the 'Disposal Requests' table has data rows.
        Returns False if the table is empty or displays 'No pending disposal requests'.
        """
        self.navigate_to_disposal_requests_tab()
        
        empty_state = self.page.locator("p, div").filter(has_text=re.compile(r"No pending disposal requests|No data", re.I)).first
        if empty_state.is_visible(timeout=1500):
            logger.info("Disposal Requests tab displays empty state: 'No pending disposal requests'")
            return False

        table_rows = self.page.locator("table tbody tr")
        if table_rows.first.is_visible(timeout=2000):
            count = table_rows.count()
            logger.info(f"Disposal Requests table has {count} row(s)")
            return count > 0
        return False

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
        
        # Guard against empty state
        empty_state = self.page.locator("p, div").filter(has_text=re.compile(r"No pending disposal requests|No data", re.I)).first
        if empty_state.is_visible(timeout=1500):
            logger.info(f"verify_disposal_request_row: Empty state active, no rows available for '{asset_code_or_name}'")
            return {}

        search_input = self.page.locator("input[placeholder*='Search asset / category' i], input[placeholder*='Search' i]").first
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
        return {}

    def is_asset_in_disposal_requests(self, asset_code_or_name: str) -> bool:
        """
        Navigates to Disposal Requests tab and checks that target asset is listed in the table.
        Guarded against empty state so it never crashes with TimeoutError.
        """
        self.navigate_to_disposal_requests_tab()
        clean_code = asset_code_or_name.strip()
        
        # Guard against empty state
        empty_state = self.page.locator("p, div").filter(has_text=re.compile(r"No pending disposal requests|No data", re.I)).first
        if empty_state.is_visible(timeout=1500):
            logger.info(f"Disposal Requests tab displays empty state; asset '{clean_code}' is not listed.")
            return False

        search_input = self.page.locator("input[placeholder*='Search asset / category' i], input[placeholder*='Search' i]").first
        if search_input.is_visible(timeout=2000):
            search_input.click()
            search_input.fill("")
            search_input.fill(clean_code)
            search_input.press("Enter")
            self.page.wait_for_timeout(1200)

        row = self.page.locator("table tbody tr").filter(has_text=clean_code).first
        if row.is_visible(timeout=2500):
            logger.info(f"Asset '{clean_code}' found in Disposal Requests table row.")
            return True

        table = self.page.locator("table tbody").first
        if table.is_visible(timeout=2000):
            if clean_code.lower() in table.inner_text().lower():
                logger.info(f"Asset '{clean_code}' found in Disposal Requests table text.")
                return True

        # Fallback: clear search and check default table
        if search_input.is_visible(timeout=1000):
            search_input.fill("")
            self.page.wait_for_timeout(1000)
            table_fb = self.page.locator("table tbody").first
            if table_fb.is_visible(timeout=1500):
                if clean_code.lower() in table_fb.inner_text().lower():
                    logger.info(f"Asset '{clean_code}' found in default Disposal Requests table.")
                    return True

        logger.info(f"Asset '{clean_code}' was NOT found in Disposal Requests table.")
        return False

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
