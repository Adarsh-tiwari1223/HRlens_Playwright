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
    
    # Go to Absence Management
    page.goto(f"{settings.BASE_URL}/absence-management")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    
    # Print cells of the first row
    first_row = page.locator("tbody tr").first
    cells = first_row.locator("td").all()
    print("=== CELL VALUES FOR FIRST ROW ===")
    for idx, cell in enumerate(cells):
        text = cell.inner_text().strip()
        print(f"Cell {idx}: '{text}'")
        
    browser.close()
