"""
Director Module Workflow Layer for HR Lens Portal (Under Masters).
Follows 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Encapsulates complete business workflows for Phases 1-4.
"""

import random
import re
from playwright.sync_api import Page
from pages.hrlense_portal.master.director_page import DirectorPage
from pages.hrlense_portal.master.director_documents_page import DirectorDocumentsPage
from testdata.dynamic.business_test_data import BusinessTestData
from utils.logger import log_step


class DirectorWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.director_page = DirectorPage(page)
        self.director_docs_page = DirectorDocumentsPage(page)

    def refresh_page(self):
        """Reloads page to ensure UI state is clean and never freezes between test steps."""
        try:
            self.page.reload()
            self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass

    def get_api_director_employees(self) -> list[str]:
        """Fetch all employees having the Director role from backend API cache or master list."""
        try:
            emps = BusinessTestData.get_employees_by_department()
            names = []
            for emp in emps:
                fn = emp.get("fullName") or f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip()
                if fn and fn not in names:
                    names.append(fn)
            if names:
                return names
        except Exception:
            pass

        return [
            "Gopal Sharma", "Brij Rawat", "Davesh Sharma", "Sanjeev Rohatgi",
            "Arvind Kumar", "Vivek Singh", "Gagan Pradhan", "Hemant Nayak", "Awadhesh Kumar Pandey"
        ]

    def get_unassigned_director(self) -> str | None:
        """
        Phase 1: Candidate Discovery
        - Candidate Discovery: Read all assigned Directors from grid into existing_directors.
        - API Validation: Fetch all employees having Director role from API into director_candidates.
        - Comparison: Compare API list with grid records to identify unassigned Directors.
        - Decision: Return target_director or None.
        """
        self.director_page.navigate_to_directors()
        existing_set = {name.strip().upper() for name in self.director_page.get_existing_director_names() if name.strip()}

        # API Validation
        director_candidates = self.get_api_director_employees()

        # Comparison (Case-insensitive)
        available_candidates = [c for c in director_candidates if c.strip().upper() not in existing_set]

        # Decision
        if available_candidates:
            target_director = available_candidates[0]
            log_step("Candidate Discovery", value=target_director)
            return target_director

        return None

    def get_first_director(self) -> str | None:
        """Retrieves the first Director name from table grid."""
        self.director_page.navigate_to_directors()
        return self.director_page.get_first_director_name()

    def get_dynamic_company_shares(self) -> tuple[dict, dict]:
        """Fetches US & Payroll Companies master lists from API cache and builds 100% dynamic multi-company shares for each run."""
        api_us = BusinessTestData.get_companies()
        api_payroll = BusinessTestData.get_payroll_companies()

        us_names = [c.get("companyName") or c.get("name") for c in api_us if c.get("companyName") or c.get("name")]
        payroll_names = [c.get("payrollCompanyName") or c.get("name") for c in api_payroll if c.get("payrollCompanyName") or c.get("name")]

        # Filter out companies whose cumulative shareholding is already maxed out (>99% assigned in Staging database, e.g. Bivocal)
        clean_us = [n for n in us_names if "bivocal" not in n.lower()]
        clean_payroll = [n for n in payroll_names if "bivocal" not in n.lower()]

        # Randomly sample dynamic US and Payroll companies for each test execution
        selected_us = random.sample(clean_us, min(2, len(clean_us))) if clean_us else ["TEK Inspirations LLC"]
        selected_payroll = random.sample(clean_payroll, min(2, len(clean_payroll))) if clean_payroll else ["ABS Staffing Solutions Pvt."]

        # Dynamic random shareholding percentages (1-3%) for each selected company
        us_shares = {name: random.randint(1, 3) for name in selected_us}
        payroll_shares = {name: random.randint(1, 3) for name in selected_payroll}
        return us_shares, payroll_shares

    def add_director(self, director_name: str, us_shares: dict = None, payroll_shares: dict = None):
        """Phase 1: Multi-Company Assignment & Form Submission."""
        log_step("Open Add Director Dialog")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()
        
        log_step("Fill Director Form", value=director_name)
        self.director_page.fill_director_details(
            director_name=director_name,
            us_company_shares=us_shares,
            payroll_company_shares=payroll_shares
        )
        
        log_step("Submit Director Form")
        self.director_page.click_save()
        self.refresh_page()

    def add_new_director_workflow(self, director_name: str, email: str, phone: str, us_shares: dict = None, payroll_shares: dict = None) -> str:
        """New Flow: Add New Director tab workflow returning toast notification with smart auto-retry."""
        log_step("Open Add Director Dialog")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()
        self.director_page.click_add_new_director_tab()

        log_step("Fill New Director Info", value=f"{director_name} | {email}")
        self.director_page.fill_new_director_info(director_name, email, phone)

        us_count = len(us_shares) if us_shares else 0
        self.director_page.select_us_companies_and_shares(us_shares or {})
        self.director_page.select_payroll_companies_and_shares(payroll_shares or {}, us_count=us_count)

        log_step("Submit New Director Form")
        self.director_page.click_save()
        toast = self.director_page.get_form_error_or_toast()
        log_step("Toast Notification", value=toast)

        # Smart Auto-Retry if toast reports remaining share percentage limit (e.g. 'has only 1.0122% share remaining')
        if toast and ("has only" in toast.lower() or "remaining" in toast.lower()):
            import re
            match = re.search(r"has only ([\d\.]+)%", toast)
            if match and self.director_page.is_modal_open():
                rem_pct = round(float(match.group(1)), 2)
                if rem_pct <= 0:
                    rem_pct = 0.01
                log_step("Auto-Retry with Rounded Remaining Percentage", value=f"{rem_pct}%")
                if us_shares:
                    for k in us_shares:
                        us_shares[k] = rem_pct
                    self.director_page.select_us_companies_and_shares(us_shares)
                if payroll_shares:
                    for k in payroll_shares:
                        payroll_shares[k] = rem_pct
                    self.director_page.select_payroll_companies_and_shares(payroll_shares, us_count=us_count)
                self.director_page.click_save()
                toast = self.director_page.get_form_error_or_toast()

        self.refresh_page()
        return toast

    def verify_director_exists(self, director_name: str) -> bool:
        """Phase 1/2 Verification: Performs search via name and verifies target Director record is present in grid."""
        log_step("Verify Director Grid", value=director_name)
        self.director_page.navigate_to_directors()

        # Perform search via name (handles multi-page pagination)
        self.director_page.search_director(director_name)

        row = self.page.locator("tbody tr").filter(has_text=director_name).first
        is_found = False
        try:
            row.wait_for(state="visible", timeout=6000)
            is_found = row.is_visible()
        except Exception:
            is_found = False

        self.director_page.search_director("")
        return is_found

    def verify_director_exists_api(self, director_name: str) -> bool:
        """API Verification: Verifies newly created director is listed under backend API response."""
        log_step("Verify Director API", value=director_name)
        try:
            from utils.api.director_api import get_directors_api
            records = get_directors_api()
            for r in records:
                name = r.get("fullName") or r.get("directorName") or r.get("name") or f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
                if name and director_name.lower() in name.lower():
                    return True
        except Exception:
            pass
        return False

    def edit_director_workflow(self, director_name: str):
        """Phase 2: Edit Director Workflow."""
        log_step("Open Edit Director Dialog", value=director_name)
        self.director_page.navigate_to_directors()
        self.director_page.edit_director(director_name)

        log_step("Submit Director Form")
        self.director_page.click_save()
        self.refresh_page()

    def validate_blank_form(self) -> dict:
        """Phase 3: Blank Form Validation."""
        log_step("Open Add Director Dialog")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()

        log_step("Submit Blank Form")
        self.director_page.click_save()
        is_open = self.director_page.is_modal_open()
        err_msg = self.director_page.get_form_error_or_toast()
        self.director_page.click_cancel()
        self.refresh_page()
        return {"is_modal_open": is_open, "error": err_msg}

    def validate_duplicate_director(self, existing_director: str) -> dict:
        """Phase 3: Duplicate Director Validation."""
        log_step("Open Add Director Dialog")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()

        log_step("Select Existing Director", value=existing_director)
        self.director_page.fill_director_details(director_name=existing_director)

        log_step("Submit Duplicate Form")
        self.director_page.click_save()
        is_open = self.director_page.is_modal_open()
        err_msg = self.director_page.get_form_error_or_toast()
        self.director_page.click_cancel()
        self.refresh_page()
        return {"is_modal_open": is_open, "error": err_msg}

    def cancel_modal_workflow(self) -> bool:
        """Phase 3: Cancel Workflow."""
        log_step("Open Add Director Dialog")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()

        log_step("Click Cancel Dialog")
        self.director_page.click_cancel()
        is_closed = not self.director_page.is_modal_open()
        self.refresh_page()
        return is_closed

    def validate_cumulative_share_overflow(self, director_name: str) -> dict:
        """Phase 3: Company Share Distribution Validation (>100%)."""
        log_step("Open Add Director Dialog")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()

        log_step("Enter Share Overflow Percentage", value="105%")
        self.director_page.fill_director_details(director_name=director_name, us_company_shares={"Vyze INC": 105})

        log_step("Submit Form")
        self.director_page.click_save()
        is_open = self.director_page.is_modal_open()
        err_msg = self.director_page.get_form_error_or_toast()
        self.director_page.click_cancel()
        self.refresh_page()
        return {"is_modal_open": is_open, "error": err_msg}

    def validate_invalid_share_inputs(self, director_name: str) -> bool:
        """Phase 3: Boundary & Invalid Input Validation (-15%, 'abc')."""
        log_step("Open Add Director Dialog")
        self.director_page.navigate_to_directors()
        self.director_page.click_add_director()

        log_step("Enter Invalid Share Inputs", value="-15%, 'abc'")
        self.director_page.fill_director_details(director_name=director_name, us_company_shares={"Vyze INC": -15})
        self.director_page.click_save()
        is_open1 = self.director_page.is_modal_open()

        self.director_page.fill_director_details(director_name=director_name, us_company_shares={"Vyze INC": "abc"})
        self.director_page.click_save()
        is_open2 = self.director_page.is_modal_open()

        self.director_page.click_cancel()
        self.refresh_page()
        return is_open1 and is_open2

    def search_director_workflow(self, director_name: str) -> str | None:
        """Phase 4: Search Director Test Scenario."""
        log_step("Search Director", value=director_name)
        self.director_page.navigate_to_directors()
        self.director_page.search_director(director_name)
        matched = self.director_page.get_first_director_name()
        self.director_page.search_director("")
        self.refresh_page()
        return matched

    def view_shareholding_tooltip_workflow(self, director_name: str):
        """Phase 4: Shareholding Details Test Scenario."""
        log_step("View Shareholding Tooltip", value=director_name)
        self.director_page.navigate_to_directors()
        self.director_page.click_shareholding_details(director_name)
        self.refresh_page()
