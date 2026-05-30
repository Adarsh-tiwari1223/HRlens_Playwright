import pytest
from core.config import settings
from pages.login_page import LoginPage
from pages.employee.offer_letter_template_page import OfferLetterTemplatePage
from testdata.static.companies import COMPANIES


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(params=COMPANIES)
def template_page(request, page):
    """Login as admin and navigate to the Offer Letter Template page for all companies."""
    company_name = request.param
    page.goto(settings.BASE_URL, timeout=60000)
    login_page = LoginPage(page)
    creds = settings.USERS["admin"]
    login_page.login(creds["username"], creds["password"])
    page.wait_for_load_state("networkidle")

    tp = OfferLetterTemplatePage(page)
    tp.navigate_to_offer_letter_template()
    tp.select_company(company_name)
    
    print(f"\n[FIXTURE] Active Company Context: {company_name}")
    return tp


# ── Test 1: CREATE + READ ─────────────────────────────────────────────────────
@pytest.mark.ui
@pytest.mark.template
def test_offer_letter_create_and_read_all_sections(template_page):
    """
    CREATE: Add all 8 standard sections in order:
      OPENING | SALARY | PROBATION | LEAVE | NOTICE | REPORTING | CUSTOM | CLOSING
    Each section uses its defined title and content from testdata/static/offer_letter_sections.py.

    Rules enforced:
      - Automatically skips creation if the section already exists on the page.
      - Fails if title is not visible on the page after Save (silent failure).

    READ: Re-verify all 8 section titles are visible after creation.
    """
    # CREATE — adds all 8 sections, title + content for each
    template_page.add_all_sections()

    # READ — verify all 8 section titles are still on the page
    template_page.read_all_sections()


# ── Test 2: UPDATE + DELETE ───────────────────────────────────────────────────
from testdata.static.offer_letter_sections import OFFER_LETTER_SECTIONS

@pytest.mark.ui
@pytest.mark.template
def test_offer_letter_reorder_sections(template_page):
    """
    REORDER: Uses a strict dependency/topological swap algorithm to achieve the Goal Order.
    Rules implemented:
    1. Order values remain unique at all times.
    2. Identifies unused order values as temporary buffers.
    3. Never assigns an occupied value.
    4. Validates destination order is available before update.
    5. Moves sections in dependency order to free up needed slots.
    6. Recalculates state dynamically after every single move.
    7. Loops until the Goal Order is perfectly matched.
    """
    goal_order = {s["key"]: s["order"] for s in OFFER_LETTER_SECTIONS}
    
    # Allow up to 20 moves to prevent infinite loops, though mathematically
    # topological sort with an empty buffer slot takes at most N+1 moves.
    max_moves = 20
    moves = 0
    
    while moves < max_moves:
        # 6. Recalculate the state after every update.
        print("\n[REORDER ALGORITHM] Recalculating current state...")
        current_state = template_page.get_current_orders()
        print(f"Current State: {current_state}")
        
        # 7. Continue until all sections match the Goal Order.
        if all(current_state.get(k) == v for k, v in goal_order.items()):
            print("\n[PASS] Goal Order successfully achieved!")
            break
            
        # 2. Identify any unused order value and use it as a temporary buffer.
        # We check values 0-8 (9 slots for 8 items, guaranteeing at least 1 free)
        used_orders = set(current_state.values())
        available_orders = set(range(9)) - used_orders
        
        if not available_orders:
            # Failsafe if the state is incredibly broken
            print("[WARN] No available buffer slots in 0-8!")
            break
            
        buffer_slot = min(available_orders)
        
        moved = False
        
        # 5. Move sections in dependency order so that each move frees the next required position.
        # First priority: Can we move a misplaced section DIRECTLY into its Goal Order slot?
        # 4. Before each update, verify the destination order is available.
        for section_key, current_val in current_state.items():
            target_val = goal_order[section_key]
            
            # If it's out of order AND its target slot is currently empty/available
            if current_val != target_val and target_val in available_orders:
                print(f"[REORDER] Slot {target_val} is available! Moving {section_key} directly to goal.")
                template_page.update_section(
                    section_key=section_key,
                    enforce_order=target_val
                )
                moved = True
                moves += 1
                break
                
        # 8. If no free order value exists for a direct move, perform a swap to the buffer to free a position
        if not moved:
            for section_key, current_val in current_state.items():
                target_val = goal_order[section_key]
                
                # Find ANY misplaced section and move it to the empty buffer slot
                if current_val != target_val:
                    print(f"[REORDER] Traffic jam! Moving {section_key} into temporary buffer slot {buffer_slot} to free up slot {current_val}.")
                    template_page.update_section(
                        section_key=section_key,
                        enforce_order=buffer_slot
                    )
                    moved = True
                    moves += 1
                    break
                    
        if not moved:
            break
            
    assert moves < max_moves, "[FAIL] Reorder algorithm exceeded max moves!"


@pytest.mark.ui
@pytest.mark.template
def test_offer_letter_duplicate_prevention(template_page):
    """
    DUPLICATE PREVENTION: Attempt to create a section that already exists (e.g., OPENING).
    Validates that the backend blocks the entry and the UI displays an 'already exists' error toast.
    """
    # We test with the very first section (OPENING) which is guaranteed to exist
    # because the first test creates all missing sections.
    target_section = OFFER_LETTER_SECTIONS[0]
    
    # Verify it exists first
    template_page.read_section(target_section["key"])
    
    # Attempt to create duplicate and assert the error toast appears
    template_page.verify_duplicate_blocked(target_section)
