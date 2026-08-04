"""
Workflow Layer for Meetings Module (HR Lens Portal -> Meetings).
Encapsulates high-level end-to-end business workflows for Meeting creation and validation.
"""

from pages.hrlense_portal.meeting.meeting_page import MeetingPage
from utils.logger import log_step


class MeetingWorkflow:
    def __init__(self, page):
        self.page = page
        self.meeting_page = MeetingPage(page)

    def execute_create_meeting_workflow(
        self,
        title: str,
        description: str,
        date_str: str,
        participant_name: str | list[str] = None,
        candidate_pool: list[str] = None,
        category_tab: str = "Employee",
        start_time: str = "10:00",
        end_time: str = "11:00",
        is_online: bool = True
    ) -> dict:
        """
        Executes complete 15-Step Create Meeting Workflow:
        1. Navigate to Meetings module.
        2. Verify 'Create New Meeting' button visibility.
        3. Click 'Create New Meeting'.
        4. Verify wizard sections.
        5. Fill Meeting Details.
        6. Select Participants via Search -> Select First -> Clear sequence (Employee/Team/Mix).
        7. Check Availability & conflicts.
        8. Submit & Confirm Meeting.
        """
        # Step 2: Navigate to Meetings
        log_step("Step 2: Navigate to Meetings Module")
        self.meeting_page.navigate_to_meetings()

        # Step 3: Check Create Button
        log_step("Step 3: Verify 'Create New Meeting' Button Visible")
        btn_ok = self.meeting_page.is_create_meeting_button_visible()

        # Step 4: Click Create
        log_step("Step 4: Click 'Create New Meeting'")
        self.meeting_page.click_create_new_meeting()

        # Step 5: Verify Wizard Sections
        log_step("Step 5: Verify Wizard Sections")
        wizard_ok = self.meeting_page.verify_wizard_sections()

        # Stepper 1: Fill Meeting Details & Click Next -> Stepper 2
        log_step("Stepper 1: Fill Meeting Details", value=f"Title='{title}' | Date='{date_str}' | Start='{start_time}' | End='{end_time}'")
        self.meeting_page.fill_meeting_details(
            title=title,
            description=description,
            date_str=date_str,
            start_time=start_time,
            end_time=end_time,
            is_online=is_online
        )
        self.meeting_page.click_next_step()

        # Stepper 2: Select Candidates & Click Check availability -> Stepper 3
        added_candidates = self.meeting_page.select_participant(
            participant_name=participant_name,
            candidate_pool=candidate_pool,
            min_count=2,
            max_count=5,
            category_tab=category_tab
        )
        p_display = ", ".join(added_candidates) if added_candidates else "sanidhy"
        log_step("Stepper 2: Search & Select Participant", value=f"Tab: '{category_tab}' | Candidates Added: '{p_display}'")

        # Stepper 3: Verify Availability & Submit 'Create meeting'
        chk_ok, avail_cnt, conflict_cnt, avail_status, conflict_count = self.meeting_page.check_availability()
        log_step("Stepper 3: Verify Availability Readout", value=f"Status=>{avail_status} | {conflict_count}")

        # Final Confirmation & Catch Google OAuth Popup
        sub_ok, popup_opened, toast_msg, action_taken, submission_status = self.meeting_page.submit_and_confirm_meeting(avail_cnt=avail_cnt, conflict_cnt=conflict_cnt)
        log_step("Submit Meeting & Catch Google OAuth Popup", value=f"Action Taken: '{action_taken}' | Toast: '{toast_msg}'")

        # Step 4: Verify Created Meeting Entry in Table Grid (Title column)
        log_step("Verify Created Meeting Entry in Table Grid (Title column)", value=f"Title='{title}'")
        in_grid, grid_meta = self.meeting_page.verify_meeting_in_list(title)
        log_step("Grid Verification Result", value=f"Verified in Table: {in_grid}")

        return {
            "btn_visible": btn_ok,
            "wizard_ok": wizard_ok,
            "availability_status": avail_status,
            "conflict_count": conflict_count,
            "popup_opened": popup_opened,
            "toast_msg": toast_msg,
            "submission_status": submission_status,
            "verified_in_list": in_grid,
            "grid_meta": grid_meta
        }
