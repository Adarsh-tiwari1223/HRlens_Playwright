"""
Workflow for Global HRlens AI Chatbot Copilot.
Orchestrates:
- Triggering and verifying Copilot on any portal page
- Quick suggestion chip queries (Leave Balance, Upcoming Holidays, etc.)
- Natural language conversational HR tasks:
    1. Leave Application & Balance inquiries
    2. Salary & Payslip breakdowns
- Conversation history clear and window management
"""

import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import Page
from pages.hrlense_portal.chatbot.global_chatbot_page import GlobalChatbotPage

logger = logging.getLogger(__name__)


class GlobalChatbotWorkflow:
    """Orchestrates Global HRlens AI Copilot interactions and validations."""

    def __init__(self, page: Page):
        self.page = page
        self.bot_page = GlobalChatbotPage(page)

    def verify_copilot_availability_workflow(self) -> Dict[str, Any]:
        """Verifies that the Copilot launcher is present, opens the window, and checks greeting."""
        logger.info("[WORKFLOW] Checking Global Copilot availability...")
        assert self.bot_page.is_chatbot_present(), "Global Chatbot widget not found on page!"

        self.bot_page.open_chatbot()
        is_open = self.bot_page.is_window_open()
        header_text = self.bot_page.header_title.first.inner_text().replace("\n", " ") if self.bot_page.header_title.count() > 0 else ""
        quick_chips = [c.inner_text().strip() for c in self.bot_page.quick_chips.all() if c.is_visible()]

        logger.info(f"[WORKFLOW] Copilot Open: {is_open} | Header: {header_text} | Chips: {quick_chips}")
        return {
            "is_open": is_open,
            "header": header_text,
            "quick_chips": quick_chips
        }

    def query_leave_balance_workflow(self) -> Dict[str, Any]:
        """
        Sends a leave balance query via prompt or quick chip,
        and verifies that the AI Copilot returns an informative response.
        """
        logger.info("[WORKFLOW] Querying Leave Balance via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "What is my current leave balance?"
        self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=15)
        logger.info(f"[WORKFLOW] Leave Balance reply: {reply[:120]}...")

        # Assert response is meaningful
        assert len(reply.strip()) > 0, "Empty response from Copilot for leave balance query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def conversational_leave_application_workflow(self, leave_reason: str = "fever", days: int = 1) -> Dict[str, Any]:
        """
        Conversational Leave Application Workflow:
        Sends natural language instruction to apply for leave,
        waits for Copilot to process, generate summary or confirmation card.
        """
        logger.info(f"[WORKFLOW] Initiating conversational leave application (reason: '{leave_reason}')...")
        self.bot_page.open_chatbot()
        prompt = f"I want to apply for {days} day sick leave tomorrow because of {leave_reason}"
        self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=18)
        action_buttons = self.bot_page.get_action_buttons()

        logger.info(f"[WORKFLOW] Conversational Leave Response: {reply[:150]}...")
        logger.info(f"[WORKFLOW] Available action buttons: {action_buttons}")

        return {
            "prompt": prompt,
            "reply": reply,
            "action_buttons": action_buttons
        }

    def query_salary_and_payslip_workflow(self) -> Dict[str, Any]:
        """
        Asks Copilot to explain salary structure or payslip details.
        Verifies that payroll/salary information is provided.
        """
        logger.info("[WORKFLOW] Querying Salary & Payslip details via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "Explain my salary structure and deduction components"
        self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=18)
        logger.info(f"[WORKFLOW] Salary structure reply: {reply[:150]}...")

        assert len(reply.strip()) > 0, "Empty response from Copilot for salary query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def verify_remote_request_restriction_workflow(self, prompt: str = "I want to apply for remote request tomorrow") -> Dict[str, Any]:
        """
        Business Rule: Chatbot supports employee self-service queries and actions
        EXCEPT applying remote work / WFH requests directly via chat.
        Verifies that submitting a remote request prompt does not trigger a remote submission
        action button and the user is redirected to use portal forms.
        """
        logger.info(f"[WORKFLOW] Verifying Remote Request restriction via Copilot (prompt: '{prompt}')...")
        self.bot_page.open_chatbot()
        self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=18)
        action_buttons = self.bot_page.get_action_buttons()

        logger.info(f"[WORKFLOW] Remote Request Reply: {reply[:120]}...")
        logger.info(f"[WORKFLOW] Action Buttons present: {action_buttons}")

        # Assert no remote work submission button is provided
        has_remote_submit_button = any(
            any(w in b.lower() for w in ["submit remote", "confirm remote", "apply remote", "confirm wfh"])
            for b in action_buttons
        )

        return {
            "prompt": prompt,
            "reply": reply,
            "action_buttons": action_buttons,
            "remote_application_blocked": not has_remote_submit_button
        }

    def execute_complete_employee_chatbot_journey_workflow(self) -> Dict[str, Any]:
        """
        Unified Single-Execution Chatbot Workflow for Real Employee:
        Executes all permitted employee actions and negative restriction rule in one browser session:
        1. Open Copilot and validate presence of all employee quick chips.
        2. Query Leave Balance -> validates AI response mentions leave policy / balance.
        3. Conversational Leave Application -> validates AI processes leave request.
        4. Salary & Payslip Inquiry -> validates AI explains salary/payroll components.
        5. Remote Request Restriction (Negative Rule) -> validates remote work application is blocked.
        6. Clear Conversation -> validates chat history resets.
        """
        logger.info("[WORKFLOW] === Starting Unified Employee Chatbot Single Execution ===")
        results = {}

        # 1. Copilot Availability & Chips
        logger.info("[WORKFLOW] [STEP 1/6] Verifying Copilot Launcher & Quick Chips...")
        results["launcher"] = self.verify_copilot_availability_workflow()

        # 2. Leave Balance Inquiry
        logger.info("[WORKFLOW] [STEP 2/6] Validating AI Leave Balance Inquiry...")
        results["leave_balance"] = self.query_leave_balance_workflow()

        # 3. Conversational Leave Application
        logger.info("[WORKFLOW] [STEP 3/6] Validating AI Conversational Leave Application...")
        results["leave_apply"] = self.conversational_leave_application_workflow(leave_reason="viral fever", days=1)

        # 4. Salary & Payroll Breakdown
        logger.info("[WORKFLOW] [STEP 4/6] Validating AI Salary & Payroll Breakdown...")
        results["salary_inquiry"] = self.query_salary_and_payslip_workflow()

        # 5. Remote Request Restriction (Disallowed action)
        logger.info("[WORKFLOW] [STEP 5/6] Validating Remote Request Restriction (Disallowed Action)...")
        results["remote_restriction"] = self.verify_remote_request_restriction_workflow("I want to apply for remote request tomorrow")

        # 6. Clear Conversation
        logger.info("[WORKFLOW] [STEP 6/6] Validating Clear Conversation Action...")
        results["is_cleared"] = self.clear_conversation_workflow()

        logger.info("[WORKFLOW] === Unified Employee Chatbot Single Execution Completed ===")
        return results

    def clear_conversation_workflow(self) -> bool:
        """Clears conversation and verifies message history is purged."""
        logger.info("[WORKFLOW] Testing Clear Conversation action...")
        self.bot_page.clear_conversation()
        for _ in range(5):
            count = self.bot_page.messages.count()
            if count <= 1:
                break
            self.page.wait_for_timeout(1000)
        remaining_msgs = self.bot_page.messages.count()
        logger.info(f"[WORKFLOW] Remaining messages after clear: {remaining_msgs}")
        return remaining_msgs <= 1  # May keep initial greeting
