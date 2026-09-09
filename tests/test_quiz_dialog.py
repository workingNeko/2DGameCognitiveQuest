# tests/test_quiz_dialog.py
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

pygame.init()
pygame.font.init()

from core.font_manager import install_font_cache
install_font_cache()

from core.quiz_dialog import RPGQuizDialog

def test_quiz_dialog_initialization_and_hitbox():
    screen = pygame.display.set_mode((1024, 768))
    dialog = RPGQuizDialog(screen, 1024, 768)

    assert dialog.box_w == 840
    assert dialog.box_h == 520
    assert dialog.box_x == (1024 - 840) // 2
    assert dialog.box_y == (768 - 520) // 2

    # Check button rects
    rect0 = dialog.get_button_rect(0)
    assert rect0.width == 740
    assert rect0.height == 50

    # Test click detection
    center0 = rect0.center
    clicked = dialog.get_clicked_choice(center0)
    assert clicked == 0

    # Test click on eliminated choice
    clicked_elim = dialog.get_clicked_choice(center0, eliminated_choices={0})
    assert clicked_elim is None

    # Test click outside
    clicked_none = dialog.get_clicked_choice((10, 10))
    assert clicked_none is None

    print("PASS: RPGQuizDialog initialization and hit-testing verified.")

def test_quiz_dialog_drawing():
    screen = pygame.display.set_mode((1024, 768))
    dialog = RPGQuizDialog(screen, 1024, 768)

    q_data = {
        "question": "Which shape has 4 equal sides and 4 right angles?",
        "choices": ["Circle", "Square", "Triangle", "Star"],
        "correct": 1
    }

    dummy_sprite = pygame.Surface((32, 32))
    dummy_sprite.fill((255, 215, 0))

    # Draw with sprite, station 2 of 5, one choice eliminated, and hint message
    dialog.update(0.016)
    dialog.draw(
        cursor_pos=(dialog.btn_x + 50, dialog.button_y_start + 10),
        q_data=q_data,
        speaker_name="Square Guardian",
        speaker_subtitle="Quest Station 2 of 5 - Storybook Meadow",
        sprite_frame=dummy_sprite,
        station_idx=2,
        total_stations=5,
        eliminated_choices={2},
        hint_msg="Count all 4 equal corners!"
    )

    print("PASS: RPGQuizDialog draws cleanly with all elements.")

def test_clean_choice_text():
    from core.quiz_dialog import clean_choice_text

    assert clean_choice_text("A. Pentagon") == "Pentagon"
    assert clean_choice_text("B. Triagle") == "Triagle"
    assert clean_choice_text("C. Square") == "Square"
    assert clean_choice_text("D. Rectangle") == "Rectangle"
    assert clean_choice_text("A. ₱23") == "₱23"
    assert clean_choice_text("A) Circle") == "Circle"
    assert clean_choice_text("B: Heart") == "Heart"
    assert clean_choice_text("[C] Star") == "Star"
    assert clean_choice_text("(D) Diamond") == "Diamond"
    assert clean_choice_text("A - Line") == "Line"
    assert clean_choice_text("All of the above") == "All of the above"
    assert clean_choice_text("Apple") == "Apple"
    assert clean_choice_text("7 mangoes") == "7 mangoes"

    print("PASS: clean_choice_text strips duplicate A/B/C/D prefixes accurately.")

if __name__ == "__main__":
    test_clean_choice_text()
    test_quiz_dialog_initialization_and_hitbox()
    test_quiz_dialog_drawing()
    print("ALL RPG QUIZ DIALOG TESTS PASSED!")

