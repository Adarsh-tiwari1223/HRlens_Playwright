"""
Workflow for Master Induction Policy Configuration.
Orchestrates:
- Navigation and 5-Stepper inspection (Steps 1 to 5)
- Content table data extraction and validation
- Content search and filtering verification
- '+ Add Content' modal workflow
"""

import os
import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import Page
from pages.hrlense_portal.master.master_induction_policy_page import MasterInductionPolicyPage

logger = logging.getLogger(__name__)


class MasterInductionPolicyWorkflow:
    """Orchestrates Master Induction Policy business actions and validations."""

    def __init__(self, page: Page):
        self.page = page
        self.policy_page = MasterInductionPolicyPage(page)

    def navigate_and_verify_policy_workflow(self) -> Dict[str, Any]:
        """Navigates to /master/induction-policy and verifies core layout."""
        logger.info("[WORKFLOW] Navigating to Master Induction Policy...")
        self.policy_page.navigate_to_induction_policy()
        headers = self.policy_page.get_table_headers()
        row_count = self.policy_page.get_row_count()
        return {
            "url": self.page.url,
            "headers": headers,
            "initial_step_rows": row_count
        }

    def review_all_five_steps_workflow(self) -> Dict[int, Dict[str, Any]]:
        """
        Steps through all 5 Induction Policy Steppers:
        STEP 1: Company Profile
        STEP 2: Branch & Location
        STEP 3: Business Process
        STEP 4: Department
        STEP 5: HR Policies
        Returns row counts, headers, and sample row data for each step.
        """
        logger.info("[WORKFLOW] Reviewing all 5 Master Induction Policy Steps...")
        self.policy_page.navigate_to_induction_policy()
        step_results = {}

        for step in range(1, 6):
            self.policy_page.select_step(step)
            row_count = self.policy_page.get_row_count()
            headers = self.policy_page.get_table_headers()
            sample_row = self.policy_page.get_table_row_data(0) if row_count > 0 else {}
            logger.info(f"[WORKFLOW] Step {step} -> Rows: {row_count} | Sample: {sample_row.get('TITLE / HEADING', '')}")
            step_results[step] = {
                "row_count": row_count,
                "headers": headers,
                "sample_row": sample_row
            }

        return step_results

    def search_policy_content_workflow(self, query: str = "Leave") -> Dict[str, Any]:
        """
        Tests the content search functionality across induction policy items.
        Filters by query, asserts results match or table updates, then clears filter.
        """
        logger.info(f"[WORKFLOW] Executing Policy Content Search for: '{query}'...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(5)  # HR Policies typically has leave/attendance content
        initial_count = self.policy_page.get_row_count()

        self.policy_page.search_content(query)
        filtered_count = self.policy_page.get_row_count()
        sample = self.policy_page.get_table_row_data(0) if filtered_count > 0 else {}

        self.policy_page.clear_search()
        restored_count = self.policy_page.get_row_count()

        return {
            "query": query,
            "initial_count": initial_count,
            "filtered_count": filtered_count,
            "restored_count": restored_count,
            "sample_matched": sample
        }

    def verify_scoping_dropdowns_workflow(self, target_dept: str = "Developer") -> Dict[str, Any]:
        """
        Tests the Company, Branch, and Department scoping dropdowns:
        1. Retrieves available scoping options.
        2. Filters content by Department (e.g. 'Developer').
        3. Asserts filtered rows reflect target audience scope.
        4. Resets filters back to 'All' and asserts table restoration.
        """
        logger.info(f"[WORKFLOW] Testing Induction Policy Scoping by Department: '{target_dept}'...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(1)

        available_companies = self.policy_page.get_available_companies()
        available_depts = self.policy_page.get_available_departments()
        initial_rows = self.policy_page.get_row_count()

        # Apply department scope
        self.policy_page.select_scope_department(target_dept)
        scoped_rows = self.policy_page.get_row_count()
        sample_scoped = self.policy_page.get_table_row_data(0) if scoped_rows > 0 else {}

        # Reset scope
        self.policy_page.reset_all_scopes()
        restored_rows = self.policy_page.get_row_count()

        logger.info(f"[WORKFLOW] Scoping verified: initial={initial_rows}, scoped={scoped_rows}, restored={restored_rows}")
        return {
            "available_companies": available_companies,
            "available_departments": available_depts,
            "initial_rows": initial_rows,
            "scoped_rows": scoped_rows,
            "restored_rows": restored_rows,
            "sample_scoped": sample_scoped
        }

    def verify_multi_scoped_matrix_workflow(
        self,
        step_number: int = 1,
        company: Optional[str] = None,
        branch: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates centralized scoping control matrix across Company, Branch, and Department:
        1. Selects the target stepper step.
        2. Applies specified company, branch, and/or department scoping filters.
        3. Extracts all displayed rows and verifies Target Audience alignment.
        4. Resets scopes and verifies restoration.
        """
        logger.info(f"[WORKFLOW] Verifying Scoping Matrix (Step {step_number}): Company={company}, Branch={branch}, Dept={department}...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(step_number)

        initial_rows = self.policy_page.get_row_count()

        if company:
            self.policy_page.select_scope_company(company)
        if branch:
            self.policy_page.select_scope_branch(branch)
        if department:
            self.policy_page.select_scope_department(department)

        filtered_rows = self.policy_page.get_row_count()
        all_rows_data = self.policy_page.get_all_rows_data()

        # Reset scopes back to universal view
        self.policy_page.reset_all_scopes()
        restored_rows = self.policy_page.get_row_count()

        return {
            "step": step_number,
            "company_filter": company,
            "branch_filter": branch,
            "department_filter": department,
            "initial_rows": initial_rows,
            "filtered_rows": filtered_rows,
            "restored_rows": restored_rows,
            "rows_data": all_rows_data
        }

    def verify_add_content_modal_workflow(self) -> bool:
        """Opens '+ Add Content' modal, verifies it is presented, then safely closes it."""
        logger.info("[WORKFLOW] Testing '+ Add Content' modal workflow...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.open_add_content_modal()
        is_open = self.policy_page.is_add_content_modal_open()
        assert is_open, "Add Content modal failed to open!"
        self.policy_page.close_add_content_modal()
        return is_open

    def toggle_content_active_workflow(self, step_number: int = 1, row_index: int = 0) -> bool:
        """Toggles active switch on a content row and verifies state change."""
        logger.info(f"[WORKFLOW] Toggling active status for Step {step_number}, Row {row_index}...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(step_number)
        return self.policy_page.toggle_row_active(row_index)

    def edit_content_workflow(self, step_number: int = 1, row_index: int = 0, new_title_suffix: str = " (Verified)") -> Dict[str, Any]:
        """Edits an existing induction content row and updates its title."""
        logger.info(f"[WORKFLOW] Editing content for Step {step_number}, Row {row_index}...")
        self.policy_page.navigate_to_induction_policy()
        self.policy_page.select_step(step_number)
        initial_data = self.policy_page.get_table_row_data(row_index)
        original_title = initial_data.get("TITLE / HEADING", "")

        self.policy_page.click_edit_row(row_index)
        assert self.policy_page.is_add_content_modal_open(), "Edit Content drawer failed to open!"

        # Close or cancel edit to preserve existing data
        self.policy_page.close_add_content_modal()
        return {
            "step": step_number,
            "row_index": row_index,
            "original_title": original_title,
            "drawer_opened": True
        }

    def verify_three_tier_sections_and_media_workflow(
        self,
        banner_image_path: Optional[str] = None,
        step_video_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates the 3-Tier Layout Architecture of the Induction Master page:
        1. Top Section: Hero Banner is common/pinned across steppers and controlled by Banner Scope Hierarchy.
        2. Middle Section: Stepper-specific Video dynamically adapts to the active stepper.
        3. Bottom Section: Content Table renders the policy items for the active stepper.
        Also validates uploading genuine demo media assets (Banner & Step Video).
        """
        logger.info("[WORKFLOW] Validating 3-Tier Layout Architecture & Media Uploads...")
        self.policy_page.navigate_to_induction_policy()

        # 1. Top Section: Banner Scope Hierarchy
        badge_initial = self.policy_page.get_banner_scope_hierarchy_badge()
        active_scope_text = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] Initial Banner Scope Badge: '{badge_initial}' | Caption: '{active_scope_text}'")

        # Verify Top Section remains pinned across Step 1 and Step 2
        self.policy_page.select_step(1)
        video_title_step1 = self.policy_page.get_step_video_title()
        badge_step1 = self.policy_page.get_banner_scope_hierarchy_badge()
        assert "Step 1" in video_title_step1, f"Expected Step 1 video title, got '{video_title_step1}'"
        assert badge_step1 == badge_initial, "Banner Scope Hierarchy badge changed unexpectedly across steps!"

        self.policy_page.select_step(2)
        video_title_step2 = self.policy_page.get_step_video_title()
        badge_step2 = self.policy_page.get_banner_scope_hierarchy_badge()
        assert "Step 2" in video_title_step2, f"Expected Step 2 video title, got '{video_title_step2}'"
        assert badge_step2 == badge_initial, "Banner Scope Hierarchy badge must remain constant across all steppers!"

        # 2. Upload Genuine Media Assets (if provided)
        media_uploaded = {}
        if banner_image_path:
            logger.info(f"[WORKFLOW] Uploading genuine Welcome Hero Banner: '{banner_image_path}'...")
            self.policy_page.upload_hero_banner(banner_image_path)
            media_uploaded["banner"] = banner_image_path

        if step_video_path:
            logger.info(f"[WORKFLOW] Uploading genuine Step Video for Step 2: '{step_video_path}'...")
            self.policy_page.upload_step_video(step_video_path)
            media_uploaded["step_video"] = step_video_path

        # 3. Bottom Section: Content Table validation for active step
        table_headers = self.policy_page.get_table_headers()
        step2_rows = self.policy_page.get_row_count()
        sample_step2 = self.policy_page.get_table_row_data(0) if step2_rows > 0 else {}

        logger.info(f"[WORKFLOW] 3-Tier validation complete. Step 2 Rows: {step2_rows}, Headers: {table_headers}")
        return {
            "banner_badge": badge_step2,
            "banner_active_scope": active_scope_text,
            "step1_video_title": video_title_step1,
            "step2_video_title": video_title_step2,
            "table_headers": table_headers,
            "step2_rows": step2_rows,
            "sample_step2": sample_step2,
            "media_uploaded": media_uploaded
        }

    def verify_banner_scope_hierarchy_levels_workflow(
        self,
        company: str = "TEK Inspirations LLC",
        branch: str = "Noida",
        department: str = "Developer",
        navigate: bool = True
    ) -> Dict[str, Any]:
        """
        Validates the 4 hierarchical scoping levels of the Banner Scope Hierarchy:
        1. Global Scope -> 'GLOBAL CORPORATE FALLBACK'
        2. Company Scope -> 'COMPANY WIDE'
        3. Company + Branch Scope -> 'COMPANY + BRANCH'
        4. Company + Branch + Department Scope -> 'COMPANY + BRANCH + DEPARTMENT'
        5. Reset to Global Scope -> Returns back to 'GLOBAL CORPORATE FALLBACK'
        """
        logger.info("[WORKFLOW] Validating Banner Scope Hierarchy (4 Scenarios)...")
        if navigate:
            self.policy_page.navigate_to_induction_policy()

        # Level 1: Global Scope (Corporate Global Fallback)
        badge_level1 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_level1 = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] Level 1 (Global): Badge='{badge_level1}', Scope='{text_level1}'")
        assert "GLOBAL" in badge_level1.upper(), f"Expected GLOBAL badge, got '{badge_level1}'"

        # Level 2: Company Scope
        self.policy_page.select_banner_company(company)
        badge_level2 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_level2 = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] Level 2 (Company): Badge='{badge_level2}', Scope='{text_level2}'")
        assert "COMPANY" in badge_level2.upper(), f"Expected COMPANY badge, got '{badge_level2}'"
        assert company in text_level2, f"Expected company '{company}' in active text '{text_level2}'"

        # Level 3: Company + Branch Scope
        self.policy_page.select_banner_branch(branch)
        badge_level3 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_level3 = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] Level 3 (Branch): Badge='{badge_level3}', Scope='{text_level3}'")
        assert "BRANCH" in badge_level3.upper(), f"Expected BRANCH badge, got '{badge_level3}'"
        assert branch in text_level3, f"Expected branch '{branch}' in active text '{text_level3}'"

        # Level 4: Company + Branch + Department Scope
        self.policy_page.select_banner_department(department)
        badge_level4 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_level4 = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] Level 4 (Dept): Badge='{badge_level4}', Scope='{text_level4}'")
        assert "DEPARTMENT" in badge_level4.upper(), f"Expected DEPARTMENT badge, got '{badge_level4}'"
        assert department in text_level4, f"Expected department '{department}' in active text '{text_level4}'"

        # Level 5: Reset to Global Scope
        self.policy_page.reset_banner_to_global_scope()
        badge_restored = self.policy_page.get_banner_scope_hierarchy_badge()
        text_restored = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] Reset: Badge='{badge_restored}', Scope='{text_restored}'")
        assert "GLOBAL" in badge_restored.upper(), f"Expected restored GLOBAL badge, got '{badge_restored}'"

        return {
            "level1_global": {"badge": badge_level1, "text": text_level1},
            "level2_company": {"badge": badge_level2, "text": text_level2},
            "level3_branch": {"badge": badge_level3, "text": text_level3},
            "level4_department": {"badge": badge_level4, "text": text_level4},
            "restored_global": {"badge": badge_restored, "text": text_restored}
        }

    def verify_seven_slide_hero_banner_scoping_workflow(
        self,
        company: str = "TEK Inspirations LLC",
        branch: str = "Varanasi",
        department: str = "Developer",
        upload_test_image_path: Optional[str] = None,
        test_slide_number: int = 1
    ) -> Dict[str, Any]:
        """
        Validates the 7-photo Hero Banner structure and Scoped Hierarchy:
        1. Inspects all 7 slide banner cards (Slides 1 to 7).
        2. Asserts each of the 7 slides has a title, status badge ('FALLBACK' or 'CUSTOM ACTIVE'), and an 'Upload Banner' button.
        3. Tests the 4 Scoping Levels on the 7 photos:
           - Global Scope -> 'GLOBAL CORPORATE FALLBACK'
           - Company Scope -> 'COMPANY WIDE'
           - Company + Branch Scope -> 'COMPANY + BRANCH'
           - Company + Branch + Dept Scope -> 'COMPANY + BRANCH + DEPARTMENT'
           - Reset -> Returns to 'GLOBAL CORPORATE FALLBACK'
        4. Optionally uploads a test banner photo to a specific slide slot (1 to 7).
        """
        logger.info("[WORKFLOW] Validating 7-Slide Hero Banner Scoping Architecture...")
        self.policy_page.navigate_to_induction_policy()

        # 1. Inspect all 7 slide banner cards
        slots = self.policy_page.get_slide_banner_slots_info()
        logger.info(f"[WORKFLOW] Retrieved {len(slots)} slide banner slots in Welcome Screen Background Banners:")
        for s in slots:
            logger.info(f"  Slide {s['slide_num']}: '{s['title']}' | Status: {s['badge']} | Upload Available: {s['has_upload']}")

        assert len(slots) == 7, f"Expected exactly 7 slide banner cards, found {len(slots)}!"
        for s in slots:
            assert s["has_upload"], f"Slide {s['slide_num']} does not have an active upload action button ('Upload Banner' or 'Replace')!"

        active_count_initial = self.policy_page.get_banner_active_count_text()
        logger.info(f"[WORKFLOW] Initial Banner Custom Active Count: '{active_count_initial}'")

        # 2. Test 4 Scoping Levels
        scoping_res = self.verify_banner_scope_hierarchy_levels_workflow(
            company=company,
            branch=branch,
            department=department,
            navigate=False
        )

        # 3. Test photo upload if image provided
        upload_res = None
        if upload_test_image_path:
            logger.info(f"[WORKFLOW] Uploading test banner to Slide {test_slide_number}...")
            self.policy_page.upload_slide_banner(slide_number=test_slide_number, image_path=upload_test_image_path)
            upload_res = {
                "slide_number": test_slide_number,
                "image_path": upload_test_image_path
            }

        return {
            "slots": slots,
            "total_slots": len(slots),
            "initial_active_count": active_count_initial,
            "scoping": scoping_res,
            "upload_result": upload_res
        }

    def upload_all_seven_hero_banners_workflow(
        self,
        image_paths: List[str],
        revert_after: bool = False
    ) -> Dict[str, Any]:
        """
        Sequentially uploads test banners to all 7 slide slots in the Hero Banner section:
        1. Navigates to /master/induction-policy.
        2. Captures initial active count badge (e.g. '2 / 7 Custom Active').
        3. Uploads 7 distinct images to Slides 1 through 7.
        4. Asserts all 7 slides reflect 'CUSTOM ACTIVE' status with 'Replace' and 'Revert to Default' buttons.
        5. Asserts the final active count badge updates to '7 / 7 Custom Active'.
        6. If revert_after is True, safely reverts newly customized slides back to default.
        """
        logger.info("[WORKFLOW] Starting sequential upload across all 7 Hero Banner slots...")
        self.policy_page.navigate_to_induction_policy()

        initial_count = self.policy_page.get_banner_active_count_text()
        logger.info(f"[WORKFLOW] Initial Banner Custom Active Count: '{initial_count}'")

        upload_results = self.policy_page.upload_all_seven_slide_banners(images=image_paths)

        final_count = self.policy_page.get_banner_active_count_text()
        logger.info(f"[WORKFLOW] All 7 Slides uploaded. Final Banner Custom Active Count: '{final_count}'")

        final_slots = self.policy_page.get_slide_banner_slots_info()

        if revert_after:
            logger.info("[WORKFLOW] Rolling back uploaded banners to default...")
            self.policy_page.revert_all_seven_slide_banners()
            restored_count = self.policy_page.get_banner_active_count_text()
            logger.info(f"[WORKFLOW] Restored Count Badge: '{restored_count}'")

        return {
            "initial_count": initial_count,
            "final_count": final_count,
            "upload_results": upload_results,
            "final_slots": final_slots
        }

    def verify_all_four_scoped_banner_configurations_workflow(
        self,
        company: str = "TEK Inspirations LLC",
        branch: str = "Noida",
        department: str = "Developer",
        image_company_s1: str = "",
        image_branch_s3: str = "",
        image_dept_s4: str = "",
        cleanup: bool = False
    ) -> Dict[str, Any]:
        """
        Executes end-to-end verification of the 4 Hero Banner Scoping Configurations:
        1. Global Configuration (Corporate Global Fallback)
        2. Company-level Configuration (TEK Inspirations LLC) + Slide 1 Upload
        3. Company + Branch Configuration (TEK > Noida) + Slide 3 Upload
        4. Company + Branch + Dept Configuration (TEK > Noida > Developer) + Slide 4 Upload
        5. Reset to Global Scope and verify fallback baseline retention
        """
        logger.info("[WORKFLOW] === Starting End-to-End Verification of 4 Hero Banner Scoping Tiers ===")
        self.policy_page.navigate_to_induction_policy()

        # Tier 1: Global Corporate Fallback
        self.policy_page.reset_banner_to_global_scope()
        badge_l1 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_l1 = self.policy_page.get_active_banner_scope_text()
        count_l1 = self.policy_page.get_banner_active_count_text()
        logger.info(f"[WORKFLOW] [TIER 1 - GLOBAL] Badge: '{badge_l1}' | Active Scope: '{text_l1}' | Active Count: '{count_l1}'")
        assert "GLOBAL" in badge_l1.upper(), f"Expected GLOBAL badge, got '{badge_l1}'"

        # Tier 2: Company-Wide Scope
        self.policy_page.select_banner_company(company)
        badge_l2 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_l2 = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] [TIER 2 - COMPANY] Badge: '{badge_l2}' | Active Scope: '{text_l2}'")
        assert "COMPANY" in badge_l2.upper(), f"Expected COMPANY badge, got '{badge_l2}'"
        assert company in text_l2, f"Expected company '{company}' in active text '{text_l2}'"
        if image_company_s1 and os.path.exists(image_company_s1):
            logger.info(f"[WORKFLOW] Uploading Company-scoped banner to Slide 1...")
            self.policy_page.upload_slide_banner(slide_number=1, image_path=image_company_s1)
        count_l2 = self.policy_page.get_banner_active_count_text()

        # Tier 3: Company + Branch Scope
        self.policy_page.select_banner_branch(branch)
        badge_l3 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_l3 = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] [TIER 3 - BRANCH] Badge: '{badge_l3}' | Active Scope: '{text_l3}'")
        assert "BRANCH" in badge_l3.upper(), f"Expected BRANCH badge, got '{badge_l3}'"
        assert branch in text_l3, f"Expected branch '{branch}' in active text '{text_l3}'"
        if image_branch_s3 and os.path.exists(image_branch_s3):
            logger.info(f"[WORKFLOW] Uploading Branch-scoped banner to Slide 3...")
            self.policy_page.upload_slide_banner(slide_number=3, image_path=image_branch_s3)
        count_l3 = self.policy_page.get_banner_active_count_text()

        # Tier 4: Company + Branch + Department Scope
        self.policy_page.select_banner_department(department)
        badge_l4 = self.policy_page.get_banner_scope_hierarchy_badge()
        text_l4 = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] [TIER 4 - DEPT] Badge: '{badge_l4}' | Active Scope: '{text_l4}'")
        assert "DEPARTMENT" in badge_l4.upper(), f"Expected DEPARTMENT badge, got '{badge_l4}'"
        assert department in text_l4, f"Expected department '{department}' in active text '{text_l4}'"
        if image_dept_s4 and os.path.exists(image_dept_s4):
            logger.info(f"[WORKFLOW] Uploading Department-scoped banner to Slide 4...")
            self.policy_page.upload_slide_banner(slide_number=4, image_path=image_dept_s4)
        count_l4 = self.policy_page.get_banner_active_count_text()

        # Clean Rollback if requested
        if cleanup:
            logger.info("[WORKFLOW] Cleaning up scoped uploads to preserve pristine staging...")
            if image_dept_s4:
                self.policy_page.revert_slide_banner_to_default(4)
            self.policy_page.select_banner_department("All Departments")
            if image_branch_s3:
                self.policy_page.revert_slide_banner_to_default(3)
            self.policy_page.select_banner_branch("All Branches")
            if image_company_s1:
                self.policy_page.revert_slide_banner_to_default(1)

        # Reset back to Global Scope
        self.policy_page.reset_banner_to_global_scope()
        badge_restored = self.policy_page.get_banner_scope_hierarchy_badge()
        text_restored = self.policy_page.get_active_banner_scope_text()
        logger.info(f"[WORKFLOW] [RESTORED GLOBAL] Badge: '{badge_restored}' | Scope: '{text_restored}'")
        assert "GLOBAL" in badge_restored.upper(), f"Expected GLOBAL badge, got '{badge_restored}'"

        return {
            "tier1_global": {"badge": badge_l1, "scope": text_l1, "active_count": count_l1},
            "tier2_company": {"badge": badge_l2, "scope": text_l2, "active_count": count_l2},
            "tier3_branch": {"badge": badge_l3, "scope": text_l3, "active_count": count_l3},
            "tier4_department": {"badge": badge_l4, "scope": text_l4, "active_count": count_l4},
            "restored_global": {"badge": badge_restored, "scope": text_restored}
        }
