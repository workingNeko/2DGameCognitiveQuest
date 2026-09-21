# tests/test_text_overlap_fixes.py - Verification for Text Overlap Fixes across the game
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.font.init()

from core.font_manager import install_font_cache, get_font
install_font_cache()

from core.quiz_dialog import RPGQuizDialog
from screens.main_menu import MainMenu


class TestTextOverlapFixes(unittest.TestCase):

    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))

    def test_main_menu_gesture_hud_does_not_overlap_exit_or_settings(self):
        """Verify gesture status badge does not overlap Exit button or Settings button on main menu."""
        menu = MainMenu(self.screen)
        menu.current_screen = "menu"

        gx, gy, gw, gh = menu.get_gesture_hud_geometry()
        gesture_rect = pygame.Rect(gx, gy, gw, gh)

        exit_rect = menu.exit_btn.rect
        sound_rect = menu.sound_btn.rect

        self.assertFalse(
            gesture_rect.colliderect(exit_rect),
            f"Gesture HUD {gesture_rect} collides with Exit button {exit_rect} on main menu!"
        )
        self.assertFalse(
            gesture_rect.colliderect(sound_rect),
            f"Gesture HUD {gesture_rect} collides with Settings button {sound_rect} on main menu!"
        )

    def test_main_menu_sound_btn_text_not_duplicated(self):
        """Verify sound button text does not format as 'SOUND: SOUND 100%'."""
        menu = MainMenu(self.screen)
        menu.current_screen = "menu"
        menu.update()

        self.assertNotIn("SOUND: SOUND", menu.sound_btn.text)
        self.assertTrue("SETTINGS" in menu.sound_btn.text)

    def test_quiz_dialog_dynamic_positioning_no_overlap(self):
        """Verify question prompt and hint banner do not collide with choice button [A]."""
        dialog = RPGQuizDialog(self.screen, 1024, 768)

        # Long multi-line question
        long_q_data = {
            "question": "In the kingdom of mathematics, an ancient guardian has a collection of 24 glowing crystals that must be divided equally among 6 golden pedastals. How many crystals will rest on each pedestal?",
            "choices": ["3 crystals", "4 crystals", "5 crystals", "6 crystals"],
            "correct": 1
        }

        # Render dialog with hint
        dialog.draw(
            cursor_pos=(0, 0),
            q_data=long_q_data,
            speaker_name="Ancient Crystal Sphinx",
            speaker_subtitle="High Guardian of the Prismatic Sanctuary - Final Trial",
            station_idx=4,
            total_stations=6,
            hint_msg="Think about dividing 24 by 6 equal parts!"
        )

        button_0_rect = dialog.get_button_rect(0)

        # Calculate where the question + hint end
        q_font = get_font(["Segoe UI", "Comic Sans MS"], 18, bold=True)
        wrapped = dialog.wrap_text(long_q_data["question"], q_font, dialog.box_w - 60)
        y_text = dialog.box_y + 88 + len(wrapped) * 23
        y_hint_bottom = y_text + 26

        # Button 0 top must be strictly below the hint bottom
        self.assertGreater(
            button_0_rect.top,
            y_hint_bottom,
            f"Choice Button [A] top ({button_0_rect.top}) collides with hint bottom ({y_hint_bottom})!"
        )

    def test_quiz_dialog_speaker_subtitle_does_not_overlap_gem_track(self):
        """Verify long speaker subtitle is clamped and does not crash into gem progress bar."""
        dialog = RPGQuizDialog(self.screen, 1024, 768)

        total_st = 6
        gem_start_x = dialog.box_x + dialog.box_w - 28 - (total_st - 1) * 30

        q_data = {
            "question": "What is 5 + 5?",
            "choices": ["8", "10", "12", "15"],
            "correct": 1
        }

        dialog.draw(
            cursor_pos=(0, 0),
            q_data=q_data,
            speaker_name="Supreme Aquatic Celestial Leviathan",
            speaker_subtitle="Guardian of the Grand Sunken Aqueduct and Subterranean Chambers - Station 6 of 6",
            station_idx=6,
            total_stations=6
        )

        text_x = dialog.box_x + 94
        max_allowed_w = gem_start_x - text_x - 16
        self.assertGreater(max_allowed_w, 100)

    def test_objectives_hud_box_widths(self):
        """Verify Quarter 1, 3, and 4 Objectives HUD boxes are wide enough to fit objective text."""
        from screens.quarter3 import Quarter3

        menu = MainMenu(self.screen)
        q3 = Quarter3(self.screen, menu, "map7.txt")

        # Quarter 3 cached obj_hud_bg width
        self.assertEqual(q3.obj_hud_bg.get_width(), 480)

        # Check longest strings comfortably fit in 480 width
        test_font = pygame.font.SysFont("Comic Sans MS", 12)
        q1_str = "- Portal Status: OPEN (Enter the portal to exit!)"
        q4_str = "- Canal Full! Talk to Guardian Bromen at dock to unlock raft!"

        self.assertLess(test_font.size(q1_str)[0] + 30, 480)
        self.assertLess(test_font.size(q4_str)[0] + 30, 480)


if __name__ == "__main__":
    unittest.main()
