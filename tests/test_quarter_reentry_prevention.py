import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
import pygame
from unittest.mock import MagicMock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))


class TestQuarterReentryPrevention(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.get_surface()
        self.mock_main_menu = MagicMock()
        self.mock_main_menu.screen = self.screen
        self.mock_main_menu.student_id = "test_student_123"
        self.mock_main_menu.selected_student = {
            "id": 123,
            "student_id": "test_student_123",
            "first_name": "Jess",
            "last_name": "Test"
        }
        self.mock_main_menu.audio_manager = MagicMock()

    @patch("db.save_system.get_completed_quarters")
    def test_completed_quarter1_cannot_be_reentered(self, mock_get_completed):
        mock_get_completed.return_value = {
            "quarter1": {"completed": True, "score": 100, "percentage": 100.0}
        }
        from screens.stageselect import StageSelect
        ss = StageSelect(self.screen, self.mock_main_menu)

        # Verify Q1 is completed and Q2 is unlocked
        self.assertTrue(ss.is_quarter_completed("quarter1"))
        self.assertFalse(ss.is_quarter_completed("quarter2"))
        self.assertTrue(ss.is_quarter_unlocked("quarter2"))

        # Try to enter quarter1 directly
        ss.enter_quarter("quarter1")
        self.assertFalse(ss.portal_transition_active, "Portal transition must NOT activate for completed quarter 1")
        self.assertIn("Quarter 1 is already completed", ss.locked_portal_banner_msg)

        # Check touching Q1 portal (left)
        left_portal = next((p for p in ss.portals if p.direction == 'left'), None)
        self.assertIsNotNone(left_portal)
        ss.player_x = left_portal.get_world_x()
        ss.player_y = left_portal.get_world_y()

        # Step collision
        ss.fist_closed = False
        ss.update()
        self.assertFalse(ss.portal_transition_active)

        # Click on left portal
        ss.trigger_click((640, 360))
        self.assertFalse(ss.portal_transition_active)

    @patch("db.save_system.get_completed_quarters")
    def test_unlocked_incomplete_quarter2_can_be_entered(self, mock_get_completed):
        mock_get_completed.return_value = {
            "quarter1": {"completed": True, "score": 100, "percentage": 100.0}
        }
        from screens.stageselect import StageSelect
        ss = StageSelect(self.screen, self.mock_main_menu)

        # Q2 is unlocked but not completed
        self.assertTrue(ss.is_quarter_unlocked("quarter2"))
        self.assertFalse(ss.is_quarter_completed("quarter2"))

        # Enter quarter2
        ss.enter_quarter("quarter2")
        self.assertTrue(ss.portal_transition_active, "Quarter 2 should be entered since it is unlocked and not yet completed")
        self.assertEqual(ss.portal_transition_target, "quarter2")

    @patch("db.save_system.get_completed_quarters")
    def test_all_quarters_completed_blocks_all_reentries(self, mock_get_completed):
        mock_get_completed.return_value = {
            "quarter1": {"completed": True, "score": 100, "percentage": 100.0},
            "quarter2": {"completed": True, "score": 100, "percentage": 100.0},
            "quarter3": {"completed": True, "score": 100, "percentage": 100.0},
            "quarter4": {"completed": True, "score": 120, "percentage": 100.0},
        }
        from screens.stageselect import StageSelect
        ss = StageSelect(self.screen, self.mock_main_menu)

        for q in ["quarter1", "quarter2", "quarter3", "quarter4"]:
            ss.portal_transition_active = False
            ss.locked_portal_banner_msg = ""
            ss.enter_quarter(q)
            self.assertFalse(ss.portal_transition_active, f"Must not enter {q} when completed")
            self.assertTrue(len(ss.locked_portal_banner_msg) > 0, f"Banner message expected for {q}")

    @patch("screens.stageselect.StageSelect")
    def test_apply_student_progress_redirects_completed_quarter_to_stage_select(self, mock_ss_cls):
        from db.save_system import apply_student_progress
        save_data = {
            "student_id": "test_student_123",
            "current_screen": "quarter4",
            "completed_quarters": {
                "quarter4": {"completed": True, "score": 120}
            },
            "quarter_data": {
                "completed": True
            }
        }
        mm = MagicMock()
        apply_student_progress(mm, save_data)
        self.assertEqual(mm.current_screen, "stage_select")


if __name__ == "__main__":
    unittest.main()
