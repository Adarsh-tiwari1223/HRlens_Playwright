"""
Page Object for Global HRlens AI Chatbot Copilot.
Available globally across portal pages (Dashboard, Master, Attendance, etc.).

Owns:
- Locators for floating trigger button, chat window, header actions (Clear, Close)
- Quick chips (Leave Balance, Salary & Payslip, Apply Leave, Upcoming Holidays, etc.)
- Message input, send button, message history (.ai-message)
- Action buttons inside bot messages (Leave Confirmation, Payroll Download, etc.)
"""

import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class GlobalChatbotPage(BasePage):
    """Page Object for the Global HRlens AI Copilot Chatbot."""

    def __init__(self, page: Page):
        super().__init__(page)

        # Floating Widget & Container
        self.wrapper = self.page.locator(".ai-chatbot-wrapper")
        self.trigger_button = self.page.locator("button.ai-chat-trigger-btn")
        self.chat_window = self.page.locator(".ai-chat-window")

        # Header Controls
        self.header_title = self.page.locator(".ai-header-info h4, .ai-chat-header")
        self.clear_button = self.page.locator("button.ai-header-btn[title='Clear Conversation']").first
        self.close_button = self.page.locator("button.ai-header-btn[title='Close']").first

        # Quick Suggestion Chips
        self.quick_chips = self.page.locator("button.ai-quick-chip")
        self.chip_leave_balance = self.page.locator("button.ai-quick-chip:has-text('Leave Balance')").first
        self.chip_attendance = self.page.locator("button.ai-quick-chip:has-text(\"Today's Attendance\")").first
        self.chip_salary_payslip = self.page.locator("button.ai-quick-chip:has-text('Salary & Payslip')").first
        self.chip_holidays = self.page.locator("button.ai-quick-chip:has-text('Upcoming Holidays')").first
        self.chip_apply_leave = self.page.locator("button.ai-quick-chip:has-text('Apply Leave')").first
        self.chip_policies = self.page.locator("button.ai-quick-chip:has-text('Company Policies')").first

        # Input & Send
        self.input_field = self.page.locator(".ai-chatbot-wrapper input[placeholder*='Ask HRlense AI' i], .ai-chat-footer input").first
        self.send_button = self.page.locator("button.ai-send-btn, .ai-chatbot-wrapper button[title='Send message']").first

        # Messages & Action Components
        self.messages = self.page.locator(".ai-chat-messages .ai-message")
        self.bot_messages = self.page.locator(".ai-chat-messages .ai-message.bot")
        self.user_messages = self.page.locator(".ai-chat-messages .ai-message.user")
        self.message_action_buttons = self.page.locator(".ai-chat-messages button")

    def is_chatbot_present(self) -> bool:
        """Verifies if the Global Chatbot trigger or window exists on the page."""
        try:
            self.trigger_button.first.wait_for(state="attached", timeout=6000)
            return True
        except Exception:
            return self.wrapper.count() > 0 or self.trigger_button.count() > 0

    def is_window_open(self) -> bool:
        """Checks if the chat window is currently visible/open."""
        return self.chat_window.is_visible()

    def open_chatbot(self):
        """Ensures the chat window is open."""
        if not self.is_window_open():
            logger.info("[UI] Opening Global Chatbot window via trigger button...")
            self.trigger_button.click(force=True)
            self.chat_window.wait_for(state="visible", timeout=5000)
        else:
            logger.info("[UI] Global Chatbot window is already open.")

    def close_chatbot(self):
        """Closes the chat window via close button."""
        if self.is_window_open():
            logger.info("[UI] Closing Global Chatbot window...")
            self.close_button.click(force=True)
            self.page.wait_for_timeout(800)

    def clear_conversation(self):
        """Clears existing chat messages via the header clear button."""
        self.open_chatbot()
        logger.info("[UI] Clearing conversation history...")
        self.clear_button.wait_for(state="visible", timeout=5000)
        self.clear_button.click(force=True)
        self.page.wait_for_timeout(1500)

    def click_quick_chip(self, chip_title: str):
        """Clicks a quick chip by text title."""
        self.open_chatbot()
        logger.info(f"[UI] Clicking quick chip: '{chip_title}'...")
        chip = self.page.locator(f"button.ai-quick-chip:has-text('{chip_title}')").first
        chip.wait_for(state="visible", timeout=5000)
        chip.click(force=True)
        self.page.wait_for_timeout(1500)

    def send_message(self, message: str):
        """Types message into the input field and sends it."""
        self.open_chatbot()
        logger.info(f"[UI] Sending prompt to Global Chatbot: '{message}'...")
        self.input_field.wait_for(state="visible", timeout=5000)
        self.input_field.fill(message)
        self.page.wait_for_timeout(300)
        # Using Enter to reliably submit across different layout overlaps, with send_button fallback
        try:
            self.input_field.press("Enter")
        except Exception:
            self.send_button.click(force=True)
        self.page.wait_for_timeout(1000)

    def wait_for_bot_response(self, timeout_sec: int = 20) -> str:
        """
        Waits for the bot response to finish generating and returns the latest bot message.
        """
        logger.info(f"[UI] Waiting for Global Chatbot response (timeout={timeout_sec}s)...")
        # Give initial delay for generation
        self.page.wait_for_timeout(4000)

        # Wait until loading / typing indicator ceases
        for _ in range(timeout_sec):
            typing = self.page.locator(".ai-message:has-text('typing'), .ai-typing-indicator, .ai-chat-messages .dot")
            if not typing.is_visible():
                break
            self.page.wait_for_timeout(1000)

        bot_msgs = self.bot_messages.all_inner_texts()
        latest_reply = bot_msgs[-1] if bot_msgs else ""
        logger.info(f"[UI] Bot Response received: {latest_reply[:120]}...")
        return latest_reply

    def get_action_buttons(self) -> List[str]:
        """Returns the list of button labels currently rendered inside chat messages."""
        return [b.inner_text().strip() for b in self.message_action_buttons.all() if b.is_visible()]

    def click_message_action_button(self, button_text: str):
        """Clicks a specific action button inside a chat message (e.g. Confirm, Submit, Download)."""
        logger.info(f"[UI] Clicking action button in chat message: '{button_text}'...")
        btn = self.page.locator(f".ai-chat-messages button:has-text('{button_text}')").first
        btn.wait_for(state="visible", timeout=5000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)
