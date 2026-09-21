import os
import sys
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.main_menu import MainMenu
from screens.quarter2 import Quarter2

def test_quarter2_bahay_kubo_portal_click_bounds():
    mm = MainMenu(screen)
    mm.selected_student = {
        "id": 1,
        "student_id": "1",
        "first_name": "Maria",
        "last_name": "Santos",
        "score": 0,
        "progress": 0,
        "level": "Grade 2",
        "gender": "female"
    }

    q2 = Quarter2(screen, mm, "map5.txt")
    mm.quarter2 = q2
    mm.current_screen = "quarter2"

    # Close initial instruction modal
    if q2.instruction_modal.is_visible:
        q2.instruction_modal.hide()

    # Verify Map 5 has 5 pieces for Bahay Kubo
    assert q2.map_name == "map5.txt"
    assert q2.kubo_pieces_collected == 0

    # Simulate completing all 5 stations
    q2.quiz_station_index = 5
    q2.current_question_index = 4
    q2.quiz_state = 3  # Correct dialog for station 5
    
    # Render correct dialog to set correct_btn_rect
    q2.draw_correct_dialog()
    assert q2.correct_btn_rect is not None
    
    # Click center of Continue Fiesta button in State 3
    btn_center = q2.correct_btn_rect.center
    q2.trigger_click(btn_center)

    # Should have built 5 pieces of Bahay Kubo and cleared stations for Knight Guardian
    assert q2.kubo_pieces_collected == 5
    assert q2.quiz_station_index == 6
    assert q2.guardian_knight_state == 1
    assert q2.camera_pan_active is True

    # Transition to State 5 (Victory Speech after Guardian Trial)
    q2.quiz_state = 5
    q2.draw_victory_speech()
    assert q2.victory_btn_rect is not None

    # Test clicking across multiple points on the 'Enter Portal >>' button:
    # 1. Top of button
    # 2. Exact center
    # 3. Bottom of button
    top_pos = (q2.victory_btn_rect.centerx, q2.victory_btn_rect.top + 5)
    center_pos = q2.victory_btn_rect.center
    bottom_pos = (q2.victory_btn_rect.centerx, q2.victory_btn_rect.bottom - 5)

    # Re-verify collision on all points
    assert q2.victory_btn_rect.collidepoint(top_pos)
    assert q2.victory_btn_rect.collidepoint(center_pos)
    assert q2.victory_btn_rect.collidepoint(bottom_pos)

    # Click center of Enter Portal button
    q2.trigger_click(center_pos)

    # Must transition to State 6 (Portal unlocked)
    assert q2.quiz_state == 6
    assert "GRAND FIESTA PORTAL UNLOCKED" in q2.banner_text

def test_quarter2_keyboard_space_return_advances():
    mm = MainMenu(screen)
    mm.selected_student = {
        "id": 1,
        "student_id": "1",
        "first_name": "Maria",
        "last_name": "Santos"
    }

    q2 = Quarter2(screen, mm, "map5.txt")
    if q2.instruction_modal.is_visible:
        q2.instruction_modal.hide()

    q2.quiz_station_index = 5
    q2.current_question_index = 4
    q2.quiz_state = 5  # Victory Speech

    # Simulate pressing SPACE
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    res = q2.handle_event(event)

    assert res == "handled"
    assert q2.quiz_state == 6

def test_quarter2_dialog_states_clicks():
    mm = MainMenu(screen)
    mm.selected_student = {
        "id": 1,
        "student_id": "1",
        "first_name": "Maria",
        "last_name": "Santos"
    }
    q2 = Quarter2(screen, mm, "map5.txt")
    if q2.instruction_modal.is_visible:
        q2.instruction_modal.hide()

    # Test State 2 (Wrong answer retry)
    q2.quiz_station_index = 1
    q2.current_question_index = 0
    q2.quiz_state = 2
    q2.draw_wrong_dialog()
    assert q2.wrong_btn_rect is not None
    q2.trigger_click(q2.wrong_btn_rect.center)
    assert q2.quiz_state == 1

    # Test State 4 (Out of tries reveal)
    q2.quiz_station_index = 2
    q2.current_question_index = 1
    q2.quiz_state = 4
    q2.draw_out_of_tries_dialog()
    assert q2.out_of_tries_btn_rect is not None
    q2.trigger_click(q2.out_of_tries_btn_rect.center)
    assert q2.quiz_state == 0
    assert q2.quiz_station_index == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

