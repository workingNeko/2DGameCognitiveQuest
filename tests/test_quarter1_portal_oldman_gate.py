import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.main_menu import MainMenu
from screens.quarter1 import Quarter1
from db.save_system import mark_quarter_completed, save_student_progress, load_student_progress, apply_student_progress

def test_portal_gated_by_oldman():
    mm = MainMenu(screen)
    mm.student_id = "1"
    mm.selected_student = {"id": 9, "student_id": "1", "first_name": "Jessuny Dado"}
    
    q1 = Quarter1(screen, mm, "map1.txt")
    if hasattr(q1, 'instruction_modal'):
        q1.instruction_modal.hide()
    mm.quarter1 = q1
    mm.current_screen = "quarter1"

    # 1. Answer all 5 shape questions
    for s in q1.shape_npcs.values():
        s["answered"] = True
    q1.quiz_station_index = 6
    q1.spawn_portals()

    # Verify Old Man puzzle is not yet solved
    assert not q1.puzzle_solved, "Old Man puzzle should not be solved yet"

    # Find the goal portal
    portal = q1.portals[0] if q1.portals else None
    assert portal is not None, "Map 1 should have a portal"

    # Move player directly onto the portal
    q1.player_x = portal.get_center_x() - 16
    q1.player_y = portal.get_center_y() - 16
    q1.teleport_cooldown = 0

    # Attempt to trigger portal teleport
    teleport_result = q1.check_portal_teleport_on_hold()

    # MUST be blocked because Old Man puzzle is not solved!
    assert teleport_result is False, "Portal should NOT activate before Old Man puzzle is solved!"
    assert q1.bridge_warning_message != "", "Warning banner should be displayed!"
    assert q1.quiz_state == 22, f"Old Man puzzle intro dialog should open! Got quiz_state={q1.quiz_state}"
    print("[PASS] Portal is strictly gated by Old Man puzzle on Map 1!")

    # 2. Simulate solving the Forest Keystone Jigsaw puzzle
    q1.init_puzzle()
    for p in q1.puzzle_pieces:
        p["is_placed"] = True
    q1.puzzle_solved = True
    q1.quiz_state = 0
    q1.teleport_cooldown = 0

    # 3. Now step on the portal again
    teleport_result_after = q1.check_portal_teleport_on_hold()
    assert teleport_result_after is True, "Portal SHOULD activate after Old Man puzzle is solved!"
    assert q1.warp_out_active is True, "Warp transition should be active!"
    print("[PASS] Portal successfully opens after solving Old Man puzzle!")

    # 4. Finish warp transition and trigger victory card
    q1.warp_out_timer = 0
    q1.update()
    assert q1.victory_card.active is True, "Victory card should be displayed!"
    print("[PASS] Victory card modal opened upon completing Quarter 1!")

    # 5. Click 'Continue to Hub' on Victory Card
    q1.victory_card.handle_click(q1.victory_card.continue_rect.center)
    assert mm.current_screen == "stage_select", f"Should return to stage_select! Got {mm.current_screen}"
    assert mm.stage_select is not None, "StageSelect screen should be created!"
    print("[PASS] Victory card Continue to Hub button transitions smoothly to Stage Select!")

def test_continue_activity_from_menu():
    mm = MainMenu(screen)
    mm.student_id = "1"
    mm.selected_student = {"id": 9, "student_id": "1", "first_name": "Jessuny Dado"}
    
    # Save student with current_screen = "menu"
    mark_quarter_completed(mm, "quarter1", score=100)
    save_student_progress(mm)

    save_data = load_student_progress("1")
    assert save_data.get("current_screen") == "menu"

    # Click CONTINUE ACTIVITY from menu
    mm.continue_activity()
    assert mm.current_screen == "stage_select", f"Continue Activity should launch stage_select! Got {mm.current_screen}"
    assert mm.stage_select is not None, "StageSelect instance should be active!"
    print("[PASS] Main Menu Continue Activity button reliably launches Stage Select!")

if __name__ == "__main__":
    test_portal_gated_by_oldman()
    test_continue_activity_from_menu()
    print("\nALL QUARTER 1 GATING & CONTINUE TESTS PASSED!")
