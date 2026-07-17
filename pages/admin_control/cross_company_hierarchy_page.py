import logging
import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class CrossCompanyHierarchyPage(BasePage):
    def navigate_to_hierarchy(self):
        logger.info("Navigating to Cross Company Hierarchy page")
        try:
            self.page.get_by_role("link", name="Admin Control").click(timeout=5000)
            self.page.get_by_role("link", name="• Cross Company Hierarchy").click(timeout=5000)
        except Exception:
            logger.info("Navigation click timed out, attempting direct URL navigation")
            self.page.goto(f"{settings.BASE_URL}/admin/cross-company-hierarchy")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def get_table_data(self) -> list[dict]:
        """
        Reads and returns the list of rows currently displayed in the table.
        Each row is parsed as a dictionary:
        {
            "s_no": str,
            "employee": str,
            "default_company": str,
            "default_access": str,
            "assigned_branches": str
        }
        """
        self.page.locator("tbody tr").first.wait_for(state="visible", timeout=5000)
        row_locators = self.page.locator("tbody tr").all()
        table_rows = []
        for row in row_locators:
            cells = row.locator("td").all()
            if len(cells) >= 5:
                row_data = {
                    "s_no": cells[0].inner_text().strip(),
                    "employee": cells[1].inner_text().strip(),
                    "default_company": cells[2].inner_text().strip(),
                    "default_access": cells[3].inner_text().strip(),
                    "assigned_branches": cells[4].inner_text().strip()
                }
                table_rows.append(row_data)
        logger.info(f"Table content read: {len(table_rows)} rows found")
        return table_rows

    def search_employee(self, employee_name: str):
        logger.info(f"Searching for employee in hierarchy table: {employee_name}")
        search_input = self.page.locator("input[placeholder*='Search']").first
        search_input.wait_for(state="visible", timeout=5000)
        search_input.click()
        # Force complete React input state clearing using DOM keyboard events
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        search_input.fill(employee_name)
        search_input.press("Enter")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def edit_employee_hierarchy(self, employee_name: str):
        """
        Finds the row containing employee_name inside tbody and clicks its Edit button.
        """
        self.search_employee(employee_name)
        logger.info(f"Opening hierarchy editor for employee: {employee_name}")
        row = self.page.locator("tbody tr").filter(has_text=employee_name).first
        row.get_by_label("Edit").click()
        self.page.wait_for_selector("role=dialog", state="visible", timeout=8000)

    def get_default_company_branch(self) -> tuple[str, str]:
        """
        Reads the Company and Branch readonly textboxes from the open Edit drawer.
        Returns (company, branch) as plain strings.
        """
        dialog = self.page.locator("role=dialog")
        company = dialog.get_by_role("textbox", name="Company").input_value()
        # Branch textbox is readonly — disambiguate from the "Search branches" input
        branch = dialog.locator("input[aria-readonly='true']").nth(1).input_value()
        logger.info(f"Default company: '{company}' | Default branch: '{branch}'")
        return company.strip(), branch.strip()

    def toggle_exclude_employee(self, exclude: bool):
        """
        Toggles the switch track for excluding employee.
        """
        switch = self.page.locator(".chakra-switch__track")
        checkbox = self.page.locator(".chakra-switch__input")
        checkbox.wait_for(state="attached", timeout=5000)
        current_state = checkbox.is_checked()
        if current_state != exclude:
            switch.click()
            logger.info(f"Exclusion switch: {exclude}")
        else:
            logger.info(f"Exclusion switch: {exclude}")

    def select_branch(self, branch_name: str, checked: bool = None) -> bool:
        """
        Selects or deselects a branch in the Edit Drawer.

        If branch_name matches the employee's default company/branch (read from
        the Company + Branch textboxes), the exclude switch is toggled instead
        of the checkbox — because the default branch cannot be unchecked directly.

        Args:
            branch_name: Full label e.g. 'Agra (Vyze INC)'
            checked: True=select, False=deselect, None=toggle

        Returns:
            True if state was changed, False if already in desired state.
        """
        # --- Check if this is the employee's default branch ---
        default_company, default_branch = self.get_default_company_branch()
        branch_part  = branch_name.split("(")[0].strip()
        company_part = branch_name.split("(")[1].rstrip(")").strip() if "(" in branch_name else ""

        is_default = (
            branch_part.lower()  == default_branch.lower() and
            company_part.lower() == default_company.lower()
        )

        if is_default:
            logger.info(f"Branch '{branch_name}' is the default branch — skipping, state unchanged")
            return False

        # --- Normal checkbox flow for non-default branches ---
        dialog = self.page.locator("role=dialog")
        search_input = dialog.locator("input[placeholder*='Search branches']")
        search_input.wait_for(state="visible", timeout=5000)
        search_input.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        search_input.fill(branch_part)
        self.page.wait_for_timeout(1000)

        checkbox = dialog.locator(
            f"xpath=.//p[normalize-space(.)='{branch_name}']"
            f"/../../label//input[@type='checkbox']"
        )
        checkbox.wait_for(state="attached", timeout=5000)

        label = dialog.locator(
            f"xpath=.//p[normalize-space(.)='{branch_name}']"
            f"/../../label[contains(@class,'chakra-checkbox')]"
        )

        current = checkbox.is_checked()
        clicked = False

        if checked is None:
            label.click()
            clicked = True
            action = "deselected" if current else "selected"
        elif checked and not current:
            label.click()
            clicked = True
            action = "selected"
        elif not checked and current:
            label.click()
            clicked = True
            action = "deselected"
        else:
            action = "already " + ("selected" if checked else "deselected")

        logger.info(f"Branch '{branch_name}': {action}")
        # Clear filter with single fill('') so all branches are visible when Update fires
        # (fill is one synthetic event — does not reset checkbox state unlike Ctrl+A+Backspace)
        search_input.fill("")
        self.page.wait_for_timeout(300)
        return clicked

    def get_assigned_branch_count(self, employee_name: str) -> int:
        """
        Opens the Edit drawer for employee_name and counts how many branch
        checkboxes are currently checked. Closes the drawer afterwards.
        """
        self.edit_employee_hierarchy(employee_name)
        dialog = self.page.locator("role=dialog")
        checked = dialog.locator(
            "input.chakra-checkbox__input[data-checked], "
            "input.chakra-checkbox__input:checked, "
            "[data-checked] input[type='checkbox']"
        ).count()
        logger.info(f"[{employee_name}] assigned branch count: {checked}")
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)
        return checked

    def ensure_two_branches(self, employee_name: str, required_branch: str) -> str | None:
        """
        Opens the Edit drawer and ensures the employee has at least 2 branches selected.
        Selects the first available unchecked branch if needed.
        Returns the branch name added, or None if already had 2+.
        """
        self.edit_employee_hierarchy(employee_name)
        dialog = self.page.locator("role=dialog")

        # Count checked using is_checked()
        all_checkboxes = dialog.locator("input.chakra-checkbox__input").all()
        checked_count  = sum(1 for cb in all_checkboxes if cb.is_checked())
        logger.info(f"[{employee_name}] currently checked branches: {checked_count}")

        if checked_count >= 2:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
            return None

        # Read all branch p texts in format "Branch (Company)"
        all_branch_ps = dialog.locator(
            "xpath=.//p[../../label[contains(@class,'chakra-checkbox')]]"
        ).all()

        for p_elem in all_branch_ps:
            branch_text = p_elem.inner_text().strip()
            if not branch_text or "(" not in branch_text:
                continue
            cb = dialog.locator(
                f"xpath=.//p[normalize-space(.)='{branch_text}']"
                f"/../../label//input[@type='checkbox']"
            ).first
            try:
                if not cb.is_checked():
                    # Close drawer and use select_branch which searches by branch(company)
                    self.page.keyboard.press("Escape")
                    self.page.wait_for_timeout(500)
                    self.edit_employee_hierarchy(employee_name)
                    self.select_branch(branch_text, checked=True)
                    self.click_update()
                    self.wait_for_toast_success()
                    logger.info(f"[{employee_name}] Added extra branch: '{branch_text}'")
                    return branch_text
            except Exception:
                continue

        logger.info(f"[{employee_name}] Could not find unchecked branch to add")
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)
        return None

    def click_update(self):
        logger.info("Clicking Update button")
        self.page.get_by_role("button", name="Update").click()

    def wait_for_reassignment_dialog(self):
        self.page.get_by_role("alertdialog").wait_for(state="visible", timeout=10000)
        logger.info("Reassignment alertdialog visible")

    def wait_for_toast_success(self) -> str:
        toast = self.page.locator("[role='status'], [role='alert'], .chakra-toast").first
        toast.wait_for(state="visible", timeout=8000)
        toast_text = toast.inner_text().strip()
        logger.info(f"toast → '{toast_text}'")
        return toast_text

    def navigate_page(self, page_number: int):
        logger.info(f"Navigating to page {page_number}")
        self.page.get_by_label(f"Page {page_number}").click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def reassign_team_lead(self) -> str:
        """
        Opens the reassign picker in the alertdialog, grabs the first visible
        option name, selects it via ArrowDown+Enter, and returns the name.
        """
        logger.info("Reassigning hierarchy — picking first available option")
        picker = (
            self.page.get_by_role("alertdialog")
            .get_by_text("Reassign new", exact=False)
            .locator("xpath=following::input[1]")
        )
        picker.wait_for(state="visible", timeout=8000)
        picker.click()
        self.page.wait_for_timeout(1000)

        first_option = self.page.locator("div.css-cgv19m").locator("div").nth(0)
        first_option.wait_for(state="visible", timeout=5000)
        selected_name = first_option.inner_text().strip().split("\n")[0].strip()

        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(500)
        logger.info(f"Selected replacement: '{selected_name}'")
        return selected_name

    def click_confirm_and_save(self):
        logger.info("Clicking Confirm & Save")
        self.page.get_by_role("button", name="Confirm & Save").click()

    def get_modal_reassignment_details(self) -> dict:
        modal = self.page.get_by_role("alertdialog")
        modal_text = modal.inner_text().strip()
        logger.info(f"Reassignment Modal:\n{modal_text}")

        result = {"raw_text": modal_text}

        branch_count_match = re.search(r"Confirm hierarchy removal\s*\((\d+)\s*branch", modal_text)
        if branch_count_match:
            result["count"] = int(branch_count_match.group(1))

        name_role_match = re.search(
            r"([A-Za-z\s\-]+?)\s+is\s+(Team Lead|Manager)\s+for\s+(\d+)",
            modal_text
        )
        if name_role_match:
            result["employee_name"] = name_role_match.group(1).strip()
            result["role"]          = name_role_match.group(2).strip()
            if "count" not in result:
                result["count"] = int(name_role_match.group(3))

        return result

