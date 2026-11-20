"""
Workflow for Department-Specific Induction Policy Editing & Live Reflection Verification.
Orchestrates:
1. Admin Persona: Inspects and edits department policy content in /master/induction-policy (STEP 4: Department).
2. Employee Persona: Navigates to /induction, traverses welcome slides & chapters, and verifies that the modified content reflects live.
3. Rollback: Restores the original content in /master/induction-policy to ensure data safety.
"""

import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import Page
from pages.hrlense_portal.master.master_induction_policy_page import MasterInductionPolicyPage
from pages.hrlense_portal.induction.induction_page import InductionPage

logger = logging.getLogger(__name__)


class InductionDepartmentWorkflow:
    """Orchestrates Phase 1: Department policy editing in Master and reflection on /induction."""

    def __init__(self, master_page: Page, induction_page: Optional[Page] = None):
        self.master_page = master_page
        self.policy_page = MasterInductionPolicyPage(master_page)
        self.emp_page = induction_page
        self.emp_induction_page = InductionPage(induction_page) if induction_page else None

    def get_all_department_policies(self) -> List[Dict[str, Any]]:
        """
        Navigates to /master/induction-policy and selects STEP 4: Department.
        Extracts all department policy items from the content table.
        """
        logger.info("[WORKFLOW] Navigating to Master Induction Policy -> STEP 4: Department...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(4)
        self.master_page.wait_for_timeout(1000)

        rows_data = self.policy_page.get_all_rows_data()
        logger.info(f"[WORKFLOW] Retrieved {len(rows_data)} Department Policy items in Step 4.")
        return rows_data

    def edit_department_content(
        self,
        row_index: int = 0,
        test_marker: str = "[Verified Reflection 2026]"
    ) -> Dict[str, Any]:
        """
        Opens the Edit drawer for the specified department row, captures original values,
        appends the test verification marker, and saves the changes.
        """
        logger.info(f"[WORKFLOW] Editing Department policy row {row_index} with test marker: '{test_marker}'...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(4)
        self.master_page.wait_for_timeout(1000)

        # Click edit
        self.policy_page.click_edit_row(row_index)

        original_title = self.policy_page.get_modal_title_value()
        original_content = self.policy_page.get_modal_content_value()
        logger.info(f"[WORKFLOW] Original Title: '{original_title}'")
        logger.info(f"[WORKFLOW] Original Content (first 100 chars): '{original_content[:100]}...'")

        # Create updated content with identifiable marker
        updated_content = f"{original_content} {test_marker}".strip()
        self.policy_page.modal_content_textarea.fill(updated_content)
        self.master_page.wait_for_timeout(400)

        # Save changes
        self.policy_page.save_modal_changes()
        logger.info(f"[WORKFLOW] Saved modified content for row {row_index}.")

        return {
            "row_index": row_index,
            "original_title": original_title,
            "original_content": original_content,
            "updated_content": updated_content,
            "test_marker": test_marker
        }

    def verify_content_reflection_on_induction(
        self,
        test_marker: str,
        employee_page: Optional[Page] = None
    ) -> Dict[str, Any]:
        """
        Navigates through the employee /induction experience (welcome slides and chapters)
        and verifies whether the test marker is rendered live on screen.
        """
        active_emp_page = employee_page or self.emp_page
        assert active_emp_page is not None, "Employee Page instance is required for reflection verification!"

        induction_page = InductionPage(active_emp_page)
        logger.info(f"[WORKFLOW] Navigating employee to /induction to verify marker: '{test_marker}'...")
        induction_page.navigate_to_induction()

        found_in_slide = False
        found_in_chapter = False
        matched_location = None
        matched_text = ""

        # 1. Check in Welcome Slides
        logger.info("[WORKFLOW] Checking Welcome Slides for reflected content...")
        slides = induction_page.get_all_welcome_slides_text(selected_guide="Sufi")
        for idx, slide_text in enumerate(slides, start=1):
            if test_marker in slide_text:
                found_in_slide = True
                matched_location = f"Welcome Slide {idx}"
                matched_text = slide_text
                logger.info(f"[WORKFLOW] Test marker REFLECTED in {matched_location}!")
                break

        # 2. Check in Interactive Chapters
        if not found_in_slide:
            logger.info("[WORKFLOW] Checking Interactive Chapters for reflected content...")
            chapters = induction_page.get_all_chapters_content()
            for ch in chapters:
                combined_chapter_text = f"{ch['title']} {ch['badge']} {ch['body']}"
                if test_marker in combined_chapter_text:
                    found_in_chapter = True
                    matched_location = f"Chapter: {ch['title']}"
                    matched_text = ch["body"]
                    logger.info(f"[WORKFLOW] Test marker REFLECTED in {matched_location}!")
                    break

        # 3. Check in /api/Induction/me payload
        found_in_api = False
        api_payload = active_emp_page.evaluate("""async () => {
            try {
                const loginData = JSON.parse(sessionStorage.getItem('loginData') || '{}');
                const token = loginData.token;
                const res = await fetch('https://audit.jobvritta.com/api/Induction/me', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                return await res.json();
            } catch(e) {
                return null;
            }
        }""")

        if api_payload and "sections" in api_payload:
            import json
            dept_sec = next((s for s in api_payload["sections"] if s.get("key") == "department"), None)
            if dept_sec:
                dept_text = json.dumps(dept_sec)
                if test_marker in dept_text:
                    found_in_api = True
                    logger.info("[WORKFLOW] Test marker REFLECTED in /api/Induction/me (Department Section)!")
                    if not matched_location:
                        matched_location = "/api/Induction/me (Department Section)"
                        matched_text = dept_sec.get("intro", "")

        is_reflected = found_in_slide or found_in_chapter or found_in_api
        logger.info(f"[WORKFLOW] Reflection Outcome: {is_reflected} | Location: {matched_location}")

        return {
            "reflected": is_reflected,
            "found_in_slide": found_in_slide,
            "found_in_chapter": found_in_chapter,
            "found_in_api": found_in_api,
            "matched_location": matched_location,
            "matched_text": matched_text[:200] if matched_text else "",
            "total_slides_checked": len(slides)
        }

    def revert_department_content(
        self,
        row_index: int,
        original_title: str,
        original_content: str
    ):
        """
        Reverts the department content back to its original title and content.
        Guarantees non-destructive rollback of test mutations.
        """
        logger.info(f"[WORKFLOW] Reverting department row {row_index} back to pristine state...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(4)
        self.master_page.wait_for_timeout(1000)

        self.policy_page.click_edit_row(row_index)
        if original_title:
            self.policy_page.modal_title_input.fill(original_title)
        self.policy_page.modal_content_textarea.fill(original_content)
        self.master_page.wait_for_timeout(400)

        self.policy_page.save_modal_changes()
        logger.info(f"[WORKFLOW] Successfully reverted department row {row_index} back to original text.")
