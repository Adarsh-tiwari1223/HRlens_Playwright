import sys
import os
sys.path.append(os.getcwd())

from playwright.sync_api import sync_playwright
from core.config import settings

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(settings.BASE_URL)
    
    # Login
    from pages.login_page import LoginPage
    LoginPage(page).login(
        settings.USERS["admin"]["username"],
        settings.USERS["admin"]["password"]
    )
    page.wait_for_load_state("networkidle")
    
    # Go to settings
    page.goto(f"{settings.BASE_URL}/absence-settings")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    
    # Print headings/labels and their parent divs
    elements = page.locator("p, div, label, dt").all()
    print("=== SEARCHING FOR SETTINGS LABELS ===")
    for el in elements:
        try:
            text = el.inner_text().strip()
            if "Continuous" in text or "Attempts" in text:
                tag = el.evaluate("node => node.tagName")
                print(f"Tag: {tag}, Text: '{text[:100]}'")
        except Exception:
            continue
            
    browser.close()
