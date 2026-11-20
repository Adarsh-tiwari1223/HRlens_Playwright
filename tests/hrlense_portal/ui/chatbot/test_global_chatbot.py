"""
Test Suite for Global HRlens AI Copilot Chatbot.
Executes all employee actions and AI response validations in a single execution flow:
1. Copilot launcher presence and quick chips verification.
2. AI-validated Leave Balance inquiry.
3. AI-validated Conversational Leave Application request.
4. AI-validated Salary structure and Payroll explanation.
5. AI-validated Disallowed Action (Remote request restriction rule).
6. Clear conversation history reset.
"""

import pytest
from workflows.hrlense_portal.chatbot.global_chatbot_workflow import GlobalChatbotWorkflow


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.chatbot
class TestGlobalChatbot:
    """Test suite for Global HRlens AI Chatbot Copilot using a real employee account."""

    def test_global_chatbot_complete_employee_actions_and_ai_validation(self, logged_in_page):
        """
        Single-Execution End-to-End Chatbot Test for Real Employee:
        Executes all permitted employee actions, validates AI-generated responses,
        and enforces the restriction rule disallowing remote work applications via chat.
        """
        page, context = logged_in_page("adarsh")
        workflow = GlobalChatbotWorkflow(page)

        print("\n" + "=" * 75)
        print("  STARTING UNIFIED CHATBOT TEST :: REAL EMPLOYEE ('adarsh')")
        print("=" * 75)

        results = workflow.execute_complete_employee_chatbot_journey_workflow()

        # -------------------------------------------------------------
        # 1. Validate Launcher & Quick Action Chips
        # -------------------------------------------------------------
        launcher = results["launcher"]
        assert launcher["is_open"], "Global Chatbot window failed to open!"
        assert len(launcher["quick_chips"]) > 0, "No quick suggestion chips found in Copilot!"

        expected_chips = ["Leave Balance", "Today's Attendance", "Salary & Payslip", "Apply Leave"]
        for ec in expected_chips:
            assert any(ec.lower() in c.lower() for c in launcher["quick_chips"]), f"Expected chip '{ec}' missing from {launcher['quick_chips']}"

        print(f"\n[AI & UI VALIDATION 1/6] Copilot Launcher & Chips verified:")
        print(f"  • Available Quick Chips: {launcher['quick_chips']}")

        # -------------------------------------------------------------
        # 2. Validate AI Leave Balance Response
        # -------------------------------------------------------------
        leave_bal = results["leave_balance"]
        bal_reply = leave_bal["reply"].strip()
        assert len(bal_reply) > 0, "AI Copilot returned an empty response for leave balance inquiry!"
        assert any(k in bal_reply.lower() for k in ["leave", "policy", "balance", "annual", "guidelines", "paid"]), (
            f"AI leave balance response lacked relevant HR terminology! Got: '{bal_reply[:150]}'"
        )

        print(f"\n[AI & UI VALIDATION 2/6] Leave Balance AI response verified:")
        print(f"  • AI Response Snippet: {bal_reply[:140]}...")

        # -------------------------------------------------------------
        # 3. Validate AI Conversational Leave Application Response
        # -------------------------------------------------------------
        leave_apply = results["leave_apply"]
        apply_reply = leave_apply["reply"].strip()
        assert len(apply_reply) > 0, "AI Copilot did not respond to conversational leave application request!"
        assert any(k in apply_reply.lower() for k in ["leave", "request", "apply", "my leaves", "guidelines", "paid"]), (
            f"AI conversational leave response lacked relevant application terminology! Got: '{apply_reply[:150]}'"
        )

        print(f"\n[AI & UI VALIDATION 3/6] Conversational Leave AI response verified:")
        print(f"  • AI Response Snippet: {apply_reply[:140]}...")
        print(f"  • Generated Action Buttons: {leave_apply['action_buttons']}")

        # -------------------------------------------------------------
        # 4. Validate AI Salary & Payroll Explanation Response
        # -------------------------------------------------------------
        salary = results["salary_inquiry"]
        salary_reply = salary["reply"].strip()
        assert len(salary_reply) > 0, "AI Copilot returned an empty response for salary breakdown inquiry!"
        assert any(k in salary_reply.lower() for k in ["salary", "payroll", "payslip", "compensation", "deduction", "slip"]), (
            f"AI salary inquiry response lacked payroll terminology! Got: '{salary_reply[:150]}'"
        )

        print(f"\n[AI & UI VALIDATION 4/6] Salary & Payroll Breakdown AI response verified:")
        print(f"  • AI Response Snippet: {salary_reply[:140]}...")

        # -------------------------------------------------------------
        # 5. Validate Remote Request Restriction (Business Rule)
        # -------------------------------------------------------------
        remote = results["remote_restriction"]
        remote_reply = remote["reply"].strip()
        assert remote["remote_application_blocked"], (
            "Chatbot unexpectedly provided a direct remote request submission button!"
        )
        assert len(remote_reply) > 0, "AI Copilot provided empty response for remote request prompt!"

        print(f"\n[AI & UI VALIDATION 5/6] Remote Request Restriction verified:")
        print(f"  • Direct Remote Submit Blocked: {remote['remote_application_blocked']}")
        print(f"  • AI Guidance Response: {remote_reply[:140]}...")

        # -------------------------------------------------------------
        # 6. Validate Clear Conversation
        # -------------------------------------------------------------
        assert results["is_cleared"], "Chat conversation history was not properly cleared!"
        print(f"\n[AI & UI VALIDATION 6/6] Conversation history cleared successfully.")

        print("\n" + "=" * 75)
        print("  [SUCCESS] All 6 Actions & AI Responses Verified in Single Execution!")
        print("=" * 75 + "\n")
