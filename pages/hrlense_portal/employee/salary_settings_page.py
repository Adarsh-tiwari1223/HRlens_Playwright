from pages.base_page import BasePage


class SalarySettingsPage(BasePage):

    TOAST           = "div[id^='toast-'][id*='-title']"
    PF_TOGGLE_INPUT = "input[type='checkbox'][aria-label='Include PF']"
    ESIC_TOGGLE_INPUT = "input[type='checkbox'][aria-label='Include ESIC']"

    # ── Step 1: Navigate to employee and grab company / branch / department ───

    def navigate_to_employee(self, employee_name: str) -> dict:
        """Navigate to employee profile and return company/branch/department."""
        from core.config import settings
        self.page.goto(f"{settings.BASE_URL}/employees")
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        # Search for employee to handle pagination
        search = self.page.locator("input[placeholder*='Search employee name'], input[placeholder*='Search']").first
        if search.is_visible():
            search.fill(employee_name)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(2000)

        # Locate employee card/link
        emp_link = self.page.locator(f"p.chakra-text:has-text('{employee_name}')").first
        if not emp_link.is_visible():
            emp_link = self.page.get_by_text(employee_name).first
        emp_link.wait_for(state="visible", timeout=15000)
        emp_link.click()
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        company = ""
        branch = ""
        department = ""
        try:
            company_el = self.page.locator("//p[normalize-space()='Company']/following-sibling::p[1]").first
            if company_el.is_visible():
                company = company_el.inner_text().strip()
            branch_el = self.page.locator("//p[normalize-space()='Branch']/following-sibling::p[1]").first
            if branch_el.is_visible():
                branch = branch_el.inner_text().strip()
            dept_el = self.page.locator("//p[normalize-space()='Department']/following-sibling::p[1]").first
            if dept_el.is_visible():
                department = dept_el.inner_text().strip()
        except Exception:
            pass

        return {"company": company, "branch": branch, "department": department}

    # ── Step 2: Navigate to salary calc settings and read threshold values ────

    def navigate_to_salary_calc_settings(self) -> None:
        """Navigates directly to /salary-calculation-setting."""
        from core.config import settings
        target_url = f"{settings.BASE_URL}/salary-calculation-setting"
        self.page.goto(target_url)
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        # Ensure table rows with actual data are loaded
        self.page.locator("table tbody tr td").first.wait_for(state="visible", timeout=15000)
        self.page.wait_for_timeout(1000)

    def filter_by_employment_type(self, condition: str = "Contains", value: str = "Employee") -> None:
        """
        Filters table by Employment Type using generic BasePage table header filter.
        """
        self.filter_custom_table_column("Employment Type", value, condition=condition)


    def get_all_visible_employment_types(self) -> list:
        """Reads the 'Employment Type' column value from all visible table rows."""
        headers = self.page.locator("table thead th").all_inner_texts()
        idx = next((i for i, h in enumerate(headers) if "employment type" in h.lower()), None)
        if idx is None:
            return []
        rows = self.page.locator("table tbody tr").all()
        types = []
        for r in rows:
            cells = r.locator("td")
            if cells.count() > idx:
                types.append(cells.nth(idx).inner_text().strip())
        return types

    def get_employee_employment_type(self) -> str:
        """Reads 'Employment Type' value from the employee profile 'Employer Details' tab."""
        tab = self.page.get_by_role("tab", name="Employer Details")
        if not tab.is_visible():
            tab = self.page.locator("//button[@role='tab' and contains(., 'Employer')]").first
        if tab.is_visible():
            tab.click()
            self.page.wait_for_timeout(500)
        emp_type_el = self.page.locator("//p[normalize-space()='Employment Type']/following-sibling::p[1]").first
        if not emp_type_el.is_visible():
            emp_type_el = self.page.locator("p:has-text('Employment Type') + p").first
        if emp_type_el.is_visible():
            return emp_type_el.inner_text().strip()
        return ""

    def get_setting_row(self, company: str = "", branch: str = "", department: str = ""):
        """Returns locator for table row matching company/branch/department, prioritizing regular EMPLOYEE rows."""
        # 1. Exact match with EMPLOYEE filter
        if company and branch and department:
            row_xpath = f"//tr[td[contains(normalize-space(),'{company}')] and td[contains(normalize-space(),'{branch}')] and td[contains(normalize-space(),'{department}')] and td[contains(normalize-space(),'Employee') or contains(normalize-space(),'EMPLOYEE')]]"
            row = self.page.locator(row_xpath).first
            if row.count() > 0:
                return row
            row_xpath = f"//tr[td[contains(normalize-space(),'{company}')] and td[contains(normalize-space(),'{branch}')] and td[contains(normalize-space(),'{department}')]]"
            row = self.page.locator(row_xpath).first
            if row.count() > 0:
                return row
        if company and branch:
            row_xpath = f"//tr[td[contains(normalize-space(),'{company}')] and td[contains(normalize-space(),'{branch}')] and (td[contains(normalize-space(),'Employee')] or td[contains(normalize-space(),'EMPLOYEE')])]"
            row = self.page.locator(row_xpath).first
            if row.count() > 0:
                return row
        if company:
            row_xpath = f"//tr[td[contains(normalize-space(),'{company}')] and (td[contains(normalize-space(),'Employee')] or td[contains(normalize-space(),'EMPLOYEE')])]"
            row = self.page.locator(row_xpath).first
            if row.count() > 0:
                return row
        # Fallback: first row that is an Employee (not Intern)
        emp_row = self.page.locator("//table/tbody/tr[td[contains(normalize-space(),'Employee') or contains(normalize-space(),'EMPLOYEE')]]").first
        if emp_row.count() > 0:
            return emp_row
        return self.page.locator("table tbody tr").first


    def get_table_esic_required_value(self, company: str = "", branch: str = "", department: str = "") -> str:
        """Reads YES/NO from the 'ESIC Required' column for the given company/branch/department (or first row)."""
        row = self.get_setting_row(company, branch, department)
        row.first.wait_for(state="visible", timeout=10000)
        try:
            row.first.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass

        # Dynamically locate the column index for 'ESIC Required' from thead headers
        headers = self.page.locator("table thead th").all_inner_texts()
        idx = next((i for i, h in enumerate(headers) if "esic required" in h.lower()), None)
        if idx is not None:
            cell = row.locator("td").nth(idx)
            return cell.inner_text().strip()

        # Fallback: search row cells directly for YES / NO
        cells = row.locator("td").all_inner_texts()
        yn = [c.strip() for c in cells if c.strip().upper() in ["YES", "NO"]]
        return yn[0] if yn else ""


    def open_setting_edit_drawer(self, company: str = "", branch: str = "", department: str = "") -> None:
        """Locates row and clicks Edit button to open the Edit Salary Calculation Setting drawer."""
        row = self.get_setting_row(company, branch, department)
        row.first.wait_for(state="visible", timeout=10000)
        try:
            row.first.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        edit_btn = row.locator("button[aria-label='Edit']").first
        if edit_btn.is_visible():
            edit_btn.click()
        else:
            row.locator("//p[normalize-space()='Edit']").click()
        self.page.locator("header:has-text('Edit Salary Calculation Setting')").wait_for(state="visible", timeout=10000)


    def is_setting_esic_required_checked(self) -> bool:
        """Returns True if 'Is ESIC Required' checkbox in the drawer is checked."""
        cb_container = self.page.locator("//label[normalize-space()='Is ESIC Required']/following-sibling::label[contains(@class,'chakra-checkbox')]")
        return cb_container.get_attribute("data-checked") is not None or cb_container.locator("input").is_checked()

    def toggle_setting_esic_required(self) -> None:
        """Clicks the 'Is ESIC Required' checkbox in the drawer."""
        cb = self.page.locator("//label[normalize-space()='Is ESIC Required']/following-sibling::label[contains(@class,'chakra-checkbox')]")
        cb.click()

    def set_setting_esic_wage_limit(self, amount: str) -> None:
        """Fills ESIC Wage Limit in the drawer."""
        field = self.page.locator("input[name='eSIC_Wage_Limit']")
        field.click()
        field.fill(amount)

    def set_setting_esic_percentages(self, emp_pct: str, empr_pct: str) -> None:
        """Fills ESIC Employee and Employer percentages in the drawer."""
        f_emp = self.page.locator("input[name='eSIC_Employee_Percentage']")
        f_emp.click()
        f_emp.fill(emp_pct)

        f_empr = self.page.locator("input[name='eSIC_Employer_Percentage']")
        f_empr.click()
        f_empr.fill(empr_pct)

    def save_setting_edit(self) -> None:
        """Clicks 'Update' in the drawer to save changes."""
        self.page.locator("button[type='submit']:has-text('Update')").click()
        self.page.wait_for_load_state("domcontentloaded")


    def read_salary_settings(self, company: str, branch: str, department: str = "") -> dict:
        """Select the matching company+branch+department row and read pf_threshold and percentages."""
        dept_condition = f" and td[normalize-space()='{department}']" if department else ""
        row_xpath = f"//tr[td[normalize-space()='{company}'] and td[normalize-space()='{branch}']{dept_condition}]"
        row = self.page.locator(row_xpath).first
        row.scroll_into_view_if_needed()
        row.hover()
        self.page.locator(f"{row_xpath}//p[normalize-space()='Edit']").click()
        self.page.wait_for_load_state("domcontentloaded")

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
        self.page.wait_for_load_state("domcontentloaded")
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
        tab = self.page.get_by_role("tab", name="Employer Details")
        if not tab.is_visible():
            tab = self.page.locator("//button[@role='tab' and contains(., 'Employer')]").first
        tab.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

        # Precise locator from user HTML: div with Salary paragraph containing the Edit button
        edit_btn = self.page.locator("//div[div/p[normalize-space()='Salary']]//button[@aria-label='Edit']").first
        if not edit_btn.is_visible():
            edit_btn = self.page.locator("div:has(p:has-text('Salary')) button[aria-label='Edit']").first
        if not edit_btn.is_visible():
            edit_btn = self.page.get_by_label("Edit").nth(4)

        edit_btn.wait_for(state="visible", timeout=10000)
        edit_btn.click()
        self.page.wait_for_load_state("domcontentloaded")

    def set_gross_salary(self, amount: str) -> None:
        field = self.page.get_by_label("Gross Salary Per Month")
        field.wait_for(state="visible")
        field.click()
        field.fill(amount)
        field.press("Tab")
        self.page.wait_for_timeout(600)

    def submit_salary_update(self) -> None:
        self.page.get_by_role("button", name="Update Details").click()

    # ── Step 4: Confirm popup that appears when gross < min_basic ────────────

    def confirm_dialog(self) -> None:
        """Confirm the popup — only appears when gross salary < min basic."""
        self.page.get_by_role("button", name="Confirm").wait_for(state="visible")
        self.page.get_by_role("button", name="Confirm").click()
        self.page.wait_for_load_state("domcontentloaded")

    def confirm_dialog_if_present(self) -> None:
        """Confirm only if the popup appeared (e.g. salary above min basic — no popup)."""
        confirm = self.page.get_by_role("button", name="Confirm")
        if confirm.is_visible():
            confirm.click()
            self.page.wait_for_load_state("domcontentloaded")

    # ── PF toggle state ───────────────────────────────────────────────────────

    def toggle_include_pf(self) -> None:
        self.page.locator("label").filter(has_text="Include PF").click()

    def is_pf_toggle_disabled(self) -> bool:
        return self.page.locator(self.PF_TOGGLE_INPUT).is_disabled()

    def is_pf_toggle_checked(self) -> bool:
        return self.page.locator(self.PF_TOGGLE_INPUT).is_checked()

    # ── ESIC toggle state ──────────────────────────────────────────────────────

    def is_esic_toggle_visible(self, timeout_ms: int = 5000) -> bool:
        """Returns True if 'Include ESIC' label/checkbox is visible in the modal within timeout."""
        loc = self.page.locator("span.chakra-checkbox__label:has-text('Include ESIC'), span:has-text('Include ESIC'), label:has-text('Include ESIC')").first
        try:
            loc.wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:
            return False

    def is_esic_toggle_checked(self) -> bool:
        """Returns True if 'Include ESIC' checkbox is checked."""
        # 1. Check parent label data-checked attribute
        container = self.page.locator("label.chakra-checkbox:has(span:has-text('Include ESIC'))").first
        if container.count() > 0:
            return container.get_attribute("data-checked") is not None
        # 2. Check input element
        cb = self.page.locator("label:has(span:has-text('Include ESIC')) input[type='checkbox'], input[aria-label='Include ESIC']").first
        if cb.count() > 0:
            return cb.is_checked()
        return False

    def toggle_include_esic(self) -> None:
        """Clicks 'Include ESIC' checkbox/label to toggle state."""
        loc = self.page.locator("span.chakra-checkbox__label:has-text('Include ESIC'), span:has-text('Include ESIC'), label:has-text('Include ESIC')").first
        loc.wait_for(state="visible", timeout=5000)
        loc.click()

    def get_modal_field_value(self, label_text: str) -> str:
        """Reads input value for a given field label inside the active modal."""
        field = self.page.get_by_label(label_text, exact=False).first
        if field.is_visible():
            return field.input_value().strip()
        # Fallback to xpath by label text
        loc = self.page.locator(f"//label[contains(normalize-space(),'{label_text}')]/following::input[1]")
        if loc.is_visible():
            return loc.input_value().strip()
        return ""

    def get_toast(self) -> str:
        return self.wait_for_toast(self.TOAST)

