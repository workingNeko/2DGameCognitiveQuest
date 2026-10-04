# tests/test_quiz_dialog.py
import os
import sys
import unittest

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

class TestQuizDialog(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))

    def test_quiz_dialog_initialization_and_hitbox(self):
        dialog = RPGQuizDialog(self.screen, 1280, 720)

        self.assertEqual(dialog.box_w, 960)
        self.assertEqual(dialog.box_h, 570)
        self.assertEqual(dialog.box_x, (1280 - 960) // 2)
        self.assertEqual(dialog.box_y, (720 - 570) // 2)

        # Check button rects
        rect0 = dialog.get_button_rect(0)
        self.assertEqual(rect0.width, 840)
        self.assertEqual(rect0.height, 56)

        # Test click detection
        center0 = rect0.center
        clicked = dialog.get_clicked_choice(center0)
        self.assertEqual(clicked, 0)

        # Test click on eliminated choice
        clicked_elim = dialog.get_clicked_choice(center0, eliminated_choices={0})
        self.assertIsNone(clicked_elim)

        # Test click outside
        clicked_none = dialog.get_clicked_choice((10, 10))
        self.assertIsNone(clicked_none)

    def test_quiz_dialog_drawing(self):
        dialog = RPGQuizDialog(self.screen, 1280, 720)

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

    def test_clean_choice_text(self):
        from core.quiz_dialog import clean_choice_text

        self.assertEqual(clean_choice_text("A. Pentagon"), "Pentagon")
        self.assertEqual(clean_choice_text("B. Triagle"), "Triagle")
        self.assertEqual(clean_choice_text("C. Square"), "Square")
        self.assertEqual(clean_choice_text("D. Rectangle"), "Rectangle")
        self.assertEqual(clean_choice_text("A. ₱23"), "₱23")
        self.assertEqual(clean_choice_text("A) Circle"), "Circle")
        self.assertEqual(clean_choice_text("B: Heart"), "Heart")
        self.assertEqual(clean_choice_text("[C] Star"), "Star")
        self.assertEqual(clean_choice_text("(D) Diamond"), "Diamond")
        self.assertEqual(clean_choice_text("A - Line"), "Line")
        self.assertEqual(clean_choice_text("All of the above"), "All of the above")
        self.assertEqual(clean_choice_text("Apple"), "Apple")
        self.assertEqual(clean_choice_text("7 mangoes"), "7 mangoes")

if __name__ == "__main__":
    unittest.main()

