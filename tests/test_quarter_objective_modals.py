# tests/test_quarter_objective_modals.py
import unittest
import pygame
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"


class MockMainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.cursor_pos = (900, 200)  # Cursor far away from player spawn
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.current_gesture = "NONE"
        self.selected_student = {
            "first_name": "Maria",
            "last_name": "Santos",
            "username": "maria_s",
            "student_id": "S-2024-001"
        }
        self.current_screen = "stage_select"
        self.last_stage_select_data = None
        self.save_data = {}
        from core.audio_manager import audio_manager
        self.audio_manager = audio_manager


class TestQuarterObjectiveModals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.main_menu = MockMainMenu(self.screen)

    def test_01_quarter1_objective_modal_persistence(self):
        """Quarter 1 objective modal pops up on entry and does not vanish when cursor is distant."""
        from screens.quarter1 import Quarter1
        q1 = Quarter1(self.screen, self.main_menu, "map1.txt")

        # Must be active on entry
        self.assertTrue(q1.instruction_modal.is_active(), "Q1 modal must be active on entry")
        self.assertIn("QUARTER 1", q1.instruction_modal.title.upper())

        # Simulate update with cursor far from player (should NOT auto-dismiss)
        q1.cursor_pos = (950, 150)
        q1.update()
        self.assertTrue(q1.instruction_modal.is_active(), "Q1 modal must persist even when cursor is distant from player")

        # Test dismiss via trigger click
        q1.trigger_click((q1.instruction_modal.btn_x + 10, q1.instruction_modal.btn_y + 10))
        self.assertFalse(q1.instruction_modal.is_active(), "Q1 modal should dismiss on click")

        # Test re-opening via Guide HUD button
        guide_btn_rect = pygame.Rect(q1.width - 256, 18, 110, 36)
        q1.trigger_click(guide_btn_rect.center)
        self.assertTrue(q1.instruction_modal.is_active(), "Q1 modal should re-open on Guide button click")

        # Test dismiss via fist hold
        import time
        q1.current_gesture = "FIST"
        q1.fist_closed = True
        q1.fist_start_time = time.time() - 1.0  # Held for > 0.9s
        q1.update()
        self.assertFalse(q1.instruction_modal.is_active(), "Q1 modal should dismiss when fist is held for >= 0.9s")

    def test_02_quarter2_objective_modal_persistence(self):
        """Quarter 2 objective modal pops up on entry and does not vanish when cursor is distant."""
        from screens.quarter2 import Quarter2
        q2 = Quarter2(self.screen, self.main_menu, "map4.txt")

        # Must be active on entry
        self.assertTrue(q2.instruction_modal.is_visible, "Q2 modal must be active on entry")
        self.assertIn("QUARTER 2", q2.instruction_modal.title.upper())

        # Simulate update with cursor far from player (should NOT auto-dismiss)
        q2.cursor_pos = (950, 150)
        q2.update()
        self.assertTrue(q2.instruction_modal.is_visible, "Q2 modal must persist even when cursor is distant from player")

        # Test dismiss via trigger click
        q2.trigger_click((q2.instruction_modal.btn_x + 10, q2.instruction_modal.btn_y + 10))
        self.assertFalse(q2.instruction_modal.is_visible, "Q2 modal should dismiss on click")

        # Test re-opening via Guide HUD button
        q2.trigger_click(q2.guide_btn_rect.center)
        self.assertTrue(q2.instruction_modal.is_visible, "Q2 modal should re-open on Guide button click")

        # Test dismiss via fist hold
        import time
        q2.fist_closed = True
        q2.fist_start_time = time.time() - 1.0
        q2.update()
        self.assertFalse(q2.instruction_modal.is_visible, "Q2 modal should dismiss when fist is held for >= 0.9s")

    def test_03_quarter3_objective_modal_persistence(self):
        """Quarter 3 objective modal pops up on entry and does not vanish when cursor is distant."""
        from screens.quarter3 import Quarter3
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")

        # Must be active on entry
        self.assertTrue(q3.instruction_modal.is_visible, "Q3 modal must be active on entry")
        self.assertIn("QUARTER 3", q3.instruction_modal.title.upper())

        # Simulate update with cursor far from player (should NOT auto-dismiss)
        q3.cursor_pos = (950, 150)
        q3.update()
        self.assertTrue(q3.instruction_modal.is_visible, "Q3 modal must persist even when cursor is distant from player")

        # Test dismiss via trigger click
        q3.trigger_click((q3.instruction_modal.btn_x + 10, q3.instruction_modal.btn_y + 10))
        self.assertFalse(q3.instruction_modal.is_visible, "Q3 modal should dismiss on click")

        # Test re-opening via Guide HUD button
        q3.trigger_click(q3.guide_btn_rect.center)
        self.assertTrue(q3.instruction_modal.is_visible, "Q3 modal should re-open on Guide button click")

        # Test dismiss via fist hold
        import time
        q3.fist_closed = True
        q3.fist_start_time = time.time() - 1.0
        q3.update()
        self.assertFalse(q3.instruction_modal.is_visible, "Q3 modal should dismiss when fist is held for >= 0.9s")

    def test_04_quarter4_objective_modal_persistence(self):
        """Quarter 4 objective modal pops up on entry and does not vanish when cursor is distant."""
        from screens.quarter4 import Quarter4
        q4 = Quarter4(self.screen, self.main_menu, "map10.txt")

        # Must be active on entry
        self.assertTrue(q4.instruction_modal.is_visible, "Q4 modal must be active on entry")
        self.assertTrue(
            "QUARTER 4" in q4.instruction_modal.title.upper() or "SUMMATIVE ASSESSMENT" in q4.instruction_modal.title.upper(),
            f"Expected QUARTER 4 or SUMMATIVE ASSESSMENT in modal title, got {q4.instruction_modal.title}"
        )

        # Simulate update with cursor far from player (should NOT auto-dismiss)
        q4.cursor_pos = (950, 150)
        q4.update()
        self.assertTrue(q4.instruction_modal.is_visible, "Q4 modal must persist even when cursor is distant from player")

        # Test dismiss via trigger click
        q4.trigger_click((q4.instruction_modal.btn_x + 10, q4.instruction_modal.btn_y + 10))
        self.assertFalse(q4.instruction_modal.is_visible, "Q4 modal should dismiss on click")

        # Test re-opening via Guide HUD button
        q4.trigger_click(q4.guide_btn_rect.center)
        self.assertTrue(q4.instruction_modal.is_visible, "Q4 modal should re-open on Guide button click")

        # Test dismiss via fist hold
        import time
        q4.fist_closed = True
        q4.fist_start_time = time.time() - 1.0
        q4.update()
        self.assertFalse(q4.instruction_modal.is_visible, "Q4 modal should dismiss when fist is held for >= 0.9s")


if __name__ == "__main__":
    unittest.main()
