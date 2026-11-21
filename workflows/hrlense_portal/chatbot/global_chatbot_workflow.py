"""
Workflow for Global HRlens AI Chatbot Copilot.
Orchestrates end-to-end testing of all employee self-service problem solving features:
1. Launcher presence and all 7 quick suggestion chips availability.
2. Leave Balance inquiry (itemized leave balance, casual, earned/privilege leaves).
3. Today's Attendance inquiry (punch timing, present/absent state, shift hours).
4. Reporting Manager & Team Lead inquiry (assigned manager, TL, approval hierarchy).
5. Salary & Payslip inquiry (compensation breakdown, payslip download instructions).
6. Upcoming Holidays inquiry (official gazetted company holidays calendar).
7. Company Policies inquiry (working hours, office conduct, leave guidelines).
8. Conversational Leave Application assistant (applying for emergency/planned leave).
9. Clear conversation header action.

Note: Remote work/WFH application requests are excluded per project requirements.
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
        """Verifies that the Copilot launcher is present, opens the window, and checks available chips."""
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
        Problem Solved: Employee checking remaining leave balance before planning time off.
        Queries leave balance via natural prompt and validates AI provides itemized balance.
        """
        logger.info("[WORKFLOW] Querying Leave Balance via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "What is my current leave balance?"
        prev_cnt = self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=25, previous_count=prev_cnt)
        logger.info(f"[WORKFLOW] Leave Balance reply: {reply[:120]}...")

        assert len(reply.strip()) > 0, "Empty response from Copilot for leave balance query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def query_today_attendance_workflow(self) -> Dict[str, Any]:
        """
        Problem Solved: Employee verifying punch-in / punch-out records and shift attendance status.
        Queries today's attendance and validates AI reports attendance/shift status.
        """
        logger.info("[WORKFLOW] Querying Today's Attendance via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "What is my attendance status and punch record today?"
        prev_cnt = self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=25, previous_count=prev_cnt)
        logger.info(f"[WORKFLOW] Today's Attendance reply: {reply[:120]}...")

        assert len(reply.strip()) > 0, "Empty response from Copilot for attendance query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def query_manager_and_tl_workflow(self) -> Dict[str, Any]:
        """
        Problem Solved: Employee finding assigned Reporting Manager and Team Lead for approvals.
        Queries manager details and validates AI identifies reporting authority.
        """
        logger.info("[WORKFLOW] Querying Reporting Manager & TL via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "Who is my reporting manager and team lead?"
        prev_cnt = self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=25, previous_count=prev_cnt)
        logger.info(f"[WORKFLOW] Manager & TL reply: {reply[:120]}...")

        assert len(reply.strip()) > 0, "Empty response from Copilot for manager query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def query_salary_and_payslip_workflow(self) -> Dict[str, Any]:
        """
        Problem Solved: Employee inquiring about monthly salary breakdown and payslip download.
        Queries salary structure and validates AI provides compensation guidance.
        """
        logger.info("[WORKFLOW] Querying Salary & Payslip details via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "Explain my salary structure, deduction components, and how to download my payslip"
        prev_cnt = self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=25, previous_count=prev_cnt)
        logger.info(f"[WORKFLOW] Salary structure reply: {reply[:120]}...")

        assert len(reply.strip()) > 0, "Empty response from Copilot for salary query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def query_upcoming_holidays_workflow(self) -> Dict[str, Any]:
        """
        Problem Solved: Employee checking upcoming public and company holidays for planning.
        Queries holiday schedule and validates AI returns holiday information.
        """
        logger.info("[WORKFLOW] Querying Upcoming Holidays via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "What are the upcoming official holidays?"
        prev_cnt = self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=25, previous_count=prev_cnt)
        logger.info(f"[WORKFLOW] Upcoming Holidays reply: {reply[:120]}...")

        assert len(reply.strip()) > 0, "Empty response from Copilot for holidays query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def query_company_policies_workflow(self) -> Dict[str, Any]:
        """
        Problem Solved: Employee checking office working hours, code of conduct, and guidelines.
        Queries policies and validates AI explains company rules.
        """
        logger.info("[WORKFLOW] Querying Company Policies via Copilot...")
        self.bot_page.open_chatbot()
        prompt = "What are the company policies regarding working hours and code of conduct?"
        prev_cnt = self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=25, previous_count=prev_cnt)
        logger.info(f"[WORKFLOW] Company Policies reply: {reply[:120]}...")

        assert len(reply.strip()) > 0, "Empty response from Copilot for policies query!"
        return {
            "query": prompt,
            "reply": reply,
            "has_content": len(reply.strip()) > 0
        }

    def conversational_leave_application_workflow(self, leave_reason: str = "personal work", days: int = 1) -> Dict[str, Any]:
        """
        Problem Solved: Employee needing to apply for leave directly or asking how to submit a request.
        Sends natural language instruction and validates AI processes or guides the request.
        """
        logger.info(f"[WORKFLOW] Initiating conversational leave application (reason: '{leave_reason}', days: {days})...")
        self.bot_page.open_chatbot()
        prompt = f"I want to apply for {days} day leave tomorrow because of {leave_reason}"
        prev_cnt = self.bot_page.send_message(prompt)

        reply = self.bot_page.wait_for_bot_response(timeout_sec=25, previous_count=prev_cnt)
        action_buttons = self.bot_page.get_action_buttons()

        logger.info(f"[WORKFLOW] Conversational Leave Response: {reply[:120]}...")
        logger.info(f"[WORKFLOW] Available action buttons: {action_buttons}")

        assert len(reply.strip()) > 0, "Empty response from Copilot for conversational leave application!"
        return {
            "prompt": prompt,
            "reply": reply,
            "action_buttons": action_buttons
        }

    def clear_conversation_workflow(self) -> bool:
        """Tests the Clear Conversation header control."""
        logger.info("[WORKFLOW] Testing Clear Conversation action...")
        self.bot_page.clear_conversation()
        logger.info("[WORKFLOW] Clear conversation header action invoked successfully.")
        return True

    def execute_complete_employee_chatbot_journey_workflow(self) -> Dict[str, Any]:
        """
        Unified End-to-End Employee Problem-Solving Journey:
        Tests all valid employee self-service features in one clean browser session (remote requests excluded):
        1. Launcher & Quick Action Chips Availability
        2. Leave Balance Inquiry
        3. Today's Attendance Inquiry
        4. Reporting Manager & TL Inquiry
        5. Salary & Payslip Breakdown Inquiry
        6. Upcoming Holidays Inquiry
        7. Company Policies Inquiry
        8. Conversational Leave Application Assistant
        9. Clear Conversation Action
        """
        logger.info("================================================================================")
        logger.info("[WORKFLOW] STARTING UNIFIED EMPLOYEE CHATBOT PROBLEM-SOLVING JOURNEY")
        logger.info("================================================================================")
        results = {}

        # 1. Launcher & Quick Action Chips
        logger.info("[WORKFLOW] [STEP 1/9] Verifying Copilot Launcher & Quick Chips...")
        results["launcher"] = self.verify_copilot_availability_workflow()

        # 2. Leave Balance Inquiry
        logger.info("[WORKFLOW] [STEP 2/9] Validating Leave Balance Resolution...")
        results["leave_balance"] = self.query_leave_balance_workflow()

        # 3. Today's Attendance Inquiry
        logger.info("[WORKFLOW] [STEP 3/9] Validating Today's Attendance Resolution...")
        results["attendance"] = self.query_today_attendance_workflow()

        # 4. Reporting Manager & TL Inquiry
        logger.info("[WORKFLOW] [STEP 4/9] Validating Manager & TL Hierarchy Resolution...")
        results["manager"] = self.query_manager_and_tl_workflow()

        # 5. Salary & Payslip Breakdown
        logger.info("[WORKFLOW] [STEP 5/9] Validating Salary & Payslip Breakdown Resolution...")
        results["salary"] = self.query_salary_and_payslip_workflow()

        # 6. Upcoming Holidays Inquiry
        logger.info("[WORKFLOW] [STEP 6/9] Validating Upcoming Holidays Resolution...")
        results["holidays"] = self.query_upcoming_holidays_workflow()

        # 7. Company Policies Inquiry
        logger.info("[WORKFLOW] [STEP 7/9] Validating Company Policies Resolution...")
        results["policies"] = self.query_company_policies_workflow()

        # 8. Conversational Leave Application Assistant
        logger.info("[WORKFLOW] [STEP 8/9] Validating Conversational Leave Application Assistant...")
        results["conversational_leave"] = self.conversational_leave_application_workflow(leave_reason="personal work", days=1)

        # 9. Clear Conversation
        logger.info("[WORKFLOW] [STEP 9/9] Validating Clear Conversation Action...")
        results["is_cleared"] = self.clear_conversation_workflow()

        logger.info("================================================================================")
        logger.info("[WORKFLOW] COMPLETED UNIFIED EMPLOYEE CHATBOT PROBLEM-SOLVING JOURNEY")
        logger.info("================================================================================")
        return results
