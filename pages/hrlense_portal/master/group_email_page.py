"""
HRlens Portal — Group Email Master Page Object.
Route: /master/group-email

Covers:
1. Navigation and tab management:
   - Company
   - Branch
   - Branch + Department
   - Branch Group
   - Branch Group + Department
   - Global
2. Grid inspection (headers, entity names, row counts).
3. Email input handling (reading, filling, pressing Enter, clearing).
4. Global tab inspection (group scope, configured recipients, status).
5. Validation & Chakra toast capture.
"""

import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class GroupEmailPage(BasePage):
    """Page Object Model for Group Email Master (/master/group-email)."""

    PAGE_ROUTE = "/master/group-email"

    EXPECTED_TABS = [
        "Company",
        "Branch",
        "Branch + Department",
        "Branch Group",
        "Branch Group + Department",
        "Global",
    ]

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_group_email(self) -> None:
        """Navigates to the Group Email Master page."""
        url = f"{settings.BASE_URL}{self.PAGE_ROUTE}"
        logger.info(f"Navigating to Group Email Master: {url}")
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1000)

        # Handle login redirect if session expired
        if "/login" in self.page.url or self.page.locator("input[type='password']").is_visible():
            from core.auth.auth_manager import authenticate_user
            logger.info("Session expired or redirected to login. Re-authenticating as admin...")
            authenticate_user(self.page, "admin")
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)

        self.page.wait_for_selector("[role='tab']", timeout=15000)

    # ──────────────────────────────────────────────────────────────────────────
    # TABS LOCATORS & ACTIONS
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def tabs(self) -> Locator:
        """Returns all tab locator elements."""
        return self.page.locator("[role='tab']")

    def get_available_tabs(self) -> List[str]:
        """Returns the inner texts of all available tabs."""
        return [t.strip() for t in self.tabs.all_inner_texts() if t.strip()]

    def get_active_tab_name(self) -> str:
        """Returns the currently selected / active tab name."""
        active_tab = self.page.locator("[role='tab'][aria-selected='true']").first
        if active_tab.is_visible(timeout=2000):
            return active_tab.inner_text().strip()
        return ""

    def select_tab(self, tab_name: str) -> None:
        """Clicks the tab matching the given name and waits for table update."""
        logger.info(f"Selecting tab: '{tab_name}'")
        tab = self.page.locator(f"[role='tab']:has-text('{tab_name}')").first
        tab.wait_for(state="visible", timeout=5000)
        tab.click()
        self.page.wait_for_timeout(600)

    # ──────────────────────────────────────────────────────────────────────────
    # TABLE & HEADERS
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def table_headers(self) -> Locator:
        """Returns column headers locator."""
        return self.page.locator("th, [role='columnheader']")

    def get_column_header_titles(self) -> List[str]:
        """Returns list of column header texts in order."""
        return [h.strip() for h in self.table_headers.all_inner_texts() if h.strip()]

    @property
    def table_rows(self) -> Locator:
        """Returns all table body rows."""
        return self.page.locator("table tbody tr")

    def get_row_count(self) -> int:
        """Returns the count of table body rows."""
        return self.table_rows.count()

    def get_row_names(self) -> List[str]:
        """Returns entity names from column 2 (e.g. company or branch name) for each row."""
        names = []
        rows = self.table_rows.all()
        for r in rows:
            cells = r.locator("td").all()
            if len(cells) >= 2:
                names.append(cells[1].inner_text().strip())
        return names

    # ──────────────────────────────────────────────────────────────────────────
    # EMAIL INPUTS & UPDATES
    # ──────────────────────────────────────────────────────────────────────────

    def get_email_input(self, row_index: int = 0) -> Locator:
        """Returns the email input field for the specified row index (0-based)."""
        row = self.table_rows.nth(row_index)
        inp = row.locator("input[placeholder*='email' i], input[type='text'], input[type='email']").first
        inp.wait_for(state="visible", timeout=5000)
        return inp

    def get_email_input_by_name(self, entity_name: str) -> Locator:
        """Returns the email input field for the row matching the entity name."""
        row = self.table_rows.filter(has_text=entity_name).first
        row.wait_for(state="visible", timeout=5000)
        inp = row.locator("input[placeholder*='email' i], input[type='text'], input[type='email']").first
        return inp

    def get_email_value(self, row_index: int = 0) -> str:
        """Reads the current value of the email input in the specified row."""
        return self.get_email_input(row_index).input_value().strip()

    def get_email_value_by_name(self, entity_name: str) -> str:
        """Reads the current value of the email input in the row with given entity name."""
        return self.get_email_input_by_name(entity_name).input_value().strip()

    def fill_email(self, row_index: int, email: str, press_enter: bool = True) -> str:
        """
        Fills the email field in the given row index.
        Optionally presses Enter to submit and captures the resulting Chakra toast.
        """
        logger.info(f"Setting email for row {row_index} to: '{email}'")
        inp = self.get_email_input(row_index)
        inp.click()
        inp.fill("")
        inp.fill(email)

        toast_msg = ""
        if press_enter:
            inp.press("Enter")
            toast_msg = self.wait_for_toast(timeout=5000)
            logger.info(f"Toast after Enter on row {row_index}: '{toast_msg}'")
        return toast_msg

    def fill_email_by_name(self, entity_name: str, email: str, press_enter: bool = True) -> str:
        """
        Fills the email field for the row matching the given entity name.
        Optionally presses Enter to submit and captures the resulting Chakra toast.
        """
        logger.info(f"Setting email for '{entity_name}' to: '{email}'")
        inp = self.get_email_input_by_name(entity_name)
        inp.click()
        inp.fill("")
        inp.fill(email)

        toast_msg = ""
        if press_enter:
            inp.press("Enter")
            toast_msg = self.wait_for_toast(timeout=5000)
            logger.info(f"Toast after Enter for '{entity_name}': '{toast_msg}'")
        return toast_msg

    # ──────────────────────────────────────────────────────────────────────────
    # GLOBAL TAB SPECIFIC
    # ──────────────────────────────────────────────────────────────────────────

    def get_global_table_data(self) -> List[Dict[str, Any]]:
        """
        Parses all rows in the Global tab table and returns structured dictionary list:
        [{'s_no': '1', 'group_scope': '...', 'configured_recipients': '...', 'total_recipients': '...', 'status': '...'}]
        """
        data = []
        rows = self.table_rows.all()
        for i, row in enumerate(rows):
            cells = row.locator("td").all()
            cell_texts = [c.inner_text().strip() for c in cells]
            inputs = [inp.input_value().strip() for inp in row.locator("input").all()]
            buttons = [b.inner_text().strip() for b in row.locator("button").all()]
            badges = [b.inner_text().strip() for b in row.locator(".chakra-badge, span[class*='badge']").all()]
            switches = row.locator("input[type='checkbox'], .chakra-switch").count()

            row_dict = {
                "row_index": i,
                "cell_texts": cell_texts,
                "inputs": inputs,
                "buttons": buttons,
                "badges": badges,
                "switches_count": switches,
            }
            if len(cell_texts) >= 5:
                row_dict.update({
                    "s_no": cell_texts[0],
                    "group_scope": cell_texts[1],
                    "configured_recipients": cell_texts[2],
                    "total_recipients": cell_texts[3],
                    "status": cell_texts[4],
                })
            data.append(row_dict)
        return data
