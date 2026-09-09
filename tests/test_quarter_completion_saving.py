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
from screens.studentselect import StudentSelect
from db.save_system import (
    mark_quarter_completed,
    load_student_progress,
    save_student_progress,
    get_completed_quarters,
    delete_student_progress,
    check_save_exists
)
from db.connect_db import db

def test_quarter_completion_saving():
    print("=== Testing Quarter Completion Saving & Persistence ===")
    
    # 1. Initialize Main Menu with student
    mm = MainMenu(screen)
    student = {
        "id": 9,
        "student_id": "1",
        "first_name": "Jessuny",
        "last_name": "Dado",
        "score": 0,
        "progress": 0,
        "level": "Grade 2",
        "gender": "male"
    }
    mm.selected_student = dict(student)
    mm.student_id = "1"
    mm.student_db_id = 9
    
    # Clean start
    delete_student_progress("1", 9, mm)
    assert check_save_exists("1") is False, "Fresh start should have no save data"

    # 2. Simulate completing Quarter 1
    q1 = Quarter1(screen, mm, "map1.txt")
    mm.quarter1 = q1
    mm.current_screen = "quarter1"
    for s in q1.shape_npcs.values():
        s["answered"] = True
    q1.oldman_riddle_answered = True
    
    # Mark completion
    mark_quarter_completed(mm, "quarter1", score=100, percentage=100.0, total_questions=5)

    # 3. Verify save file updated with score, progress, and completed_quarters
    save_data = load_student_progress("1")
    assert save_data is not None, "Save file must exist after mark_quarter_completed!"
    assert "quarter1" in save_data.get("completed_quarters", {}), "Quarter 1 must be marked completed!"
    assert save_data["completed_quarters"]["quarter1"]["completed"] is True
    assert save_data["selected_student"]["score"] == 100, f"Expected 100 pts, got {save_data['selected_student']['score']}"
    assert save_data["selected_student"]["progress"] == 25, f"Expected 25%, got {save_data['selected_student']['progress']}"
    assert mm.selected_student["score"] == 100, "In-memory selected_student must be updated!"
    assert mm.selected_student["progress"] == 25, "In-memory selected_student progress must be updated!"
    print("[PASS] Persistent save file and in-memory student updated with 100 pts and 25% progress!")

    # 4. Finish and return to hub
    q1.finish_and_return_to_hub()
    assert mm.current_screen == "stage_select", f"Should return to stage_select! Got {mm.current_screen}"
    assert mm.stage_select is not None, "StageSelect must be active"
    assert mm.stage_select.is_quarter_completed("quarter1") is True, "StageSelect must recognize Q1 is cleared"
    assert mm.stage_select.is_quarter_unlocked("quarter2") is True, "StageSelect must recognize Q2 is unlocked"
    print("[PASS] StageSelect correctly marks Quarter 1 as CLEARED and Quarter 2 as OPEN!")

    # 5. Press ESC to return to Main Menu
    esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    mm.stage_select.handle_event(esc_event)
    assert mm.current_screen == "menu", f"Expected menu screen, got {mm.current_screen}"
    
    # Verify main menu buttons reconfigured to show CONTINUE ACTIVITY
    btn_texts = [b.text for b in mm.buttons]
    assert "CONTINUE ACTIVITY" in btn_texts, f"Main Menu must show CONTINUE ACTIVITY! Found: {btn_texts}"
    assert "START NEW ACTIVITY" in btn_texts, f"Main Menu must show START NEW ACTIVITY! Found: {btn_texts}"
    print("[PASS] Returning to Menu via ESC automatically configures CONTINUE ACTIVITY button!")

    # 6. Verify StudentSelect displays real score and progress
    ss_screen = StudentSelect(screen, mm)
    matching = [s for s in ss_screen.students if str(s.get("student_id")) == "1" or str(s.get("id")) == "9"]
    assert len(matching) > 0, "Student must exist in student list"
    assert matching[0]["score"] == 100, f"Expected 100 score in StudentSelect, got {matching[0]['score']}"
    assert matching[0]["progress"] == 25, f"Expected 25% progress in StudentSelect, got {matching[0]['progress']}"
    print("[PASS] StudentSelect list displays real score (100) and progress (25%)!")

    # 7. Verify Leaderboard contains completed quarter data
    l_data = db.get_leaderboard_data()
    matching_lb = [e for e in l_data if str(e.get("student_id")) == "1" or str(e.get("id")) == "9"]
    assert len(matching_lb) > 0, "Student must exist in Leaderboard data"
    assert matching_lb[0]["quarters"][1] is not None, "Quarter 1 must be present in Leaderboard"
    assert matching_lb[0]["quarters"][1]["completed"] is True, "Quarter 1 must be marked completed in Leaderboard"
    print("[PASS] Leaderboard reflects completed quarter from persistent save!")

    # 8. Test clicking CONTINUE ACTIVITY
    mm.continue_activity()
    assert mm.current_screen == "stage_select", f"Continue Activity must load stage_select! Got {mm.current_screen}"
    assert mm.stage_select.is_quarter_unlocked("quarter2") is True, "Quarter 2 must remain unlocked upon continuing"
    print("[PASS] Continue Activity cleanly resumes Stage Select with Quarter 2 unlocked!")

    print("\nALL QUARTER COMPLETION SAVING & PERSISTENCE TESTS PASSED!")

if __name__ == "__main__":
    test_quarter_completion_saving()
