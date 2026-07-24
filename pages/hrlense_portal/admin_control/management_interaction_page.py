import logging
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

from core.config import settings

class ManagementInteractionPage(BasePage):
    def navigate_to_management(self):
        logger.info("Navigating to Management Interaction page")
        try:
            self.page.get_by_role("link", name="Team-Management").click(timeout=5000)
            self.page.get_by_role("link", name="• Management Interaction").click(timeout=5000)
        except Exception:
            logger.info("Navigation click timed out, attempting direct URL navigation")
            self.page.goto(f"{settings.BASE_URL}/GroupHierarchy")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def search_employee(self, employee_name: str):
        logger.info(f"Searching for employee: {employee_name}")
        search_input = self.page.get_by_placeholder("Search employee name")
        search_input.wait_for(state="visible", timeout=5000)
        search_input.click()
        # Force complete React input state clearing using DOM keyboard events
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        search_input.fill(employee_name)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def get_first_employee_with_team(self, exclude: str = "", return_all: bool = False):
        """
        Scans the Management Interaction table and returns employees who have
        visible team members in the View Team modal.
        return_all=True  → returns list of all verified candidate names
        return_all=False → returns first verified name or None
        """
        logger.info("Scanning table for employees with visible team members")
        self.navigate_to_management()

        rows = self.page.locator("tbody tr").all()
        candidates = []
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) < 10:
                continue
            raw   = cells[2].inner_text().strip()
            parts = [p.strip() for p in raw.split("\n") if p.strip()]
            name  = parts[1] if len(parts) >= 2 else parts[0]
            if exclude and exclude.lower() in name.lower():
                continue
            try:
                if int(cells[8].inner_text().strip()) > 0:
                    candidates.append(name)
            except ValueError:
                continue

        logger.info(f"Candidates with team_size > 0: {candidates}")

        verified = []
        for name in candidates:
            members = self.view_team(name)
            if members:
                logger.info(f"Verified team members for: '{name}' ({len(members)} members)")
                if return_all:
                    verified.append(name)
                else:
                    return name

        if return_all:
            return verified
        logger.info("No employee with visible team members found")
        return None

    def get_employee_management_data(self, employee_name: str) -> dict:
        """
        Locates the row for employee_name and returns parsed details:
        {
            "employee": str,
            "branch": str,
            "department": str,
            "designation": str,
            "role": str,
            "team_size": int
        }
        """
        self.search_employee(employee_name)
        logger.info(f"Retrieving management details for employee: {employee_name}")
        row = self.page.locator("tbody tr").filter(has_text=employee_name).first
        try:
            row.wait_for(state="visible", timeout=4000)
            expect(row.locator("td")).to_have_count(10, timeout=4000)
        except Exception:
            logger.info(f"Employee '{employee_name}' is not listed in Team Interaction. Returning default empty values.")
            return {
                "employee": employee_name,
                "branch": "",
                "department": "",
                "designation": "",
                "role": "",
                "team_size": 0
            }
        cells = row.locator("td").all()
        
        data = {
            "employee": cells[2].inner_text().strip(),
            "branch": cells[4].inner_text().strip(),
            "department": cells[5].inner_text().strip(),
            "designation": cells[6].inner_text().strip(),
            "role": cells[7].inner_text().strip(),
            "team_size": int(cells[8].inner_text().strip())
        }
        logger.info(f"Retrieved: {data}")
        return data

    def view_team(self, employee_name: str) -> list[dict]:
        """
        Clicks View Team for the employee and returns combined team members.
        If employee has both TL and Manager roles, iterates all matching rows.
        """
        self.search_employee(employee_name)
        logger.info(f"Viewing team of: {employee_name}")
        self.page.locator("tbody tr").first.wait_for(state="visible", timeout=5000)
        rows = self.page.locator(f"tbody tr:has(td:has-text('{employee_name}'))").all()
        if not rows:
            # fallback: filter by has_text
            rows = self.page.locator("tbody tr").filter(has_text=employee_name).all()
        if not rows:
            logger.info(f"No rows found for '{employee_name}'. Returning empty.")
            return []

        all_members = []
        for idx, row in enumerate(rows):
            try:
                row.wait_for(state="visible", timeout=3000)
                # first row = TL view, last row = Manager view
                row.get_by_label("View").click()
            except Exception:
                logger.info(f"No View button on row {idx} for '{employee_name}', skipping.")
                continue

            self.page.wait_for_selector("role=dialog", state="visible", timeout=8000)
            tbody = self.page.locator("role=dialog").locator("tbody")
            try:
                tbody.locator("tr").first.wait_for(state="visible", timeout=3000)
                for r in tbody.locator("tr").all():
                    cells = r.locator("td").all()
                    if len(cells) >= 7:
                        all_members.append({
                            "name":    cells[2].inner_text().strip(),
                            "company": cells[5].inner_text().strip(),
                            "branch":  cells[6].inner_text().strip()
                        })
            except Exception:
                logger.info(f"No reporting members in modal for row {idx}.")

            self.page.get_by_role("button", name="Close").click()
            self.page.wait_for_selector("role=dialog", state="hidden", timeout=5000)

        logger.info(f"Retrieved {len(all_members)} team members for '{employee_name}': {all_members}")
        return all_members
