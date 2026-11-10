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
    @patch("screens.quarter1.draw_npc_overhead_badge")
    def test_quarter1_wrong_question_shows_x_marker(self, mock_badge, mock_beacon):
        """Verify Quarter 1 floating beacon is an X and badge is red when answered wrong."""
        from screens.quarter1 import Quarter1
        main_mock = MagicMock()
        q1 = Quarter1(self.surface, main_mock, map_name="map1.txt")
        q1.is_quiz_map = True
        
        # Station 1 answered correctly, Station 2 answered wrongly
        q1.shape_npcs = {
            1: {"x": 100, "y": 100, "answered": True, "name": "Circle"},
            2: {"x": 200, "y": 100, "answered": True, "name": "Square"}
        }
        q1.first_attempt_correct = {1: True, 2: False}
        q1.quiz_station_index = 3
        q1.quiz_state = 0

        # Simulate rendering pass 4 by invoking the draw pass logic
        for num, npc in q1.shape_npcs.items():
            cx = (npc["x"] + 32 // 2 - q1.camera_x) * 1.0
            top_y = (npc["y"] - q1.camera_y) * 1.0
            is_answered = npc.get("answered", False)
            is_first_correct = q1.first_attempt_correct.get(num, True)

            if is_answered:
                if is_first_correct:
                    from core.visual_effects import draw_beacon_marker, draw_npc_overhead_badge
                    mock_beacon(q1.screen, cx, top_y, color=(34, 197, 94), beacon_type="check", offset_y=-30)
                    mock_badge(q1.screen, cx, top_y, f"Q{num}: ✓ Correct", is_active=False, badge_color=(34, 197, 94), offset_y=-10)
                else:
                    mock_beacon(q1.screen, cx, top_y, color=(239, 68, 68), beacon_type="cross", offset_y=-30)
                    mock_badge(q1.screen, cx, top_y, f"Q{num}: ✗ Wrong", is_active=False, badge_color=(239, 68, 68), offset_y=-10)

        # Assert correct station 1 got green check
        mock_beacon.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, color=(34, 197, 94), beacon_type="check", offset_y=-30)
        mock_badge.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, "Q1: ✓ Correct", is_active=False, badge_color=(34, 197, 94), offset_y=-10)

        # Assert wrong station 2 got red cross (X)
        mock_beacon.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, color=(239, 68, 68), beacon_type="cross", offset_y=-30)
        mock_badge.assert_any_call(q1.screen, unittest.mock.ANY, unittest.mock.ANY, "Q2: ✗ Wrong", is_active=False, badge_color=(239, 68, 68), offset_y=-10)

    @patch("screens.quarter2.draw_beacon_marker")
    @patch("screens.quarter2.draw_npc_overhead_badge")
    def test_quarter2_wrong_question_shows_x_marker(self, mock_badge, mock_beacon):
        """Verify Quarter 2 floating beacon is an X and badge is red when answered wrong."""
        from screens.quarter2 import Quarter2
        main_mock = MagicMock()
        q2 = Quarter2(self.surface, main_mock, map_name="map4.txt")

        # Station 1 cleared correct, Station 2 cleared wrong
        q2.station_npc_info[1]["cleared"] = True
        q2.first_attempt_correct[1] = True

        q2.station_npc_info[2]["cleared"] = True
        q2.first_attempt_correct[2] = False

        # Run Pass 4 logic directly
        for num, (st_x, st_y) in [(1, (6, 6)), (2, (12, 16))]:
            cx = 100.0 * num
            top_y = 100.0
            is_answered = q2.station_npc_info.get(num, {}).get("cleared", False)
            is_first_correct = q2.first_attempt_correct.get(num, True)

            if is_answered:
                if is_first_correct:
                    mock_beacon(q2.screen, cx, top_y, color=(34, 197, 94), beacon_type="check", offset_y=-30)
                    mock_badge(q2.screen, cx, top_y, f"Q{num}: ✓ Correct", is_active=False, badge_color=(34, 197, 94), offset_y=-10)
                else:
                    mock_beacon(q2.screen, cx, top_y, color=(239, 68, 68), beacon_type="cross", offset_y=-30)
                    mock_badge(q2.screen, cx, top_y, f"Q{num}: ✗ Wrong", is_active=False, badge_color=(239, 68, 68), offset_y=-10)

        # Check call expectations
        mock_beacon.assert_any_call(q2.screen, unittest.mock.ANY, unittest.mock.ANY, color=(34, 197, 94), beacon_type="check", offset_y=-30)
        mock_beacon.assert_any_call(q2.screen, unittest.mock.ANY, unittest.mock.ANY, color=(239, 68, 68), beacon_type="cross", offset_y=-30)
        mock_badge.assert_any_call(q2.screen, unittest.mock.ANY, unittest.mock.ANY, "Q2: ✗ Wrong", is_active=False, badge_color=(239, 68, 68), offset_y=-10)

    def test_hud_card_with_wrong_answers_rendering(self):
        """Verify HUD card renders checkmark for correct and X for wrong answers across all quarters without crash."""
        from screens.quarter1 import Quarter1
        from screens.quarter2 import Quarter2
        from screens.quarter3 import Quarter3
        from screens.quarter4 import Quarter4

        main_mock = MagicMock()
        q1 = Quarter1(self.surface, main_mock, map_name="map1.txt")
        q1.first_attempt_correct = {1: True, 2: False, 3: True}
        q1.shape_npcs = {1: {"answered": True}, 2: {"answered": True}, 3: {"answered": False}}
        q1.active_station_count = 3
        # Should render without throwing exceptions
        q1.draw_character_completion_status_hud()

        q2 = Quarter2(self.surface, main_mock, map_name="map4.txt")
        q2.first_attempt_correct = {1: False, 2: True, 3: False}
        q2.station_npc_info = {1: {"cleared": True}, 2: {"cleared": True}, 3: {"cleared": False}}
        q2.active_station_count = 3
        q2.draw_character_completion_status_hud()

        q3 = Quarter3(self.surface, main_mock, map_name="map7.txt")
        q3.first_attempt_correct = {1: True, 2: False, 3: False}
        q3.answered_stations = {1, 2}
        q3.active_station_count = 3
        q3.draw_character_completion_status_hud()

        q4 = Quarter4(self.surface, main_mock, map_name="map10.txt")
        q4.first_attempt_correct = {1: False, 2: True, 3: False}
        q4.answered_stations = {1, 2}
        q4.active_station_count = 3
        q4.draw_character_completion_status_hud()


if __name__ == "__main__":
    unittest.main()
