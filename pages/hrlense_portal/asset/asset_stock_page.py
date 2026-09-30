"""
Page Object Model for HRlens Portal - Stock Manager (/asset-stock).

Represents the Stock Manager page which displays:
- Total assets and branch overview header
- Left-side branch selection panel with branch asset and availability counters
- 7 Stock Status Cards: All Assets, Available, Assigned, Reserved, Maintenance, Damaged, Insured
- Category quick filter buttons
- Search bar, columns toggler, asset inventory data table, and pagination controls
"""

import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetStockPage(BasePage):
    """Page Object for /asset-stock (Stock Manager)."""

    def navigate_to_asset_stock(self):
        """Navigates directly to the Asset Stock page (/asset-stock)."""
        logger.info("Navigating to Asset Stock (/asset-stock)")
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-stock", timeout=20000)
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1500)
            return
        except Exception:
            pass

        try:
            link = self.page.locator("a").filter(has_text=re.compile(r"Asset Stock|Stock Manager|Stock", re.I)).first
            if link.is_visible(timeout=3000):
                link.click()
                self.page.wait_for_load_state("domcontentloaded")
                self.page.wait_for_timeout(1500)
        except Exception as e:
            logger.warning(f"Fallback navigation note: {e}")

    def get_stock_header_info(self) -> dict:
        """
        Reads the Stock Manager header banner.
        Example: 'Stock Manager' | '200 assets across 10 branches'
        """
        info = {"title": "", "subtitle": "", "total_assets": None, "total_branches": None}
        try:
            title_el = self.page.locator("p").filter(has_text=re.compile(r"^Stock Manager$", re.I)).first
            if title_el.is_visible(timeout=2000):
                info["title"] = title_el.inner_text().strip()

            sub_el = self.page.locator("p").filter(has_text=re.compile(r"\d+\s+assets\s+across\s+\d+\s+branches", re.I)).first
            if sub_el.is_visible(timeout=2000):
                sub_text = sub_el.inner_text().strip()
                info["subtitle"] = sub_text
                m = re.search(r"(\d+)\s+assets\s+across\s+(\d+)\s+branches", sub_text, re.I)
                if m:
                    info["total_assets"] = int(m.group(1))
                    info["total_branches"] = int(m.group(2))
        except Exception as e:
            logger.warning(f"Error reading header info: {e}")

        logger.info(f"[STOCK HEADER] {info}")
        return info

    def get_branch_list(self) -> list[dict]:
        """
        Reads all branches listed on the left panel (Available for IT Admin and Admin only).
        Returns an empty list for Branch IT users who are strictly scoped to their own branch without a cross-branch filter.
        """
        branches = []
        try:
            panel = self.page.locator(".css-hrv7b2, div:has(> p:text('BRANCHES'))").first
            if not panel.is_visible(timeout=1500):
                logger.info("[STOCK BRANCHES] Branch filter panel not present (Branch-scoped IT user view).")
                return []

            branch_buttons = panel.locator("button").all()
            for btn in branch_buttons:
                txt = btn.inner_text().strip()
                if not txt:
                    continue
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                b_name = lines[0] if lines else ""
                
                assets_num = None
                avail_num = None
                m_asset = re.search(r"(\d+)\s+assets?", txt, re.I)
                m_avail = re.search(r"(\d+)\s+avail", txt, re.I)
                if m_asset:
                    assets_num = int(m_asset.group(1))
                if m_avail:
                    avail_num = int(m_avail.group(1))

                if b_name:
                    branches.append({
                        "name": b_name,
                        "assets": assets_num,
                        "available": avail_num,
                        "raw_text": txt
                    })
        except Exception as e:
            logger.warning(f"Error reading branch list: {e}")

        logger.info(f"[STOCK BRANCHES] Found {len(branches)} branches: {[b['name'] for b in branches]}")
        return branches

    def select_branch(self, branch_name: str = "Varanasi"):
        """
        Clicks the specified branch button on the left panel if available (Admin / IT Admin view).
        For Branch IT users, their assigned branch is already default and active.
        """
        logger.info(f"Ensuring active branch: '{branch_name}' on /asset-stock")
        panel = self.page.locator(".css-hrv7b2, div:has(> p:text('BRANCHES'))").first
        if panel.is_visible(timeout=1500):
            branch_btn = panel.locator("button").filter(
                has=self.page.locator("p", has_text=re.compile(rf"^{re.escape(branch_name)}$", re.I))
            ).first
            if branch_btn.is_visible(timeout=2000):
                branch_btn.click(force=True)
                self.page.wait_for_timeout(1000)
                return

        # Check dropdown filter if present (Admin / IT Admin view)
        select_el = self.page.locator("select.chakra-select").filter(has=self.page.locator(f"option:has-text('{branch_name}')")).first
        if select_el.is_visible(timeout=1500):
            select_el.select_option(label=branch_name)
            self.page.wait_for_timeout(1000)

    def is_branch_filter_visible(self) -> bool:
        """Checks if the cross-branch filter is visible (Admin / IT Admin only)."""
        panel = self.page.locator(".css-hrv7b2, div:has(> p:text('BRANCHES'))").first
        dropdown = self.page.locator("select.chakra-select").filter(has=self.page.locator("option:has-text('Varanasi')")).first
        return panel.is_visible(timeout=1500) or dropdown.is_visible(timeout=1500)

    def get_stock_cards(self, branch_name: str = "Varanasi") -> dict[str, int]:
        """
        Reads the 7 stock status metric buttons for the active branch:
        - All Assets
        - Available
        - Assigned
        - Reserved
        - Maintenance
        - Damaged
        - Insured
        """
        if branch_name:
            self.select_branch(branch_name)

        # Wait for cards to render
        try:
            self.page.locator("button").filter(
                has=self.page.locator("p", has_text=re.compile(r"^All Assets$", re.I))
            ).first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

        metrics = {}
        expected_cards = ["All Assets", "Available", "Assigned", "Reserved", "Maintenance", "Damaged", "Insured"]

        for card_name in expected_cards:
            btn = self.page.locator("button").filter(
                has=self.page.locator("p", has_text=re.compile(rf"^{card_name}$", re.I))
            ).first
            if btn.is_visible(timeout=2000):
                p_texts = btn.locator("p").all_inner_texts()
                for pt in p_texts:
                    pt_clean = pt.strip()
                    if pt_clean.isdigit():
                        metrics[card_name] = int(pt_clean)
                        break

        logger.info(f"[STOCK CARDS] Branch: '{branch_name}' -> {metrics}")
        return metrics

    def get_category_filters(self) -> list[str]:
        """Extracts available category quick-filter button labels (e.g. 'All Categories', 'IT Hardware · 2')."""
        cats = []
        try:
            cat_container = self.page.locator(".chakra-stack").filter(
                has=self.page.locator("button", has_text=re.compile(r"All Categories", re.I))
            ).first
            if cat_container.is_visible(timeout=2000):
                buttons = cat_container.locator("button").all()
                cats = [b.inner_text().strip() for b in buttons if b.inner_text().strip()]
        except Exception as e:
            logger.warning(f"Error reading category filters: {e}")
        return cats

    def search_asset(self, query: str):
        """Fills the search input above the asset table."""
        search_in = self.page.locator("input[placeholder*='Search code, name, serial' i], input[placeholder*='Search' i]").first
        if search_in.is_visible(timeout=2000):
            search_in.fill("")
            search_in.fill(query)
            search_in.press("Enter")
            self.page.wait_for_timeout(800)

    def get_table_asset_rows(self) -> list[dict]:
        """Extracts visible rows from the asset stock data table."""
        rows = []
        try:
            tr_locators = self.page.locator("table tbody tr").all()
            for tr in tr_locators:
                tds = [td.inner_text().strip() for td in tr.locator("td").all()]
                if tds and len(tds) >= 5:
                    rows.append({
                        "code": tds[0],
                        "name": tds[1],
                        "category": tds[2],
                        "serial_no": tds[3],
                        "status": tds[4],
                        "assigned_to": tds[5] if len(tds) > 5 else "—"
                    })
        except Exception as e:
            logger.warning(f"Error reading table rows: {e}")
        return rows

    def get_pagination_summary(self) -> str:
        """Reads pagination text, e.g. 'Showing 1-20 of 20 records'."""
        try:
            text_el = self.page.locator("p").filter(has_text=re.compile(r"Showing\s+\d+-\d+\s+of\s+\d+\s+records", re.I)).first
            if text_el.is_visible(timeout=2000):
                return text_el.inner_text().strip()
        except Exception:
            pass
        return ""
