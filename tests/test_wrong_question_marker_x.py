# tests/test_wrong_question_marker_x.py
import unittest
import os
import pygame
from unittest.mock import MagicMock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

pygame.init()
pygame.display.set_mode((1280, 720))


class TestWrongQuestionMarkerX(unittest.TestCase):
    def setUp(self):
        self.surface = pygame.Surface((1280, 720), pygame.SRCALPHA)

    def test_beacon_marker_cross_and_x_types(self):
        """Verify draw_beacon_marker supports 'cross' and 'x' types with caching."""
        from core.visual_effects import draw_beacon_marker, _BEACON_CACHE
        
        # Test 'cross' beacon
        draw_beacon_marker(self.surface, 150, 150, color=(239, 68, 68), beacon_type="cross", offset_y=-30)
        key_cross = ((239, 68, 68), "cross", True)
        self.assertIn(key_cross, _BEACON_CACHE)
        self.assertIsNotNone(_BEACON_CACHE[key_cross])

        # Test 'x' beacon
        draw_beacon_marker(self.surface, 250, 150, color=(239, 68, 68), beacon_type="x", offset_y=-30)
        key_x = ((239, 68, 68), "x", True)
        self.assertIn(key_x, _BEACON_CACHE)
        self.assertIsNotNone(_BEACON_CACHE[key_x])

    @patch("screens.quarter1.draw_beacon_marker")
    def test_quarter1_question_mark_for_all_unanswered_and_no_names(self, mock_beacon):
        """Verify all unanswered NPCs show a question mark beacon, and no names overhead."""
        from screens.quarter1 import Quarter1
        main_mock = MagicMock()
        q1 = Quarter1(self.surface, main_mock, map_name="map1.txt")
        q1.is_quiz_map = True
        
        # 4 stations: 1 correct, 2 wrong, 3 active unanswered, 4 inactive unanswered
        q1.shape_npcs = {
            1: {"x": 100, "y": 100, "answered": True, "name": "Circle"},
            2: {"x": 200, "y": 100, "answered": True, "name": "Square"},
            3: {"x": 300, "y": 100, "answered": False, "name": "Triangle"},
            4: {"x": 400, "y": 100, "answered": False, "name": "Star"},
        }
        q1.first_attempt_correct = {1: True, 2: False, 3: True, 4: True}
        q1.quiz_station_index = 3
        q1.quiz_state = 0

        # Draw the screen
        q1.draw()

        # Station 1 (correct): check beacon
        mock_beacon.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, color=(34, 197, 94), beacon_type="check", offset_y=int(-30 * 1.50))
        # Station 2 (wrong): cross/X beacon
        mock_beacon.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, color=(239, 68, 68), beacon_type="cross", offset_y=int(-30 * 1.50))
        # Station 3 (unanswered active): question mark beacon
        mock_beacon.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, color=(250, 204, 21), beacon_type="question", offset_y=int(-32 * 1.50))
        # Station 4 (unanswered inactive): question mark beacon as well!
        mock_beacon.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, color=(251, 191, 36), beacon_type="question", offset_y=int(-32 * 1.50))

    @patch("screens.quarter2.draw_beacon_marker")
    def test_quarter2_question_mark_for_all_unanswered(self, mock_beacon):
        """Verify Quarter 2 shows question mark for all unanswered stalls and X for wrong."""
        from screens.quarter2 import Quarter2
        main_mock = MagicMock()
        q2 = Quarter2(self.surface, main_mock, map_name="map4.txt")

        q2.station_npc_info[1]["cleared"] = True
        q2.first_attempt_correct[1] = True

        q2.station_npc_info[2]["cleared"] = True
        q2.first_attempt_correct[2] = False

        q2.station_npc_info[3]["cleared"] = False
        q2.station_npc_info[4]["cleared"] = False
        q2.quiz_station_index = 3
        q2.quiz_state = 0

        q2.draw()

        mock_beacon.assert_any_call(q2.screen, unittest.mock.ANY, unittest.mock.ANY, color=(34, 197, 94), beacon_type="check", offset_y=int(-30 * 1.50))
        mock_beacon.assert_any_call(q2.screen, unittest.mock.ANY, unittest.mock.ANY, color=(239, 68, 68), beacon_type="cross", offset_y=int(-30 * 1.50))
        mock_beacon.assert_any_call(q2.screen, unittest.mock.ANY, unittest.mock.ANY, color=(251, 191, 36), beacon_type="question", offset_y=int(-32 * 1.50))
        mock_beacon.assert_any_call(q2.screen, unittest.mock.ANY, unittest.mock.ANY, color=(226, 180, 20), beacon_type="question", offset_y=int(-32 * 1.50))

    def test_hud_card_and_objectives_box_with_wrong_answers_rendering(self):
        """Verify HUD card and Objectives window render wrong answer indicators across all quarters without crash."""
        from screens.quarter1 import Quarter1
        from screens.quarter2 import Quarter2
        from screens.quarter3 import Quarter3
        from screens.quarter4 import Quarter4

        main_mock = MagicMock()
        q1 = Quarter1(self.surface, main_mock, map_name="map1.txt")
        q1.first_attempt_correct = {1: True, 2: False, 3: True}
        q1.shape_npcs = {1: {"answered": True}, 2: {"answered": True}, 3: {"answered": False}}
        q1.active_station_count = 3
        # Should render HUD card and Objectives window with wrong indicator
        q1.draw_character_completion_status_hud()
        q1.draw_ui()

        q2 = Quarter2(self.surface, main_mock, map_name="map4.txt")
        q2.first_attempt_correct = {1: False, 2: True, 3: False}
        q2.station_npc_info = {1: {"cleared": True}, 2: {"cleared": True}, 3: {"cleared": False}}
        q2.active_station_count = 3
        q2.quiz_station_index = 3
        q2.draw_character_completion_status_hud()
        q2.draw_ui()

        q3 = Quarter3(self.surface, main_mock, map_name="map7.txt")
        q3.first_attempt_correct = {1: True, 2: False, 3: False}
        q3.answered_stations = {1, 2}
        q3.active_station_count = 3
        q3.quiz_station_index = 3
        q3.draw_character_completion_status_hud()
        q3.draw_ui()

        q4 = Quarter4(self.surface, main_mock, map_name="map10.txt")
        q4.first_attempt_correct = {1: False, 2: True, 3: False}
        q4.answered_stations = {1, 2}
        q4.active_station_count = 3
        q4.quiz_station_index = 3
        q4.draw_character_completion_status_hud()
        q4.draw_ui()


if __name__ == "__main__":
    unittest.main()
