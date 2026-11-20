"""
Workflow for Employee Induction Module Experience.
Orchestrates:
- Welcome slides completion and AI Guide selection (Sufi / Aarav / Mira)
- Interactive Chapter progression and navigation
- Induction Notepad note-taking, saved state verification, and .txt export
- Induction-Specific AI Chatbot query handling (Sufi guide responses)
"""

import os
import logging
from typing import Dict, Any, Optional
from playwright.sync_api import Page
from pages.hrlense_portal.induction.induction_page import InductionPage

logger = logging.getLogger(__name__)


class InductionWorkflow:
    """Orchestrates Employee Induction business processes and validations."""

    def __init__(self, page: Page):
        self.page = page
        self.induction_page = InductionPage(page)

    def complete_welcome_journey_workflow(self, guide_name: str = "Sufi") -> Dict[str, Any]:
        """
        Completes the initial 7-slide onboarding journey, selects the preferred AI guide,
        and transitions the user into the interactive Chapter View.
        """
        logger.info(f"[WORKFLOW] Starting Induction Welcome Journey (Guide: {guide_name})...")
        self.induction_page.navigate_to_induction()

        if self.induction_page.is_welcome_slide_visible():
            self.induction_page.advance_welcome_slides(selected_guide=guide_name)

        # Confirm chapter view reached
        is_chapter_view = (
            self.induction_page.notes_launcher.is_visible() or
            self.induction_page.chat_launcher.is_visible() or
            self.induction_page.chapter_next_button.is_visible()
        )
        logger.info(f"[WORKFLOW] Chapter view reached: {is_chapter_view}")
        return {
            "success": is_chapter_view,
            "url": self.page.url,
            "guide": guide_name
        }

    def add_and_export_notes_workflow(self, note_text: str) -> Dict[str, Any]:
        """
        Induction Notepad Workflow:
        1. Ensures user is inside Chapter View.
        2. Opens Notepad drawer.
        3. Adds the specified note text and submits.
        4. Triggers 'Export (.txt)' download.
        5. Reads the downloaded file on disk to verify data integrity.
        """
        logger.info(f"[WORKFLOW] Executing Notepad Add & Export for: '{note_text[:50]}...'")
        self.complete_welcome_journey_workflow()

        # Add note
        self.induction_page.add_note(note_text)

        # Export notes
        downloaded_file = self.induction_page.export_notes()
        assert os.path.exists(downloaded_file), f"Exported notes file not found at: {downloaded_file}"

        with open(downloaded_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        logger.info(f"[WORKFLOW] Note verification: file size = {len(file_content)} bytes")
        note_found_in_file = note_text in file_content

        return {
            "file_path": downloaded_file,
            "file_size": len(file_content),
            "note_persisted": note_found_in_file,
            "content_preview": file_content[:200]
        }

    def ask_induction_guide_workflow(self, question: Optional[str] = None, chip_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Induction-Specific AI Guide (Sufi) Workflow:
        1. Ensures user is inside Chapter View.
        2. Opens Induction Chatbot drawer.
        3. Either clicks a predefined chip (e.g. 'Leave Policy') or submits a custom question.
        4. Waits for AI response and returns it.
        """
        logger.info("[WORKFLOW] Interacting with Induction AI Guide (Sufi)...")
        self.complete_welcome_journey_workflow()

        if chip_name:
            logger.info(f"[WORKFLOW] Clicking chip: '{chip_name}'")
            self.induction_page.click_chat_chip(chip_name)
            query_used = chip_name
        elif question:
            logger.info(f"[WORKFLOW] Submitting question: '{question}'")
            self.induction_page.ask_induction_guide(question)
            query_used = question
        else:
            query_used = "Leave Policy"
            self.induction_page.click_chat_chip("Leave Policy")

        bot_reply = self.induction_page.wait_for_guide_response(timeout_sec=15)
        return {
            "query": query_used,
            "bot_reply": bot_reply,
            "is_valid_reply": len(bot_reply.strip()) > 0 and "typing" not in bot_reply.lower()
        }
