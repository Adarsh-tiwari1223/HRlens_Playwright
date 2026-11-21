"""
Test Suite for Global HRlens AI Copilot Chatbot.
Automates and validates all employee self-service problem solving features:
1. Copilot launcher presence and all 7 quick suggestion chips.
2. AI-validated Leave Balance inquiry.
3. AI-validated Today's Attendance and punch record inquiry.
4. AI-validated Reporting Manager & TL hierarchy inquiry.
5. AI-validated Salary structure and Payslip download inquiry.
6. AI-validated Upcoming Holidays calendar inquiry.
7. AI-validated Company Policies and guidelines inquiry.
8. AI-validated Conversational Leave Application assistant.
9. Clear conversation history reset.

Note: Remote work/WFH application requests are excluded per project requirements.
"""

import pytest
from workflows.hrlense_portal.chatbot.global_chatbot_workflow import GlobalChatbotWorkflow


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.chatbot
class TestGlobalChatbot:
    """Test suite for Global HRlens AI Chatbot Copilot covering all employee problem-solving features."""

    def test_global_chatbot_all_employee_features_journey(self, logged_in_page):
        """
        Unified End-to-End Test for Real Employee:
        Executes and validates all 8 employee problem-solving features and session reset
        in a single continuous browser execution.
        """
        page, context = logged_in_page("kumar_piyush")
        workflow = GlobalChatbotWorkflow(page)

        print("\n" + "=" * 80)
        print("  STARTING GLOBAL CHATBOT ALL-FEATURES TEST :: EMPLOYEE ('kumar_piyush')")
        print("=" * 80)

        results = workflow.execute_complete_employee_chatbot_journey_workflow()

        # -------------------------------------------------------------
        # 1. Validate Launcher & Quick Action Chips
        # -------------------------------------------------------------
        launcher = results["launcher"]
        assert launcher["is_open"], "Global Chatbot window failed to open!"
        assert len(launcher["quick_chips"]) > 0, "No quick suggestion chips found in Copilot!"

        expected_chips = [
            "Leave Balance",
            "Today's Attendance",
            "My Manager & TL",
            "Salary & Payslip",
            "Company Policies",
            "Upcoming Holidays",
            "Apply Leave"
        ]
        for ec in expected_chips:
            assert any(ec.lower() in c.lower() for c in launcher["quick_chips"]), (
                f"Expected quick chip '{ec}' missing from {launcher['quick_chips']}"
            )

        print(f"\n[VALIDATION 1/9] Copilot Launcher & Chips verified:")
        print(f"  • Available Quick Chips: {launcher['quick_chips']}")

        # -------------------------------------------------------------
        # 2. Validate Leave Balance Inquiry
        # -------------------------------------------------------------
        leave_bal = results["leave_balance"]
        bal_reply = leave_bal["reply"].strip()
        assert len(bal_reply) > 0, "AI Copilot returned an empty response for leave balance inquiry!"
        assert any(k in bal_reply.lower() for k in ["leave", "policy", "balance", "casual", "earned", "privilege", "paid", "days"]), (
            f"AI leave balance response lacked relevant HR terminology! Got: '{bal_reply[:150]}'"
        )
        print(f"\n[VALIDATION 2/9] Leave Balance verified:")
        print(f"  • AI Response Snippet: {bal_reply[:140]}...")

        # -------------------------------------------------------------
        # 3. Validate Today's Attendance Inquiry
        # -------------------------------------------------------------
        attendance = results["attendance"]
        att_reply = attendance["reply"].strip()
        assert len(att_reply) > 0, "AI Copilot returned an empty response for today's attendance inquiry!"
        assert any(k in att_reply.lower() for k in ["attendance", "punch", "shift", "present", "timing", "hours", "status", "today", "record"]), (
            f"AI attendance response lacked attendance terminology! Got: '{att_reply[:150]}'"
        )
        print(f"\n[VALIDATION 3/9] Today's Attendance verified:")
        print(f"  • AI Response Snippet: {att_reply[:140]}...")

        # -------------------------------------------------------------
        # 4. Validate Reporting Manager & TL Inquiry
        # -------------------------------------------------------------
        manager = results["manager"]
        mgr_reply = manager["reply"].strip()
        assert len(mgr_reply) > 0, "AI Copilot returned an empty response for manager/TL inquiry!"
        assert any(k in mgr_reply.lower() for k in ["manager", "tl", "team lead", "reporting", "lead", "supervisor", "hierarchy", "assigned"]), (
            f"AI manager response lacked hierarchy terminology! Got: '{mgr_reply[:150]}'"
        )
        print(f"\n[VALIDATION 4/9] Manager & TL Hierarchy verified:")
        print(f"  • AI Response Snippet: {mgr_reply[:140]}...")

        # -------------------------------------------------------------
        # 5. Validate Salary & Payslip Breakdown Inquiry
        # -------------------------------------------------------------
        salary = results["salary"]
        sal_reply = salary["reply"].strip()
        assert len(sal_reply) > 0, "AI Copilot returned an empty response for salary breakdown inquiry!"
        assert any(k in sal_reply.lower() for k in ["salary", "payroll", "payslip", "compensation", "deduction", "slip", "payment", "earnings"]), (
            f"AI salary response lacked payroll terminology! Got: '{sal_reply[:150]}'"
        )
        print(f"\n[VALIDATION 5/9] Salary & Payslip Breakdown verified:")
        print(f"  • AI Response Snippet: {sal_reply[:140]}...")

        # -------------------------------------------------------------
        # 6. Validate Upcoming Holidays Inquiry
        # -------------------------------------------------------------
        holidays = results["holidays"]
        hol_reply = holidays["reply"].strip()
        assert len(hol_reply) > 0, "AI Copilot returned an empty response for upcoming holidays inquiry!"
        assert any(k in hol_reply.lower() for k in ["holiday", "calendar", "festival", "leave", "upcoming", "date", "diwali", "new year", "day", "republic"]), (
            f"AI holidays response lacked holiday terminology! Got: '{hol_reply[:150]}'"
        )
        print(f"\n[VALIDATION 6/9] Upcoming Holidays verified:")
        print(f"  • AI Response Snippet: {hol_reply[:140]}...")

        # -------------------------------------------------------------
        # 7. Validate Company Policies Inquiry
        # -------------------------------------------------------------
        policies = results["policies"]
        pol_reply = policies["reply"].strip()
        assert len(pol_reply) > 0, "AI Copilot returned an empty response for company policies inquiry!"
        assert any(k in pol_reply.lower() for k in ["policy", "guideline", "timing", "hours", "conduct", "rules", "probation", "notice", "standard"]), (
            f"AI policies response lacked policy terminology! Got: '{pol_reply[:150]}'"
        )
        print(f"\n[VALIDATION 7/9] Company Policies verified:")
        print(f"  • AI Response Snippet: {pol_reply[:140]}...")

        # -------------------------------------------------------------
        # 8. Validate Conversational Leave Application Assistant
        # -------------------------------------------------------------
        leave_app = results["conversational_leave"]
        apply_reply = leave_app["reply"].strip()
        assert len(apply_reply) > 0, "AI Copilot returned an empty response for conversational leave assistant!"
        assert any(k in apply_reply.lower() for k in ["leave", "request", "apply", "casual", "paid", "myleaves", "portal", "submit", "guidelines"]), (
            f"AI conversational leave response lacked relevant application terminology! Got: '{apply_reply[:150]}'"
        )
        print(f"\n[VALIDATION 8/9] Conversational Leave Assistant verified:")
        print(f"  • AI Response Snippet: {apply_reply[:140]}...")
        print(f"  • Action Buttons: {leave_app['action_buttons']}")

        # -------------------------------------------------------------
        # 9. Validate Clear Conversation Action
        # -------------------------------------------------------------
        assert results["is_cleared"], "Chat conversation history was not properly cleared!"
        print(f"\n[VALIDATION 9/9] Conversation history cleared successfully.")

        print("\n" + "=" * 80)
        print("  [SUCCESS] All 8 Employee Features + Clear Action Verified in Single Execution!")
        print("=" * 80 + "\n")
