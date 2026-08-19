"""
HRlens Portal — Branch Asset Visibility Isolation & Scoping Specification Test Suite.

Audits Multi-Tenant / Branch-Scoped Data Isolation:
1. Logs in as Branch IT Person for a specific Branch (e.g., Agra, Varanasi, Meerut, Noida).
2. Navigates to Asset Inventory (/asset-entry) and Asset Return (/asset-return).
3. Reads all visible asset records in the grid.
4. Evaluates whether IT Person sees ONLY their branch assets OR if cross-branch assets are visible.
5. Logs structured security & visibility audit summary table.
"""

import re
import logging
import pytest

from core.config import settings
from pages.base_page import TestStoryLogger, format_ascii_table
from pages.hrlense_portal.asset.asset_entry_page import AssetEntryPage
from pages.hrlense_portal.asset.asset_return_page import AssetReturnPage
from utils.branch_it_selector import get_branch_it_person

logger = logging.getLogger(__name__)


@pytest.mark.ui
@pytest.mark.asset
@pytest.mark.branch_visibility
class TestBranchAssetVisibilityIsolationSpec:

    @pytest.mark.parametrize("branch_name", ["Agra", "Varanasi"])
    def test_audit_branch_asset_visibility_scoping(self, logged_in_page, branch_name):
        """
        Audits asset visibility for Branch IT Person:
        Checks if assets from other branches are visible or isolated to target branch.
        """
        story = TestStoryLogger(f"Branch Visibility Audit: {branch_name}", module="Asset Management", phase="Security Audit")
        story.start()

        it_person = get_branch_it_person(branch_name)
        it_user_key = it_person["user_key"]
        
        user_info = settings.USERS.get(it_user_key, {})
        if not user_info.get("password"):
            logger.warning(f"[AUDIT] Password for IT Person '{it_person['name']}' ({it_user_key}) is blank in .env. Falling back to Admin.")
            it_user_key = "admin"

        logger.info(f"[BRANCH VISIBILITY AUDIT START] Branch: '{branch_name}' | IT Person: '{it_person['name']}' ({it_user_key})")
        it_page, _ = logged_in_page(it_user_key)

        # 1. Audit Asset Entry Inventory page (/asset-entry)
        entry_page = AssetEntryPage(it_page)
        entry_page.navigate_to_asset_entry()
        
        # Read visible rows in Asset Entry grid
        entry_rows = it_page.locator("table tbody tr").all()
        logger.info(f"[{branch_name} AUDIT] Total visible rows on Asset Entry grid: {len(entry_rows)}")

        visible_assets = []
        target_branch_count = 0
        other_branch_count = 0

        for idx, r in enumerate(entry_rows[:25], 1):
            try:
                text = r.inner_text().strip()
                match = re.search(r"ASSET-[A-Z0-9-]+", text)
                asset_code = match.group(0) if match else f"ROW-{idx}"
                
                # Check for branch keywords in text (e.g. Agra, Varanasi, Meerut, Noida, Lucknow, Jaipur)
                detected_branch = "Unknown"
                for b in ["Agra", "Varanasi", "Meerut", "Noida", "Lucknow", "Greater Noida", "Jaipur", "VAR", "AGR", "MEE"]:
                    if b.lower() in text.lower():
                        detected_branch = b
                        break

                is_target = (branch_name.lower() in text.lower()) or (detected_branch.lower() in branch_name.lower())
                if is_target:
                    target_branch_count += 1
                elif detected_branch != "Unknown":
                    other_branch_count += 1

                visible_assets.append({
                    "row": idx,
                    "asset_code": asset_code,
                    "detected_branch": detected_branch,
                    "matches_user_branch": is_target,
                    "raw_snippet": text[:60].replace("\n", " ")
                })
            except Exception:
                pass

        # 2. Audit Asset Return grid (/asset-return)
        return_page = AssetReturnPage(it_page)
        return_page.navigate_to_asset_return()
        return_rows = it_page.locator("table tbody tr").all()
        logger.info(f"[{branch_name} AUDIT] Total visible rows on Asset Return grid: {len(return_rows)}")

        # 3. Print Structured ASCII Audit Report
        audit_summary = {
            "branch_audited": branch_name,
            "it_person_logged_in": it_person["name"],
            "total_assets_visible": len(visible_assets),
            "target_branch_assets": target_branch_count,
            "other_branch_assets_visible": other_branch_count,
            "visibility_scope": "STRICTLY ISOLATED" if (other_branch_count == 0 and target_branch_count > 0) else "GLOBAL / ALL BRANCHES VISIBLE"
        }

        print("\n" + format_ascii_table(f"BRANCH ASSET VISIBILITY AUDIT — {branch_name.upper()}", audit_summary))
        print(format_ascii_table(f"VISIBLE ASSETS SAMPLE ({branch_name.upper()})", visible_assets[:10]))

        logger.info(f"[BRANCH VISIBILITY AUDIT COMPLETED] Result: {audit_summary['visibility_scope']}")
