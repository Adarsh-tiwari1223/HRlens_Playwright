from pages.base_page import BasePage


class SalarySettingsPage(BasePage):

    TOAST           = "div[id^='toast-'][id*='-title']"
    PF_TOGGLE_INPUT = "input[type='checkbox'][aria-label='Include PF']"

    # ── Step 1: Navigate to employee and grab company / branch / department ───

    def navigate_to_employee(self, employee_name: str) -> dict:
        """Navigate to employee profile and return company/branch/department."""
        from core.config import settings
        self.page.goto(settings.BASE_URL)
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Employees").click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_text(employee_name).first.click()
        self.page.wait_for_load_state("networkidle")

        company    = self.page.locator("//p[normalize-space()='Company']/following-sibling::p[1]").first.inner_text().strip()
        branch     = self.page.locator("//p[normalize-space()='Branch']/following-sibling::p[1]").first.inner_text().strip()
        department = self.page.locator("//p[normalize-space()='Department']/following-sibling::p[1]").first.inner_text().strip()
        return {"company": company, "branch": branch, "department": department}

    # ── Step 2: Navigate to salary calc settings and read threshold values ────

    def navigate_to_salary_calc_settings(self) -> None:
        from core.config import settings
        self.page.goto(settings.BASE_URL)
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("link", name="Admin Control").click()
        self.page.get_by_role("link", name="• Salary Calculation Setting").click()
        self.page.wait_for_load_state("networkidle")

    def read_salary_settings(self, company: str, branch: str, department: str = "") -> dict:
        """Select the matching company+branch+department row and read pf_threshold and percentages."""
        dept_condition = f" and td[normalize-space()='{department}']" if department else ""
        row_xpath = f"//tr[td[normalize-space()='{company}'] and td[normalize-space()='{branch}']{dept_condition}]"
        row = self.page.locator(row_xpath).first
        row.scroll_into_view_if_needed()
        row.hover()
        self.page.locator(f"{row_xpath}//p[normalize-space()='Edit']").click()
        self.page.wait_for_load_state("networkidle")

        pf_threshold = int(self.page.get_by_placeholder("Enter Minimum basic for pf").input_value().strip())
        basic_pct    = self.page.get_by_placeholder("Enter Basic Percentage").input_value().strip()
        hra_pct      = self.page.get_by_placeholder("Enter HRA Percentage").input_value().strip()
        return {
            "pf_threshold": pf_threshold,
            "basic_pct":    float(basic_pct) if basic_pct else None,
            "hra_pct":      float(hra_pct)   if hra_pct   else None,
        }

    def read_min_basic_from_slab(self, gross_salary: int) -> int | None:
        """Open Salary Slab Rules tab and find the min_basic for the row matching gross_salary."""
        self.page.get_by_role("tab", name="Salary Slab Rules").click()
        self.page.wait_for_load_state("networkidle")
        rows = self.page.locator("table tbody tr").all()
        for row in rows:
            cells = row.locator("td").all_inner_texts()
            if len(cells) >= 3:
                try:
                    from_val  = int(cells[2].replace(",", "").strip() or 0)
                    to_val    = int(cells[3].replace(",", "").strip() or 0)
                    min_basic = int(cells[4].replace(",", "").strip() or 0)
                    if from_val <= gross_salary <= to_val:
                        return min_basic
                except (ValueError, IndexError):
                    continue
        return None

    def set_pf_threshold(self, value: str) -> None:
        field = self.page.get_by_placeholder("Enter Minimum basic for pf")
        field.click()
        field.fill(value)
        self.page.get_by_role("button", name="Update").click()

    def set_hra_percentage(self, value: str) -> None:
        field = self.page.get_by_placeholder("Enter HRA Percentage")
        field.click()
        field.fill(value)
        self.page.get_by_role("button", name="Update").click()

    def add_slab_rule(self, from_val: str, to_val: str, min_basic: str) -> None:
        self.page.get_by_role("button", name="Add Slab Rule").click()
        row = self.page.get_by_role("row", name="Company Branch save")
        row.get_by_placeholder("From").fill(from_val)
        row.get_by_placeholder("To").fill(to_val)
        row.get_by_placeholder("Min Basic").fill(min_basic)
        row.get_by_label("save").click()

    def get_slab_row_count(self) -> int:
        return self.get_count("table tbody tr")

    # ── Step 3: Open salary edit form ────────────────────────────────────────

    def open_salary_edit(self) -> None:
        self.page.get_by_role("tab", name="Employer Details").click()
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_text("Salary", exact=True).click()
        edit_btn = self.page.get_by_label("Edit").nth(4)
        edit_btn.wait_for(state="visible")
        edit_btn.click()

    def set_gross_salary(self, amount: str) -> None:
        field = self.page.get_by_label("Gross Salary Per Month")
        field.wait_for(state="visible")
        field.click()
        field.fill(amount)

    def submit_salary_update(self) -> None:
        self.page.get_by_role("button", name="Update Details").click()

    # ── Step 4: Confirm popup that appears when gross < min_basic ────────────

    def confirm_dialog(self) -> None:
        """Confirm the popup — only appears when gross salary < min basic."""
        self.page.get_by_role("button", name="Confirm").wait_for(state="visible")
        self.page.get_by_role("button", name="Confirm").click()
        self.page.wait_for_load_state("networkidle")

    def confirm_dialog_if_present(self) -> None:
        """Confirm only if the popup appeared (e.g. salary above min basic — no popup)."""
        confirm = self.page.get_by_role("button", name="Confirm")
        if confirm.is_visible():
            confirm.click()
            self.page.wait_for_load_state("networkidle")

    # ── PF toggle state ───────────────────────────────────────────────────────

    def toggle_include_pf(self) -> None:
        self.page.locator("label").filter(has_text="Include PF").click()

    def is_pf_toggle_disabled(self) -> bool:
        return self.page.locator(self.PF_TOGGLE_INPUT).is_disabled()

    def is_pf_toggle_checked(self) -> bool:
        return self.page.locator(self.PF_TOGGLE_INPUT).is_checked()

    def get_toast(self) -> str:
        return self.wait_for_toast(self.TOAST)
