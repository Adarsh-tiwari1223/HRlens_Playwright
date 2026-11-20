"""
Test Suite for Employee Induction Module Experience (/induction).
Covers:
1. 7-slide onboarding journey and AI Guide selection (Sufi).
2. Induction Notepad note creation, saved verification, and .txt export download.
3. Induction-Specific AI Chatbot (Ask Sufi) queries and quick chips.
"""

import os
import pytest
from workflows.hrlense_portal.induction.induction_workflow import InductionWorkflow


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.induction
class TestInductionModule:
    """Test suite for Employee Induction Module."""

    def test_induction_welcome_journey_and_ai_guide_selection(self, admin_page):
        """
        Verifies that navigating to /induction allows completing the 7-slide onboarding
        journey, selecting an AI Guide (Sufi), and reaching the interactive Chapter View.
        """
        workflow = InductionWorkflow(admin_page)
        journey_result = workflow.complete_welcome_journey_workflow(guide_name="Sufi")

        assert journey_result["success"], "Failed to transition to Induction Chapter View!"
        print(f"[TEST PASS] Induction Welcome Journey completed successfully with AI Guide '{journey_result['guide']}'.")

    def test_induction_notepad_create_and_export_notes(self, admin_page):
        """
        Verifies the Induction Notepad tool:
        1. Opens the Notepad drawer.
        2. Types and saves a new induction note.
        3. Exports saved notes as a .txt file.
        4. Validates that the exported file is downloaded and contains the exact note text.
        """
        workflow = InductionWorkflow(admin_page)
        test_note = "Automated Verification Note: Welcome to TEK Inspirations induction module."

        export_result = workflow.add_and_export_notes_workflow(test_note)

        assert export_result["file_size"] > 0, "Exported notes file is empty!"
        assert export_result["note_persisted"], f"Note text '{test_note}' was not found in exported file!"
        print(f"[TEST PASS] Notepad note added and exported successfully to '{export_result['file_path']}'.")

    def test_induction_ai_guide_sufi_interaction(self, admin_page):
        """
        Verifies the Induction-Specific AI Chatbot (Ask Sufi):
        1. Opens the Induction Chat panel.
        2. Clicks a predefined induction quick chip ('Leave Policy') or sends an orientation query.
        3. Asserts Sufi provides an induction-relevant response.
        """
        workflow = InductionWorkflow(admin_page)
        interaction_res = workflow.ask_induction_guide_workflow(chip_name="Leave Policy")

        assert interaction_res["is_valid_reply"], f"Sufi AI Guide failed to provide a valid response! Got: '{interaction_res['bot_reply']}'"
        print(f"[TEST PASS] Sufi Induction AI Guide responded successfully: '{interaction_res['bot_reply'][:100]}...'")
