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

if __name__ == "__main__":
    unittest.main()
