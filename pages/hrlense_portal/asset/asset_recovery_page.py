"""
HRlens Portal — Asset Recovery Page Object (UI Tier).

Handles UI interactions for https://stg-hrlense.jobvritta.com/asset-recovery:
- Metric cards: Total Recoverable, Recovered, Pending, Open Cases
- Tabs: All, Pending, Partially Settled, Settled
- Search & Table row inspection
- Settlement recording & status verification
"""

import logging
import re
from typing import Dict, List, Union
from playwright.sync_api import Page
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetRecoveryPage(BasePage):
    """Page Object for Asset Recovery & Settlement Tracking module."""

    SEARCH_INPUT = "input[placeholder*='Search asset / employee' i], input[placeholder*='Search' i]"

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_asset_recovery(self) -> None:
        """Navigates directly to /asset-recovery page and waits for header."""
        logger.info("UI Action: Navigating to /asset-recovery")
        try:
            self.page.bring_to_front()
        except Exception:
            pass

        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/asset-recovery"
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.dismiss_all_floating_alerts()

        # Wait for Asset Recovery title or KPI cards
        self.page.locator(
            "h2:has-text('Asset Recovery'), p:has-text('Asset Recovery'), "
            "div:has-text('Total Recoverable'), div:has-text('Open Cases')"
        ).first.wait_for(state="visible", timeout=10000)

    def get_kpi_metrics(self) -> Dict[str, str]:
        """
        Reads KPI summary card values using exact DOM structure:
        - Total Recoverable (e.g. ₹0)
        - Recovered (e.g. ₹0)
        - Pending (e.g. ₹0)
        - Open Cases (e.g. 0)
        """
        logger.info("UI Check: Reading /asset-recovery KPI metric cards")
        metrics = {
            "total_recoverable": "0",
            "recovered": "0",
            "pending": "0",
            "open_cases": "0",
        }

        try:
            tot_card = self.page.locator("div:has(> p:has-text('Total Recoverable'))").first
            if tot_card.is_visible(timeout=2000):
                metrics["total_recoverable"] = tot_card.locator("p").first.inner_text().replace("₹", "").strip()

            rec_card = self.page.locator("div:has(> p:has-text('Recovered'))").first
            if rec_card.is_visible(timeout=2000):
                metrics["recovered"] = rec_card.locator("p").first.inner_text().replace("₹", "").strip()

            pen_card = self.page.locator("div:has(> p:has-text('Pending'))").first
            if pen_card.is_visible(timeout=2000):
                metrics["pending"] = pen_card.locator("p").first.inner_text().replace("₹", "").strip()

            cases_card = self.page.locator("div:has(> p:has-text('Open Cases'))").first
            if cases_card.is_visible(timeout=2000):
                metrics["open_cases"] = cases_card.locator("p").first.inner_text().strip()
        except Exception as ex:
            logger.warning(f"KPI extraction note: {ex}")

        logger.info(f"Asset Recovery KPI Metrics: {metrics}")
        return metrics

    def is_empty_state_visible(self) -> bool:
        """Checks if 'No recovery records' or 'No records found' is visible."""
        return self.page.locator("p:has-text('No recovery records'), p:has-text('No records found')").first.is_visible(timeout=3000)

        logger.info(f"Asset Recovery KPI Metrics: {metrics}")
        return metrics

    def switch_tab(self, tab_name: str = "Pending") -> None:
        """Switches between tabs: All, Pending, Partially Settled, Settled."""
        logger.info(f"UI Action: Switching to tab '{tab_name}' on /asset-recovery")
        tab = self.page.locator(f"button[role='tab']:has-text('{tab_name}'), a:has-text('{tab_name}'), div[role='tab']:has-text('{tab_name}')").first
        tab.wait_for(state="visible", timeout=5000)
        tab.click()
        self.page.wait_for_timeout(500)

    def search_record(self, query: str) -> None:
        """Types query in 'Search asset / employee...' input field."""
        logger.info(f"UI Action: Searching asset recovery record -> '{query}'")
        search_in = self.page.locator(self.SEARCH_INPUT).first
        search_in.wait_for(state="visible", timeout=5000)
        search_in.fill(query)
        search_in.press("Enter")
        self.page.wait_for_timeout(1000)

    def get_recovery_row_details(self, identifier: str) -> Dict[str, Union[bool, str]]:
        """
        Searches and reads row details matching employee name or asset code:
        Parses exact columns: Asset Code, Asset Name, Employee, Reason, Return Date, Total, Recovered, Balance, Status
        """
        logger.info(f"UI Check: Looking for recovery record -> '{identifier}'")
        self.search_record(identifier)

        row = self.page.locator(f"table tbody tr:has-text('{identifier}')").first
        if not row.is_visible(timeout=3000):
            logger.info(f"No recovery record found for '{identifier}'")
            return {"found": False}

        cells = [c.strip() for c in row.locator("td").all_inner_texts()]
        if len(cells) >= 9:
            details = {
                "found": True,
                "asset_code": cells[0],
                "asset_name": cells[1],
                "employee": cells[2],
                "reason": cells[3],
                "return_date": cells[4],
                "total": cells[5],
                "recovered": cells[6],
                "balance": cells[7],
                "status": cells[8],
                "has_settle_btn": row.locator("button:has-text('Settle')").is_visible(timeout=1000),
            }
            logger.info(f"Parsed recovery row for '{identifier}': {details}")
            return details

        return {"found": True, "row_text": " | ".join(cells)}

    def click_settle_button(self, identifier: str) -> bool:
        """Clicks 'Settle' button on target recovery row and waits for modal."""
        logger.info(f"UI Action: Clicking 'Settle' button for '{identifier}'")
        self.search_record(identifier)

        row = self.page.locator(f"table tbody tr:has-text('{identifier}')").first
        row.wait_for(state="visible", timeout=5000)

        settle_btn = row.locator("button:has-text('Settle')").first
        settle_btn.wait_for(state="visible", timeout=3000)
        settle_btn.click()

        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        modal.wait_for(state="visible", timeout=5000)
        return modal.is_visible()

    def get_settle_modal_details(self) -> Dict[str, str]:
        """
        Reads summary details from the open Settle Recovery modal:
        - Asset, Employee, Reason, Return Date, Total Recovery, Already Recovered, Pending Balance
        """
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        details = {}
        for block in modal.locator("div.css-97pxie").all():
            label = block.locator("p").first.inner_text().strip()
            val = block.locator("p").last.inner_text().strip()
            details[label] = val
        logger.info(f"Settle Recovery Modal Summary: {details}")
        return details

    def settle_in_full(
        self,
        payment_mode: str = "Salary Deduction",
        settlement_date: str = None,
        reference_no: str = "",
        remarks: str = "Settled in full via salary deduction"
    ) -> str:
        """
        Executes 'Full' settlement workflow:
        1. Ensures 'Full (...)' pill is selected
        2. Fills Settlement Date (if provided)
        3. Selects Payment Mode ('Cash', 'Bank Transfer', 'UPI', 'Cheque', 'Salary Deduction')
        4. Fills Reference No & Remarks
        5. Clicks 'Settle in Full' button and captures toast
        """
        logger.info(f"UI Action: Executing Full Settlement via Mode: '{payment_mode}'")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first

        # Ensure Full option is active
        full_pill = modal.locator("p:has-text('Full')").first
        if full_pill.is_visible(timeout=1000):
            full_pill.click()
            self.page.wait_for_timeout(300)

        # Date
        if settlement_date:
            date_in = modal.locator("input[type='date']").first
            if date_in.is_visible(timeout=1000):
                date_in.fill(settlement_date)

        # Payment Mode
        mode_select = modal.locator("select").first
        if mode_select.is_visible(timeout=1000):
            mode_select.select_option(label=payment_mode)

        # Reference No
        if reference_no:
            ref_in = modal.locator("input[placeholder*='receipt' i], input[placeholder*='Txn' i]").first
            if ref_in.is_visible(timeout=1000):
                ref_in.fill(reference_no)

        # Remarks
        if remarks:
            rem_in = modal.locator("textarea").first
            if rem_in.is_visible(timeout=1000):
                rem_in.fill(remarks)

        # Click 'Settle in Full'
        submit_btn = modal.locator("button:has-text('Settle in Full')").first
        submit_btn.wait_for(state="visible", timeout=3000)
        submit_btn.click()

        toast = self.wait_for_toast(timeout=5000)
        logger.info(f"Settle in Full toast: '{toast}'")
        return toast

    def record_partial_settlement(
        self,
        amount: str = "2000",
        payment_mode: str = "Salary Deduction",
        settlement_date: str = None,
        reference_no: str = "",
        remarks: str = "Partial recovery recorded"
    ) -> str:
        """
        Executes 'Partial' settlement workflow:
        1. Clicks 'Partial' pill
        2. Fills Partial Amount (e.g. ₹2,000)
        3. Fills Settlement Date (if provided)
        4. Selects Payment Mode ('Cash', 'Bank Transfer', 'UPI', 'Cheque', 'Salary Deduction')
        5. Fills Reference No & Remarks
        6. Clicks 'Record Payment' button and captures toast
        """
        logger.info(f"UI Action: Executing Partial Settlement: ₹{amount} via Mode: '{payment_mode}'")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first

        # Click Partial option
        partial_pill = modal.locator("p:has-text('Partial')").first
        partial_pill.wait_for(state="visible", timeout=2000)
        partial_pill.click()
        self.page.wait_for_timeout(500)

        # Amount input (max pending balance)
        amt_in = modal.locator("input[placeholder='0.00'], input[type='number']").first
        amt_in.wait_for(state="visible", timeout=2000)
        amt_in.fill(str(amount))

        # Date
        if settlement_date:
            date_in = modal.locator("input[type='date']").first
            if date_in.is_visible(timeout=1000):
                date_in.fill(settlement_date)

        # Payment Mode
        mode_select = modal.locator("select").first
        if mode_select.is_visible(timeout=1000):
            mode_select.select_option(label=payment_mode)

        # Reference No
        if reference_no:
            ref_in = modal.locator("input[placeholder*='receipt' i], input[placeholder*='Txn' i]").first
            if ref_in.is_visible(timeout=1000):
                ref_in.fill(reference_no)

        # Remarks
        if remarks:
            rem_in = modal.locator("textarea").first
            if rem_in.is_visible(timeout=1000):
                rem_in.fill(remarks)

        # Click 'Record Payment'
        submit_btn = modal.locator("button:has-text('Record Payment')").first
        submit_btn.wait_for(state="visible", timeout=3000)
        submit_btn.click()

        toast = self.wait_for_toast(timeout=5000)
        logger.info(f"Record Partial Payment toast: '{toast}'")
        return toast
