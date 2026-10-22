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
        if len(cells) >= 10:
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
                "next_due": cells[8],
                "status": cells[9],
                "has_settle_btn": row.locator("button:has-text('Settle')").is_visible(timeout=1000),
            }
            logger.info(f"Parsed recovery row for '{identifier}': {details}")
            return details
        elif len(cells) >= 9:
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
                "next_due": "",
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
        if not row.is_visible(timeout=5000):
            logger.info(f"Recovery row for '{identifier}' not visible.")
            return False

        settle_btn = row.locator("button:has-text('Settle')").first
        if not settle_btn.is_visible(timeout=3000):
            logger.info(f"'Settle' button for '{identifier}' not visible on row.")
            return False
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

    def create_installment_plan(
        self,
        months_count: int = 2,
        custom_installments: list[dict] = None
    ) -> str:
        """
        Executes 'Installments' plan creation workflow:
        1. Clicks 'Installments' pill/tab button
        2. Selects number of months from dropdown (e.g. 2, 5, 10 months)
        3. Clicks 'Auto split' button to automatically distribute pending balance equally
        4. Optionally customizes dates/amounts if custom_installments provided
        5. Verifies 'Balanced ✓' status
        6. Clicks 'Save Plan' button and captures toast notification
        """
        logger.info(f"UI Action: Creating Installment Plan for {months_count} months")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first

        # 1. Click Installments tab / pill
        # If an installment schedule is already present, plan is already configured
        if modal.locator("text='INSTALLMENT SCHEDULE'").first.is_visible(timeout=1000):
            logger.info("Installment plan already active for this recovery.")
            return "Installment plan already active"

        inst_tab = modal.locator("p:has-text('Installments'), button:has-text('Installments')").first
        if not inst_tab.is_visible(timeout=1500):
            inst_tab = modal.locator("[role='tab']:has-text('Installments'), div:has-text('Installments')").first
        inst_tab.wait_for(state="visible", timeout=3000)
        inst_tab.click()
        self.page.wait_for_timeout(500)

        # 2. Select months count dropdown
        month_select = modal.locator("select").first
        if month_select.is_visible(timeout=2000):
            try:
                month_select.select_option(str(months_count))
            except Exception:
                month_select.select_option(value=str(months_count))
            self.page.wait_for_timeout(300)

        # 3. Click 'Auto split' button
        auto_split_btn = modal.locator("button:has-text('Auto split'), button:has-text('Auto Split')").first
        if auto_split_btn.is_visible(timeout=2000):
            auto_split_btn.click()
            self.page.wait_for_timeout(500)

        # 4. Optional custom installments handling
        if custom_installments:
            rows = modal.locator("div:has(> input[type='number']), div:has(> input[value])").all()
            for idx, item in enumerate(custom_installments):
                if idx < len(rows):
                    row = rows[idx]
                    if "amount" in item:
                        amt_input = row.locator("input[type='number'], input[placeholder*='0' i]").first
                        if amt_input.is_visible():
                            amt_input.fill(str(item["amount"]))
                    if "date" in item:
                        date_input = row.locator("input[type='date'], input[placeholder*='dd' i]").first
                        if date_input.is_visible():
                            date_input.fill(str(item["date"]))

        # 5. Check balance status
        try:
            balanced_el = modal.locator("text=Balanced, text=Planned").first
            if balanced_el.is_visible(timeout=1500):
                logger.info(f"Installment balance status: '{balanced_el.inner_text().strip()}'")
        except Exception:
            pass

        # 6. Click 'Save Plan' button
        save_btn = modal.locator("button:has-text('Save Plan'), button:has-text('Save')").first
        if not save_btn.is_visible(timeout=2000):
            save_btn = modal.get_by_role("button", name="Save Plan").first
        save_btn.wait_for(state="visible", timeout=3000)
        save_btn.click()

        toast = self.wait_for_toast(timeout=5000)
        logger.info(f"Save Installment Plan toast: '{toast}'")
        return toast

    def get_installment_plan_details(self) -> dict:
        """
        Reads visible installment rows and balance summary from Settle Recovery modal.
        Returns:
        {
            'installments': [{'num': 1, 'date': '10/06/2026', 'amount': '1000'}, ...],
            'planned_status': 'Planned ₹2,000 of ₹2,000',
            'is_balanced': True
        }
        """
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        details = {"installments": [], "planned_status": "", "is_balanced": False}

        try:
            # Check for Balanced badge
            balanced_badge = modal.locator("text=Balanced, text=Planned").first
            if balanced_badge.is_visible(timeout=1500):
                details["planned_status"] = balanced_badge.inner_text().strip()
                details["is_balanced"] = "balanced" in details["planned_status"].lower()
        except Exception:
            pass

        return details

    def get_installment_schedule_items(self) -> List[Dict[str, Union[str, bool]]]:
        """
        Reads saved 'INSTALLMENT SCHEDULE' cards in the Settle Recovery modal:
        [
            {'num': '#1', 'amount': '₹1,000', 'due_date': 'Due 05 Oct 2026', 'status': 'PENDING', 'can_pay': True},
            {'num': '#2', 'amount': '₹1,000', 'due_date': 'Due 05 Nov 2026', 'status': 'PENDING', 'can_pay': True}
        ]
        """
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        items = []
        schedule_section = modal.locator("div:has(> p:text-matches('INSTALLMENT SCHEDULE', 'i')), div:has-text('INSTALLMENT SCHEDULE')").first
        if not schedule_section.is_visible(timeout=2000):
            return items

        # Look for cards matching #1, #2...
        cards = modal.locator("div:has(> div:has-text('#')), div:has(> span:has-text('#'))").all()
        if not cards:
            cards = modal.locator("div.css-0, div").filter(has_text=re.compile(r"^#\d+")).all()

        for card in cards:
            text = card.inner_text().strip()
            if "#" in text and ("Due" in text or "PENDING" in text or "PAID" in text):
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                num_match = re.search(r"#\d+", text)
                amt_match = re.search(r"₹[\d,]+", text)
                due_match = re.search(r"Due\s+[^\n]+", text)
                status_match = re.search(r"(PENDING|PAID|SETTLED)", text, re.I)

                pay_btn = card.locator("button:has-text('Pay')").first
                items.append({
                    "num": num_match.group(0) if num_match else "",
                    "amount": amt_match.group(0) if amt_match else "",
                    "due_date": due_match.group(0) if due_match else "",
                    "status": status_match.group(0) if status_match else "",
                    "can_pay": pay_btn.is_visible(timeout=500) if pay_btn else False,
                })

        logger.info(f"Parsed Installment Schedule items: {items}")
        return items

    def click_revise_plan(self) -> bool:
        """Clicks 'Revise plan' button to modify an active installment plan."""
        logger.info("UI Action: Clicking 'Revise plan' button")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        revise_btn = modal.locator("button:has-text('Revise plan')").first
        revise_btn.wait_for(state="visible", timeout=3000)
        revise_btn.click()
        self.page.wait_for_timeout(500)
        return True

    def click_pay_installment(self, installment_num: int = 1) -> bool:
        """Clicks 'Pay' button for a specific installment number in the schedule."""
        logger.info(f"UI Action: Clicking 'Pay' for installment #{installment_num}")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        card = modal.locator(f"div:has-text('#{installment_num}')").filter(has_text="Due").first
        card.wait_for(state="visible", timeout=3000)
        pay_btn = card.locator("button:has-text('Pay')").first
        pay_btn.wait_for(state="visible", timeout=2000)
        pay_btn.click()
        self.page.wait_for_timeout(500)
        return True

