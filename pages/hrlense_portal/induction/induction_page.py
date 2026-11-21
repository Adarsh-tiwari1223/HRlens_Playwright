"""
Page Object for Employee Induction Module.
URL: /induction

Owns:
- Locators for 7-slide onboarding journey:
    Slide 1: Welcome ('Let's Get Started')
    Slides 2-6: Company Profile, People, Department, Sufi Intro, Induction Journey ('Continue' / 'Previous')
    Slide 7: AI Guide Selection ('Sufi', 'Aarav', 'Mira') -> 'Resume Induction' / 'Start Induction'
- Locators for Interactive Chapter Experience:
    Chapter progress bar, Section badges, Next/Previous chapter buttons, Complete induction button
- Locators for Induction Notepad Tool:
    Launcher button (.induction-notes-launcher), Panel (.induction-notes-panel),
    Note composer textarea, '+ Add Note' button, Saved notes pill/counter,
    Export notes ('Export (.txt)')
- Locators for Induction-Specific AI Chatbot (Sufi / Guide):
    Launcher button (.induction-chat-launcher), Panel (.induction-chat-panel),
    Quick chips (Branch Head, Team Lead & Manager, Leave Policy, Office Timings),
    Chat input, Form submit button, Message bubbles
"""

import os
import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Locator, Download
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class InductionPage(BasePage):
    """Page Object for HRlens Employee Induction Experience (/induction)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{settings.BASE_URL}/induction"

        # ----------------- 7-Slide Welcome Journey -----------------
        self.welcome_header = self.page.locator(".welcome-header, h1:has-text('EMPLOYEE INDUCTION')").first
        self.welcome_title = self.page.locator(".welcome-header-title, .welcome-heading-welcome").first
        self.start_journey_button = self.page.locator("button.welcome-cta:has-text(\"Let's Get Started\"), button:has-text(\"Let's Get Started\")").first
        self.continue_slide_button = self.page.locator("button.welcome-cta:has-text('Continue'), button:has-text('Continue')").first
        self.previous_slide_button = self.page.locator("button.welcome-previous-cta:has-text('Previous'), button:has-text('Previous')").first
        self.guide_sufi_button = self.page.locator("button:has-text('Sufi')").first
        self.guide_aarav_button = self.page.locator("button:has-text('Aarav')").first
        self.guide_mira_button = self.page.locator("button:has-text('Mira')").first
        self.resume_induction_button = self.page.locator("button:has-text('Resume Induction'), button:has-text('Start Induction'), button.welcome-cta").first

        # ----------------- Interactive Chapter View -----------------
        self.chapter_progress = self.page.locator("div:has-text('CHAPTER PROGRESS'), div:has-text('% completed')").first
        self.chapter_next_button = self.page.locator("button:has-text('Next')").first
        self.chapter_prev_button = self.page.locator("button:has-text('Previous')").first
        self.complete_induction_button = self.page.locator("button:has-text('Complete induction')").first

        # ----------------- Induction Notepad Tool -----------------
        self.notes_launcher = self.page.locator("button.induction-tools-launcher.induction-notes-launcher").first
        self.notes_panel = self.page.locator(".induction-tool-panel.induction-notes-panel").first
        self.notes_badge = self.page.locator(".induction-notes-section-badge").first
        self.saved_notes_pill = self.page.locator(".induction-notes-video-pill").first
        self.note_textarea = self.page.locator("textarea[placeholder*='Write down key takeaways' i], .induction-notes-panel textarea").first
        self.add_note_button = self.page.locator(".induction-notes-panel button:has-text('+ Add Note'), button:has-text('+ Add Note')").first
        self.export_notes_button = self.page.locator(".induction-notes-panel button:has-text('Export (.txt)'), button:has-text('Export')").first

        # ----------------- Induction-Specific AI Chatbot (Sufi) -----------------
        self.chat_launcher = self.page.locator("button.induction-tools-launcher.induction-chat-launcher").first
        self.chat_panel = self.page.locator(".induction-tool-panel.induction-chat-panel").first
        self.chat_header = self.page.locator(".induction-chat-panel h3, .induction-chat-panel").first
        self.chip_branch_head = self.page.locator(".induction-chat-panel button:has-text('Branch Head')").first
        self.chip_team_lead = self.page.locator(".induction-chat-panel button:has-text('Team Lead & Manager')").first
        self.chip_leave_policy = self.page.locator(".induction-chat-panel button:has-text('Leave Policy')").first
        self.chip_office_timings = self.page.locator(".induction-chat-panel button:has-text('Office Timings')").first
        self.chat_input = self.page.locator(".induction-chat-form input, .induction-chat-panel input[placeholder*='Ask' i]").first
        self.chat_submit_button = self.page.locator(".induction-chat-form button[type='submit'], .induction-chat-panel button[type='submit']").first
        self.chat_messages = self.page.locator(".induction-chat-messages .induction-chat-message")

        # Generic tool panel close button
        self.tool_close_button = self.page.locator("button[aria-label='Close'], button.close-btn, button:has-text('✕')").first

    def navigate_to_induction(self):
        """Navigates to /induction route."""
        logger.info(f"[UI] Navigating to Induction Module: {self.url}")
        self.page.goto(self.url, wait_until="domcontentloaded", timeout=25000)
        self.page.wait_for_timeout(1500)
        if "/induction" not in self.page.url:
            raise RuntimeError(f"Failed to load induction page. Current: {self.page.url}")

    def is_welcome_slide_visible(self) -> bool:
        """Checks if the initial welcome slide is visible."""
        return self.start_journey_button.is_visible()

    def advance_welcome_slides(self, selected_guide: str = "Sufi"):
        """
        Advances through all initial welcome slides and selects the preferred AI guide
        to reach the interactive Chapter View.
        """
        logger.info(f"[UI] Advancing welcome slides (Selected AI Guide: {selected_guide})...")
        for step in range(1, 9):
            if self.start_journey_button.is_visible():
                logger.info("[UI] Step: Clicking \"Let's Get Started\"...")
                self.start_journey_button.click()
                self.page.wait_for_timeout(800)
            elif self.continue_slide_button.is_visible():
                logger.info("[UI] Step: Clicking 'Continue'...")
                self.continue_slide_button.click()
                self.page.wait_for_timeout(800)
            elif self.resume_induction_button.is_visible():
                # Guide selection slide
                if selected_guide.lower() == "aarav" and self.guide_aarav_button.is_visible():
                    self.guide_aarav_button.click()
                elif selected_guide.lower() == "mira" and self.guide_mira_button.is_visible():
                    self.guide_mira_button.click()
                elif self.guide_sufi_button.is_visible():
                    self.guide_sufi_button.click()
                self.page.wait_for_timeout(500)
                logger.info("[UI] Clicking 'Resume / Start Induction'...")
                self.resume_induction_button.click()
                self.page.wait_for_timeout(1500)
                break
            elif self.notes_launcher.is_visible() or self.chat_launcher.is_visible():
                logger.info("[UI] Chapter view reached.")
                break
            else:
                self.page.wait_for_timeout(500)

    # ----------------- Notepad Interactions -----------------
    def open_notepad(self):
        """Opens the Induction Notepad drawer if not already open."""
        if not self.is_notepad_open():
            logger.info("[UI] Opening Induction Notepad drawer...")
            self.notes_launcher.wait_for(state="visible", timeout=7000)
            self.notes_launcher.click()
            self.notes_panel.wait_for(state="visible", timeout=5000)
        else:
            logger.info("[UI] Induction Notepad drawer is already open.")

    def is_notepad_open(self) -> bool:
        """Verifies if the Induction Notepad panel is open."""
        return self.notes_panel.is_visible()

    def add_note(self, text: str):
        """Types a note into the Notepad and clicks '+ Add Note'."""
        self.open_notepad()
        logger.info(f"[UI] Adding note: '{text}'...")
        self.note_textarea.wait_for(state="visible", timeout=5000)
        self.note_textarea.fill(text)
        self.page.wait_for_timeout(400)
        self.add_note_button.wait_for(state="visible", timeout=5000)
        self.add_note_button.click()
        self.page.wait_for_timeout(1200)

    def export_notes(self, save_dir: Optional[str] = None) -> str:
        """
        Clicks 'Export (.txt)' button, captures the downloaded file,
        and saves it to the specified directory (defaults to reports/).
        Returns the absolute path to the downloaded file.
        """
        self.open_notepad()
        target_dir = save_dir or os.path.join(os.getcwd(), "reports")
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"[UI] Exporting notes (.txt) to {target_dir}...")

        with self.page.expect_download(timeout=8000) as download_info:
            self.export_notes_button.click()

        download: Download = download_info.value
        dest_path = os.path.join(target_dir, download.suggested_filename)
        download.save_as(dest_path)
        logger.info(f"[UI] Notes exported successfully: {dest_path}")
        return dest_path

    # ----------------- Induction Chatbot Interactions -----------------
    def open_induction_chat(self):
        """Opens the Induction AI Guide (Sufi) chat panel if not already open."""
        if not self.is_induction_chat_open():
            logger.info("[UI] Opening Induction AI Guide chat panel...")
            self.chat_launcher.wait_for(state="visible", timeout=7000)
            self.chat_launcher.click()
            self.chat_panel.wait_for(state="visible", timeout=5000)
        else:
            logger.info("[UI] Induction AI Guide chat panel is already open.")

    def is_induction_chat_open(self) -> bool:
        """Verifies if the Induction Chatbot panel is open."""
        return self.chat_panel.is_visible()

    def click_chat_chip(self, chip_name: str):
        """Clicks one of the predefined quick chips in Sufi chat."""
        self.open_induction_chat()
        logger.info(f"[UI] Clicking Induction Chat chip: '{chip_name}'...")
        chip = self.page.locator(f".induction-chat-panel button:has-text('{chip_name}')").first
        chip.wait_for(state="visible", timeout=5000)
        chip.click()
        self.page.wait_for_timeout(1000)

    def ask_induction_guide(self, question: str):
        """Sends a natural language question to the Induction AI Guide."""
        self.open_induction_chat()
        logger.info(f"[UI] Asking Induction Guide: '{question}'...")
        self.chat_input.wait_for(state="visible", timeout=5000)
        self.chat_input.fill(question)
        self.page.wait_for_timeout(300)
        if self.chat_submit_button.is_visible():
            self.chat_submit_button.click()
        else:
            self.chat_input.press("Enter")
        self.page.wait_for_timeout(1000)

    def wait_for_guide_response(self, timeout_sec: int = 15) -> str:
        """Waits for Sufi to finish generating and returns the latest assistant message."""
        logger.info(f"[UI] Waiting for Induction AI Guide response (timeout={timeout_sec}s)...")
        # Wait until typing indicator finishes
        self.page.wait_for_timeout(3000)
        for _ in range(timeout_sec):
            typing = self.page.locator(".induction-chat-message:has-text('typing')")
            if not typing.is_visible():
                break
            self.page.wait_for_timeout(1000)

        messages = self.chat_messages.all_inner_texts()
        last_msg = messages[-1] if messages else ""
        logger.info(f"[UI] Received Induction AI Guide response: {last_msg[:120]}...")
        return last_msg

    # ----------------- Scoped Chapter & Slide Verification -----------------
    def get_welcome_slide_text(self) -> str:
        """Returns the full text displayed on the active welcome slide."""
        container = self.page.locator(".welcome-container, .induction-welcome-modal, main, body").first
        return container.inner_text().strip()

    def get_displayed_chapter_info(self) -> Dict[str, Any]:
        """
        Returns structured details of the currently displayed chapter:
        - Title
        - Category / Section badge
        - Body / Content paragraphs
        - Progress text
        - Next / Prev / Complete button visibility
        """
        title = ""
        badge = ""
        body = ""
        progress = ""

        title_el = self.page.locator(".induction-chapter-title, .chapter-header h2, h2.chakra-heading, h2").first
        if title_el.is_visible():
            title = title_el.inner_text().strip()

        badge_el = self.page.locator(".induction-chapter-badge, .section-badge, span.badge, .chakra-badge").first
        if badge_el.is_visible():
            badge = badge_el.inner_text().strip()

        body_el = self.page.locator(".induction-chapter-content, .chapter-body, .induction-content-card").first
        if body_el.is_visible():
            body = body_el.inner_text().strip()

        if self.chapter_progress.is_visible():
            progress = self.chapter_progress.inner_text().strip()

        return {
            "title": title,
            "badge": badge,
            "body": body,
            "progress": progress,
            "has_next": self.chapter_next_button.is_visible() and self.chapter_next_button.is_enabled(),
            "has_prev": self.chapter_prev_button.is_visible() and self.chapter_prev_button.is_enabled(),
            "is_complete_visible": self.complete_induction_button.is_visible()
        }

    def click_next_chapter(self):
        """Clicks the 'Next' button to advance to the next induction chapter."""
        next_btn = self.page.locator(".chapter-nav button:has-text('Next'), .induction-chapter-footer button:has-text('Next'), button.chapter-next:has-text('Next'), button.chakra-button:has-text('Next'), button:has-text('Next'):not(.scene-skip-button)").first
        if next_btn.is_visible() and next_btn.is_enabled():
            logger.info("[UI] Advancing to next induction chapter...")
            try:
                next_btn.scroll_into_view_if_needed()
                next_btn.click(timeout=3000)
            except Exception:
                try:
                    next_btn.click(force=True, timeout=2000)
                except Exception:
                    pass
            self.page.wait_for_timeout(1500)
        else:
            logger.info("[UI] Next chapter button is not enabled or visible.")

    def click_previous_chapter(self):
        """Clicks the 'Previous' button to move back to the preceding chapter."""
        prev_btn = self.page.locator(".chapter-nav button:has-text('Previous'), .induction-chapter-footer button:has-text('Previous'), button.chapter-prev:has-text('Previous'), button.chakra-button:has-text('Previous'), button:has-text('Previous'):not(.scene-skip-button)").first
        if prev_btn.is_visible() and prev_btn.is_enabled():
            logger.info("[UI] Returning to previous induction chapter...")
            try:
                prev_btn.scroll_into_view_if_needed()
                prev_btn.click(timeout=3000)
            except Exception:
                try:
                    prev_btn.click(force=True, timeout=2000)
                except Exception:
                    pass
            self.page.wait_for_timeout(1500)
        else:
            logger.info("[UI] Previous chapter button is not enabled or visible.")

    def get_all_welcome_slides_text(self, selected_guide: str = "Sufi") -> List[str]:
        """
        Advances slide-by-slide through the 7-slide welcome onboarding journey,
        capturing the full text displayed on each slide before clicking Continue.
        Returns the list of text strings from all visited slides.
        """
        logger.info(f"[UI] Capturing all welcome slides text (Guide: {selected_guide})...")
        slides_text = []

        for step in range(1, 10):
            current_text = self.get_welcome_slide_text()
            if current_text and (not slides_text or current_text != slides_text[-1]):
                slides_text.append(current_text)

            if self.start_journey_button.is_visible():
                logger.info("[UI] Clicking \"Let's Get Started\"...")
                self.start_journey_button.click()
                self.page.wait_for_timeout(800)
            elif self.continue_slide_button.is_visible():
                logger.info(f"[UI] Slide {len(slides_text)}: Clicking 'Continue'...")
                self.continue_slide_button.click()
                self.page.wait_for_timeout(800)
            elif self.resume_induction_button.is_visible():
                # Guide selection slide
                if selected_guide.lower() == "aarav" and self.guide_aarav_button.is_visible():
                    self.guide_aarav_button.click()
                elif selected_guide.lower() == "mira" and self.guide_mira_button.is_visible():
                    self.guide_mira_button.click()
                elif self.guide_sufi_button.is_visible():
                    self.guide_sufi_button.click()
                self.page.wait_for_timeout(500)
                logger.info("[UI] Clicking 'Resume / Start Induction'...")
                self.resume_induction_button.click()
                self.page.wait_for_timeout(1500)
                break
            elif self.notes_launcher.is_visible() or self.chat_launcher.is_visible():
                logger.info("[UI] Chapter view reached during slide traversal.")
                break
            else:
                self.page.wait_for_timeout(500)

        return slides_text

    def get_all_chapters_content(self, max_chapters: int = 15) -> List[Dict[str, Any]]:
        """
        Iterates forward through all accessible induction chapters and extracts
        their title, badge, content body, and progress information.
        Returns a list of dictionaries for each visited chapter.
        """
        logger.info("[UI] Extracting all induction chapters content...")
        chapters = []
        seen_titles = set()

        for _ in range(max_chapters):
            info = self.get_displayed_chapter_info()
            if info["title"] and info["title"] not in seen_titles:
                seen_titles.add(info["title"])
                chapters.append(info)
                logger.info(f"[UI] Chapter recorded: '{info['title']}' | Badge: '{info['badge']}'")

            if info["has_next"]:
                self.click_next_chapter()
            else:
                logger.info("[UI] Reached final induction chapter.")
                break

        return chapters
