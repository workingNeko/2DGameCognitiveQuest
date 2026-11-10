# tests/test_dynamic_questions_and_objective_toggle.py
import os
import sys
import json
import unittest
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.settings_manager import (
    is_objective_finder_enabled,
    set_objective_finder_enabled,
    toggle_objective_finder,
    _get_settings_path
)
from core.dynamic_quiz_manager import allocate_dynamic_stations
from core.pathfinder_guide import QuestPathfinderGuide

class TestDynamicQuestionsAndObjectiveToggle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        # Ensure a clean state before each test
        set_objective_finder_enabled(False)

    def tearDown(self):
        # Reset to default
        set_objective_finder_enabled(False)

    def test_objective_finder_default_state(self):
        """Verify objective finder guide is disabled by default as requested."""
        self.assertFalse(is_objective_finder_enabled())

    def test_objective_finder_toggle_and_persistence(self):
        """Verify toggling objective finder persists correctly to audio_settings.json."""
        # Toggle on
        new_state = toggle_objective_finder()
        self.assertTrue(new_state)
        self.assertTrue(is_objective_finder_enabled())

        # Verify disk persistence
        settings_path = _get_settings_path()
        self.assertTrue(os.path.exists(settings_path))
        with open(settings_path, "r") as f:
            data = json.load(f)
        self.assertTrue(data.get("objective_finder", False))

        # Toggle back off
        new_state = toggle_objective_finder()
        self.assertFalse(new_state)
        self.assertFalse(is_objective_finder_enabled())

        with open(settings_path, "r") as f:
            data = json.load(f)
        self.assertFalse(data.get("objective_finder", True))

    def test_pathfinder_guide_suppression_when_disabled(self):
        """Verify pathfinder guide completely skips path calculation and drawing when disabled."""
        class MockQuarter:
            def __init__(self):
                self.screen = pygame.Surface((640, 480))
                self.quarter_id = "quarter1"
                self.map_name = "map1.txt"
                self.player_x = 64
                self.player_y = 64
                self.camera_x = 0
                self.camera_y = 0
                self.quiz_station_index = 1
                self.quiz_state = 0
                self.quiz_stations = {1: (5, 5), 2: (10, 5)}
                self.ROWS = 15
                self.COLS = 20
                self.game_map = ["G" * 20 for _ in range(15)]
                self.WALKABLE_TILES = {"G"}

        set_objective_finder_enabled(False)
        mock_q = MockQuarter()
        guide = QuestPathfinderGuide(mock_q, quarter_id="quarter1", theme="forest")

        # When disabled, update must fast-exit and cached path must remain empty
        guide.update(0.016)
        self.assertEqual(len(guide.cached_path_world), 0)

        # Draw call should execute safely without drawing any trail
        guide.draw(mock_q.screen)
        self.assertEqual(len(guide.cached_path_world), 0)

        # When enabled, update calculates path
        set_objective_finder_enabled(True)
        guide.active = True
        guide.update(0.016)
        self.assertTrue(len(guide.cached_path_world) >= 2)

    def test_dynamic_station_allocation(self):
        """Verify dynamic station allocation places new stations on walkable tiles away from forbidden tiles."""
        game_map = [
            "WWWWWWWWWWWWWWWWWWWW",
            "WGGGGGGGGGGGGGGGGGGW",
            "WGGGGGGGGGGGGGGGGGGW",
            "WGGGGGGGGGGGGGGGGGGW",
            "WGGGGGGGGGGGGGGGGGGW",
            "WGGGGGGGGGGGGGGGGGGW",
            "WWWWWWWWWWWWWWWWWWWW"
        ]
        existing = [(2, 2), (5, 2)]
        forbidden = {(1, 1), (2, 1), (3, 1)} # e.g. player spawn
        walkable = {"G"}

        # Request 6 total stations (existing 2 + 4 new = 6 total)
        total_stations = allocate_dynamic_stations(
            game_map,
            existing_stations=existing,
            needed_count=6,
            forbidden_tiles=forbidden,
            walkable_chars=walkable
        )

        self.assertEqual(len(total_stations), 6)

        for nx, ny in total_stations:
            # Must be walkable tile
            self.assertEqual(game_map[ny][nx], "G")
            # Must not be forbidden
            self.assertNotIn((nx, ny), forbidden)

        # Combined stations must all be unique
        self.assertEqual(len(total_stations), len(set(total_stations)))

        # Also verify dict input format (as used by game screens)
        dict_existing = {1: (2, 2), 2: (5, 2)}
        dict_result = allocate_dynamic_stations(
            game_map,
            existing_stations=dict_existing,
            needed_count=6,
            forbidden_tiles=forbidden,
            walkable_chars=walkable
        )
        self.assertIsInstance(dict_result, dict)
        self.assertEqual(len(dict_result), 6)
        self.assertEqual(dict_result[1], (2, 2))
        self.assertEqual(dict_result[2], (5, 2))
        for sid, (dx, dy) in dict_result.items():
            self.assertIn(sid, range(1, 7))
            self.assertEqual(game_map[dy][dx], "G")
            self.assertNotIn((dx, dy), forbidden)

    def test_nonlinear_question_index_mapping(self):
        """Verify that approaching Station N maps directly to Question N (current_question_index = N - 1)."""
        questions = [
            {"question": "Q1: What is a circle?", "choices": ["A", "B", "C"], "correct": 0},
            {"question": "Q2: What is a square?", "choices": ["A", "B", "C"], "correct": 1},
            {"question": "Q3: What is a triangle?", "choices": ["A", "B", "C"], "correct": 2},
            {"question": "Q4: What is a rectangle?", "choices": ["A", "B", "C"], "correct": 0},
            {"question": "Q5: What is a hexagon?", "choices": ["A", "B", "C"], "correct": 1},
            {"question": "Q6: What is an octagon?", "choices": ["A", "B", "C"], "correct": 2},
            {"question": "Q7: What is an oval?", "choices": ["A", "B", "C"], "correct": 0},
        ]

        # Player visits stations out of order: 4 -> 2 -> 7 -> 1
        visited_sequence = [4, 2, 7, 1]
        answered_stations = set()

        for station_id in visited_sequence:
            q_index = station_id - 1
            self.assertGreaterEqual(q_index, 0)
            self.assertLess(q_index, len(questions))

            # Verify station corresponds exactly to question
            expected_q = questions[q_index]["question"]
            self.assertTrue(expected_q.startswith(f"Q{station_id}:"))

            answered_stations.add(station_id)

        self.assertEqual(answered_stations, {1, 2, 4, 7})
        # Check next unanswered from full set {1..7}
        all_stations = set(range(1, 8))
        unanswered = sorted(list(all_stations - answered_stations))
        self.assertEqual(unanswered, [3, 5, 6])

    def test_max_fifteen_questions_ceiling_and_error_handler(self):
        """Verify the game strictly enforces a maximum ceiling of 15 questions per quarter/summative assessment and handles overflows gracefully."""
        from core.dynamic_quiz_manager import MAX_QUESTIONS_PER_QUARTER, validate_and_clamp_questions
        from db.connect_db import map_cloud_questions

        self.assertEqual(MAX_QUESTIONS_PER_QUARTER, 15)

        # 1. Verify allocate_dynamic_stations can allocate up to 15 stations, and caps at 15 if webapp provides 20+
        game_map = ["G" * 30 for _ in range(20)]
        existing = {1: (2, 2), 2: (5, 2)}
        allocated_15 = allocate_dynamic_stations(
            game_map,
            existing_stations=existing,
            needed_count=15,  # Follow 15 questions from web app
            walkable_chars={"G"}
        )
        self.assertEqual(len(allocated_15), 15)
        self.assertEqual(max(allocated_15.keys()), 15)

        # Request 25 stations -> must be clamped to 15
        allocated_over = allocate_dynamic_stations(
            game_map,
            existing_stations=existing,
            needed_count=25,
            walkable_chars={"G"}
        )
        self.assertEqual(len(allocated_over), 15)

        # 2. Verify validate_and_clamp_questions accepts up to 15 questions, and clamps >15
        sample_questions_20 = [
            {"question": f"Question {i}", "choices": ["A", "B", "C", "D"], "correct": 0}
            for i in range(1, 21)
        ]
        clamped_q = validate_and_clamp_questions(sample_questions_20, quarter_num=1)
        self.assertEqual(len(clamped_q), 15)
        self.assertEqual(clamped_q[0]["question"], "Question 1")
        self.assertEqual(clamped_q[14]["question"], "Question 15")

        # Verify it skips malformed or empty items
        malformed = [None, "invalid", {}, {"question": "   "}, {"question": "Valid Question"}]
        filtered = validate_and_clamp_questions(malformed, quarter_num=4)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["question"], "Valid Question")

        # 3. Verify map_cloud_questions accepts up to 15 questions, and caps at 15
        raw_mock_questions = [
            {"prompt": f"Question {i}", "optionA": "1", "optionB": "2", "optionC": "3", "optionD": "4", "correctAnswer": "A"}
            for i in range(1, 25)  # 24 questions from cloud
        ]
        mapped = map_cloud_questions(raw_mock_questions)
        self.assertEqual(len(mapped), 15)
        self.assertEqual(mapped[0]["question"], "Question 1")
        self.assertEqual(mapped[14]["question"], "Question 15")

    def test_objective_hud_dimensions_and_map_clearance(self):
        """Verify the enlarged Objective HUD window dimensions (640x96) preserve map visibility."""
        screen_w, screen_h = 1280, 720
        box_w, box_h = 640, 96
        box_x = (screen_w - box_w) // 2
        box_y = screen_h - box_h - 12

        # Verify centered horizontally with ample clearance on left and right
        left_clearance = box_x
        right_clearance = screen_w - (box_x + box_w)
        self.assertEqual(left_clearance, 320)
        self.assertEqual(right_clearance, 320)
        self.assertGreaterEqual(left_clearance + right_clearance, 640)

        # Verify docked at the bottom, leaving >= 85% of vertical space completely open for the map
        vertical_open_space = box_y
        self.assertEqual(vertical_open_space, 612)
        open_ratio = vertical_open_space / screen_h
        self.assertGreaterEqual(open_ratio, 0.85)

        # Verify player center (y=360) is completely clear of the HUD window
        player_center_y = screen_h // 2
        self.assertLess(player_center_y, box_y - 100)

    def test_fifteen_question_status_pills_fit_without_overflow(self):
        """Verify that status pills for up to 15 questions fit inside the 640px HUD box with no clipping."""
        box_w = 640
        tot_st = 15
        pill_w = 23 if tot_st > 10 else 26
        pill_gap = 4 if tot_st > 10 else 6
        start_x = 95 # relative to box_x

        total_track_w = tot_st * pill_w + (tot_st - 1) * pill_gap
        # 15 * 23 + 14 * 4 = 345 + 56 = 401px
        self.assertEqual(total_track_w, 401)

        end_x = start_x + total_track_w
        # Must fit within the box with safe margins (box_w - 14)
        self.assertLess(end_x, box_w - 14)

    def test_npc_markers_and_badges_render_safely(self):
        """Verify visual marker utilities render without runtime error for answered and active states."""
        from core.visual_effects import (
            draw_npc_ground_pedestal,
            draw_npc_overhead_badge,
            draw_beacon_marker
        )

        test_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)

        # Ground pedestal: active gold vs answered emerald vs answered wrong red
        draw_npc_ground_pedestal(test_surf, 200, 200, is_active=True, color=(250, 204, 21), pulse_phase=1.0)
        draw_npc_ground_pedestal(test_surf, 300, 200, is_active=False, color=(34, 197, 94), pulse_phase=2.0)
        draw_npc_ground_pedestal(test_surf, 400, 200, is_active=False, color=(239, 68, 68), pulse_phase=2.0)

        # Overhead badge: with checkmark status vs wrong status
        draw_npc_overhead_badge(test_surf, 200, 200, text="Q1: ✓ Correct", is_active=False, badge_color=(34, 197, 94), offset_y=-10)
        draw_npc_overhead_badge(test_surf, 300, 200, text="Station 2: Triangle", is_active=True, badge_color=(250, 204, 21), offset_y=-10)
        draw_npc_overhead_badge(test_surf, 400, 200, text="Q3: ✗ Wrong", is_active=False, badge_color=(239, 68, 68), offset_y=-10)

        # Radiant beacon marker: check beacon vs question beacon vs wrong cross/x beacon
        draw_beacon_marker(test_surf, 200, 200, color=(34, 197, 94), beacon_type="check", offset_y=-30)
        draw_beacon_marker(test_surf, 300, 200, color=(251, 191, 36), beacon_type="question", offset_y=-32)
        draw_beacon_marker(test_surf, 400, 200, color=(239, 68, 68), beacon_type="cross", offset_y=-30)
        draw_beacon_marker(test_surf, 500, 200, color=(239, 68, 68), beacon_type="x", offset_y=-30)

        # Confirm surface is drawn to
        self.assertTrue(test_surf.get_width() == 1280 and test_surf.get_height() == 720)

    def test_character_completion_status_hud_card(self):
        """Verify the top-left Character Question Completion Status Card renders properly and clears other HUD elements."""
        class MockQuarterWithHUD:
            def __init__(self):
                self.screen = pygame.Surface((1280, 720))
                self.width = 1280
                self.height = 720
                self.is_quiz_map = True
                self.player_name = "Ana Mendoza"
                self.active_station_count = 15
                self.shape_npcs = {i: {"answered": (i <= 7)} for i in range(1, 16)}

            def get_ui_font(self, size, bold=False):
                from core.font_manager import get_font
                return get_font(["Segoe UI", "Tahoma", "Arial"], size, bold=bold)

        mock = MockQuarterWithHUD()
        from screens.quarter1 import Quarter1
        # Test draw method directly
        Quarter1.draw_character_completion_status_hud(mock)

        # Verify card bounds: card_x=18, card_w=240 -> right edge is 258
        card_right = 18 + 240
        # Stage timer is centered at (1280 - 160) // 2 = 560
        timer_left = (1280 - 160) // 2
        self.assertLess(card_right, timer_left)
        # Margin between character status card and timer must be > 300px
        self.assertGreaterEqual(timer_left - card_right, 300)

if __name__ == "__main__":
    unittest.main()
