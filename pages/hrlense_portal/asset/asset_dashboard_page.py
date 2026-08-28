import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class AssetDashboardPage(BasePage):
    """
    Page Object Model for HRlens Asset Dashboard & Stock Overview:
    - /asset-dashboard (Overview metrics, charts & 30-day warranty alerts)
    - /asset-stock (Stock counters: Total Assets, Available, Assigned, Maintenance, Damaged)
    """

    def navigate_to_asset_dashboard(self):
        """Navigates directly to the Asset Dashboard page (/asset-dashboard)."""
        logger.info("Navigating to Asset Dashboard (/asset-dashboard)")
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-dashboard", timeout=20000)
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1000)
            return
        except Exception:
            pass

        try:
            link = self.page.locator("a").filter(has_text=re.compile(r"Asset Dashboard", re.I)).first
            if link.is_visible(timeout=3000):
                link.click()
                self.page.wait_for_load_state("domcontentloaded")
                self.page.wait_for_timeout(1000)
        except Exception as e:
            logger.warning(f"Fallback navigation note: {e}")

    def navigate_to_asset_stock(self):
        """Navigates directly to the Asset Stock page (/asset-stock)."""
        logger.info("Navigating to Asset Stock (/asset-stock)")
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-stock", timeout=20000)
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1000)
            return
        except Exception:
            pass

        try:
            link = self.page.locator("a").filter(has_text=re.compile(r"Asset Stock|Stock", re.I)).first
            if link.is_visible(timeout=3000):
                link.click()
                self.page.wait_for_load_state("domcontentloaded")
                self.page.wait_for_timeout(1000)
        except Exception as e:
            logger.warning(f"Fallback navigation note: {e}")

    def get_stock_metrics(self) -> dict:
        """
        Extracts stock metrics cards from the Asset Stock or Asset Dashboard.
        Looks for Total Assets, Available, Assigned, Maintenance, Damaged counters.
        """
        logger.info("Extracting stock metric cards from page...")
        metrics = {}
        try:
            cards = self.page.locator("div.chakra-stat, div[class*='stat'], div[class*='card'], .chakra-stack, table tbody tr").all()
            for card in cards:
                txt = card.inner_text().strip()
                if not txt:
                    continue
                for label in ["Total Assets", "Available", "Assigned", "Under Maintenance", "Maintenance", "Damaged", "Scrapped", "Sold"]:
                    if label.lower() in txt.lower():
                        nums = re.findall(r"\b\d+\b", txt)
                        if nums:
                            metrics[label] = nums[-1]
                        else:
                            metrics[label] = txt.replace("\n", " ")
        except Exception as e:
            logger.warning(f"Stock metrics parsing note: {e}")

        logger.info(f"Captured Stock Metrics: {metrics}")
        return metrics

    def get_warranty_alert_banner(self) -> str:
        """Reads 30-Day Warranty alert notification banner or section on the dashboard."""
        candidates = [
            self.page.locator(".chakra-alert, [role='alert']").first,
            self.page.locator("div:has(> p):has-text('warranty'), p:has-text('warranty')").first,
            self.page.locator("div:has-text('Warranty Expiry'), div:has-text('Expiring Soon'), div:has-text('Repair / Damage')").first
        ]
        for loc in candidates:
            try:
                if loc.is_visible(timeout=1500):
                    raw = loc.inner_text().strip()
                    for line in raw.split("\n"):
                        if any(w in line.lower() for w in ["warranty", "expir", "repair", "damage", "day"]):
                            return line.strip()
                    return raw[:100]
            except Exception:
                continue
        return "Dashboard active"

    def get_warranty_expiring_soon_count(self) -> int:
        """
        Extracts the exact 'Expiring Soon' counter from the 'Warranty Expiring Soon' card on /asset-dashboard.
        HTML target:
        <p class="chakra-text">Warranty Expiring Soon</p>
        <div class="css-0">
            <p class="chakra-text">Expiring Soon</p>
            <p class="chakra-text">N</p>
            <p class="chakra-text">expiring within 30 days</p>
        </div>
        """
        logger.info("Reading 'Expiring Soon' warranty counter on /asset-dashboard...")
        self.navigate_to_asset_dashboard()

        card_locators = [
            self.page.locator("div:has(> p:text('Expiring Soon')):has(p:text('expiring within 30 days'))"),
            self.page.locator("div:has(p:has-text('Warranty Expiring Soon'))"),
            self.page.locator("div:has(p:has-text('expiring within 30 days'))")
        ]

        for card in card_locators:
            try:
                if card.is_visible(timeout=2000):
                    # Find all paragraph text elements inside the card
                    p_texts = card.locator("p").all_inner_texts()
                    for t in p_texts:
                        t_clean = t.strip()
                        if t_clean.isdigit():
                            count = int(t_clean)
                            logger.info(f"Captured 'Expiring Soon' count: {count} (from card texts: {p_texts})")
                            return count
            except Exception:
                continue

        logger.info("Could not extract exact 'Expiring Soon' digit; falling back to 0")
        return 0


