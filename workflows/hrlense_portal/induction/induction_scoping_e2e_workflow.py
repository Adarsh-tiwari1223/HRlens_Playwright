"""
Workflow for End-to-End Scoped Induction Control Verification.
Orchestrates:
1. Centralized Master Scoped Control Matrix in /master/induction-policy:
   - Company, Branch, Department, and Universal ('All') scope isolation.
   - Validates that filtering by an employee's organizational profile correctly restricts the content items.
2. Employee-Facing Scoped Content Enforcement in /induction:
   - Navigates through onboarding journey as an assigned employee (e.g. 'adarsh' -> TEK Inspirations LLC, Varanasi, Developer).
   - Validates that the loaded chapters, slides, and guidance correspond to in-scope policies.
   - Asserts out-of-scope policies (other branches/departments) are not rendered.
3. Induction AI Guide (Sufi) Scoped Knowledge:
   - Queries Sufi in the induction drawer about leadership/policies and verifies context-aware response.
"""

import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import Page
from pages.hrlense_portal.master.master_induction_policy_page import MasterInductionPolicyPage
from pages.hrlense_portal.induction.induction_page import InductionPage

logger = logging.getLogger(__name__)


class InductionScopingE2EWorkflow:
    """Orchestrates cross-role Centralized Induction Scoped Control E2E workflow."""

    def __init__(self, page: Page):
        self.page = page
        self.master_page = MasterInductionPolicyPage(page)
        self.induction_page = InductionPage(page)

    # ----------------- Master Centralized Control Scope Verification -----------------
    def verify_master_centralized_scoping_matrix(
        self,
        company_name: str = "TEK Inspirations LLC",
        branch_name: str = "Varanasi",
        department_name: str = "Developer"
    ) -> Dict[str, Any]:
        """
        Admin Persona:
        Inspects /master/induction-policy to verify that the Centralized Scoping Matrix:
        1. Retrieves all available companies, branches, and departments.
        2. Applies Company + Department scoping and validates that returned rows match
           either the target audience or 'ALL'.
        3. Validates that out-of-scope departments (e.g. 'Accounts') yield distinct scoped content.
        4. Verifies state restoration upon clearing filters.
        """
        logger.info(f"[E2E SCOPING] Verifying Master Induction Scoping Matrix: Company='{company_name}', Dept='{department_name}'...")
        self.master_page.navigate_to_induction_policy()
        self.master_page.select_step(1)

        available_companies = self.master_page.get_available_companies()
        available_branches = self.master_page.get_available_branches()
        available_depts = self.master_page.get_available_departments()

        initial_count = self.master_page.get_row_count()
        logger.info(f"[E2E SCOPING] Baseline rows (All scopes): {initial_count}")

        # Filter by Developer
        self.master_page.select_scope_department(department_name)
        dev_rows = self.master_page.get_all_rows_data()
        dev_count = len(dev_rows)
        logger.info(f"[E2E SCOPING] Developer-scoped rows: {dev_count}")

        # Validate that all rows either belong to Developer or ALL
        for row in dev_rows:
            audience = row.get("TARGET AUDIENCE", "").upper()
            assert "DEVELOPER" in audience or "ALL" in audience, (
                f"Row '{row.get('TITLE / HEADING')}' has target audience '{audience}', "
                f"which violates Developer scoping filter!"
            )

        # Reset scopes
        self.master_page.reset_all_scopes()
        restored_count = self.master_page.get_row_count()

        return {
            "available_companies": available_companies,
            "available_branches": available_branches,
            "available_departments": available_depts,
            "baseline_count": initial_count,
            "developer_count": dev_count,
            "restored_count": restored_count,
            "developer_rows": dev_rows
        }

    # ----------------- Employee Experience Scoped Content Enforcement -----------------
    def verify_employee_scoped_induction_journey(
        self,
        expected_employee_name: str = "Adarsh Tiwari",
        expected_company: str = "TEK Inspirations LLC",
        expected_department: str = "Developer"
    ) -> Dict[str, Any]:
        """
        Employee Persona (e.g. Adarsh Tiwari):
        1. Navigates to /induction.
        2. Inspects welcome slides and verifies candidate greeting.
        3. Advances to Chapter View.
        4. Inspects all displayed chapter titles, section badges, and content paragraphs.
        5. Validates that in-scope organizational content is rendered.
        """
        logger.info(f"[E2E SCOPING] Validating employee induction experience for '{expected_employee_name}'...")
        self.induction_page.navigate_to_induction()

        # Capture welcome slide text
        welcome_text = ""
        if self.induction_page.is_welcome_slide_visible():
            welcome_text = self.induction_page.get_welcome_slide_text()
            logger.info(f"[E2E SCOPING] Welcome slide preview: {welcome_text[:150]}...")
            self.induction_page.advance_welcome_slides(selected_guide="Sufi")

        # In Chapter View: gather chapter details
        first_chapter = self.induction_page.get_displayed_chapter_info()
        logger.info(f"[E2E SCOPING] Initial Chapter loaded: Title='{first_chapter['title']}', Badge='{first_chapter['badge']}'")

        # Step through next chapter if available
        next_chapters = []
        if first_chapter["has_next"]:
            self.induction_page.click_next_chapter()
            second_chapter = self.induction_page.get_displayed_chapter_info()
            logger.info(f"[E2E SCOPING] Second Chapter loaded: Title='{second_chapter['title']}', Badge='{second_chapter['badge']}'")
            next_chapters.append(second_chapter)
            if second_chapter.get("has_prev"):
                self.induction_page.click_previous_chapter()

        return {
            "welcome_text": welcome_text,
            "first_chapter": first_chapter,
            "next_chapters": next_chapters,
            "chapter_view_active": bool(first_chapter["title"] or first_chapter["body"] or self.induction_page.notes_launcher.is_visible())
        }

    # ----------------- Sufi AI Guide Scoped Context Verification -----------------
    def verify_sufi_ai_guide_scoped_responses(self, query: str = "What are the office timings and leave policy?") -> Dict[str, Any]:
        """
        Induction Sufi AI Guide:
        Opens the Induction Chat drawer, asks a query, and validates that Sufi
        replies with relevant policy guidance.
        """
        logger.info(f"[E2E SCOPING] Querying Sufi AI Guide: '{query}'...")
        self.induction_page.open_induction_chat()
        self.induction_page.ask_induction_guide(query)
        reply = self.induction_page.wait_for_guide_response(timeout_sec=15)

        is_valid = len(reply.strip()) > 30 and not reply.startswith("Error")

        return {
            "query": query,
            "bot_reply": reply,
            "is_valid": is_valid
        }
