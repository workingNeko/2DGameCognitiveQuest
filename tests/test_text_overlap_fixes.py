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
        q_text = long_q_data["question"]
        q_font_size = 24 if len(q_text) < 130 else 22
        q_font = get_font(["Segoe UI", "Comic Sans MS"], q_font_size, bold=True)
        wrapped = dialog.wrap_text(q_text, q_font, dialog.box_w - 60)
        line_height = 32 if q_font_size == 24 else 28
        y_text = dialog.box_y + 96 + len(wrapped) * line_height
        y_hint_bottom = y_text + 30

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

    def test_loading_screen_elements_no_overlap(self):
        """Verify LOADING... text, subtitle banner, and Objectives HUD never overlap across all quarters."""
        from screens.stageselect import StageSelect
        menu = MainMenu(self.screen)
        ss = StageSelect(self.screen, menu)

        cy = ss.height // 2
        base_y = cy - 85

        for qid in ["quarter1", "quarter2", "quarter3", "quarter4"]:
            ss._init_portal_transition_fx(qid)
            dest_rect = ss._cached_dest_rect

            # 1. Letters lowest bounce check
            for i, data in enumerate(ss.loading_letters):
                # Max oscillation offset is +8
                letter_h = data["surf"].get_height() - data["pad"] * 2
                max_letter_bottom = base_y + 8 + letter_h

                self.assertLess(
                    max_letter_bottom,
                    dest_rect.top,
                    f"[{qid}] LOADING... letter {i} bottom ({max_letter_bottom}) overlaps subtitle banner top ({dest_rect.top})!"
                )

            # 2. Subtitle banner must be strictly above bottom HUD
            hud_pos = ss._cached_hud_pos
            self.assertLess(
                dest_rect.bottom,
                hud_pos[1],
                f"[{qid}] Subtitle banner bottom ({dest_rect.bottom}) overlaps HUD top ({hud_pos[1]})!"
            )

    def test_stageselect_top_hud_text_does_not_overlap_stars(self):
        """Verify Quarters Mastered text does not collide with the first golden star medal."""
        from screens.stageselect import StageSelect
        menu = MainMenu(self.screen)
        ss = StageSelect(self.screen, menu)

        hud_w, hud_h = 370, 42
        hud_x = (ss.width - hud_w) // 2
        hud_y = 12

        hud_font = get_font("Comic Sans MS", 16, bold=True)
        text_w = hud_font.render("Quarters Mastered: 4/4", True, (241, 245, 249)).get_width()
        text_right = hud_x + 16 + text_w

        first_star_left = (hud_x + 258) - 8  # star radius = 8

        self.assertLess(
            text_right,
            first_star_left,
            f"Stage progress text right edge ({text_right}) collides with first star left edge ({first_star_left})!"
        )

    def test_tutorial_skip_button_text_does_not_overlap_esc_pill(self):
        """Verify 'Skip Tutorial' text has clear separation from the ESC shortcut pill."""
        from screens.tutorial import TutorialScreen
        menu = MainMenu(self.screen)
        tut = TutorialScreen(self.screen, menu)

        skip_rect = pygame.Rect(tut.width - 325, 18, 180, 36)
        skip_txt_w = tut.skip_font.render("Skip Tutorial", True, (255, 255, 255)).get_width()
        text_right = skip_rect.x + 14 + skip_txt_w

        pill_left = skip_rect.right - 52
        self.assertLess(
            text_right,
            pill_left,
            f"Tutorial skip text right edge ({text_right}) collides with pill left edge ({pill_left})!"
        )


if __name__ == "__main__":
    unittest.main()

