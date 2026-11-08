# tests/test_quarter3_victory_card_fist.py - Tests closed fist click on Quarter 3 Victory Card
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

import pygame
pygame.init()
pygame.font.init()

from screens.quarter3 import Quarter3


class MockMainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.student_id = "Q3_FIST_TEST_001"
        self.student_db_id = 888
        self.selected_student = {
            "id": 888,
            "student_id": "Q3_FIST_TEST_001",
            "first_name": "Test",
            "last_name": "Student",
            "score": 0,
            "progress": 0,
            "level": "Grade 2",
            "gender": "male"
        }
        self.current_screen = "quarter3"
        self.popup_state = None
        self.stage_select = None
        self.quarter3 = None
        self.last_stage_select_data = None
        self.audio_manager = MagicMock()


class TestQuarter3VictoryCardFist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.mm = MockMainMenu(self.screen)
        self.q3 = Quarter3(self.screen, self.mm, "map7.txt")
        self.mm.quarter3 = self.q3
        self.q3.instruction_modal.hide()

    def test_01_fist_click_on_continue_to_hub(self):
        """Verify closed fist hold/click on 'Continue to Hub' returns player to stage select."""
        # Activate victory card modal at end of Quarter 3
        self.q3.victory_card.show(total_questions=5, correct_first_try=5, score=100)
        self.assertTrue(self.q3.victory_card.active, "Victory card must be active")

        # Mock finish_and_return_to_hub callback
        self.q3.finish_and_return_to_hub = MagicMock()
        self.q3.victory_card.continue_callback = self.q3.finish_and_return_to_hub

        # Simulate closed fist hold click on the Continue button center
        con_center = self.q3.victory_card.continue_rect.center
        self.q3.trigger_click(con_center)

        self.q3.finish_and_return_to_hub.assert_called_once()
        self.assertFalse(self.q3.victory_card.active, "Victory card should dismiss on continue click")

    def test_02_fist_click_on_replay_stage(self):
        """Verify closed fist hold/click on 'Replay Stage' invokes level restart."""
        # Activate victory card modal at end of Quarter 3
        self.q3.victory_card.show(total_questions=5, correct_first_try=4, score=80)
        self.assertTrue(self.q3.victory_card.active, "Victory card must be active")

        # Mock restart_level callback
        self.q3.restart_level = MagicMock()
        self.q3.victory_card.replay_callback = self.q3.restart_level

        # Simulate closed fist hold click on the Replay button center
        rep_center = self.q3.victory_card.replay_rect.center
        self.q3.trigger_click(rep_center)

        self.q3.restart_level.assert_called_once()
        self.assertFalse(self.q3.victory_card.active, "Victory card should dismiss on replay click")


if __name__ == "__main__":
    unittest.main()

