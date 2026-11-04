import os
import sys
import unittest
import tempfile
import json
from unittest.mock import MagicMock, patch
import urllib.error

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["COGNITIVE_API_URL"] = "http://127.0.0.1:9/api"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from db.connect_db import Database, map_cloud_questions
from core.report_card import VictoryReportCard
from core.pathfinder_guide import PathfinderGuide
from screens.main_menu import MainMenu
from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4


class TestCloudQuestionSync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(api_base_url="http://127.0.0.1:9/api")
        self.db.cache_dir = self.temp_dir.name

        self.mock_menu = MagicMock()
        self.mock_menu.screen = screen
        self.mock_menu.selected_student = {"id": 1, "student_id": "1001", "first_name": "TestHero"}
        self.mock_menu.student_db_id = 1
        self.mock_menu.audio_manager = MagicMock()

    def tearDown(self):
        self.temp_dir.cleanup()

    # ------------------------------------------------------------------
    # 1. Database.get_questions: Authoritative Empty Cloud Overwrites Cache
    # ------------------------------------------------------------------
    def test_database_syncs_empty_cloud_and_overwrites_cached_questions(self):
        """When teacher deletes all questions in the cloud (HTTP 200 with []),
        local cache must be overwritten with [] and get_questions returns []."""
        cache_path = os.path.join(self.temp_dir.name, "questions_q4.json")
        # Pre-seed stale cache with 6 questions
        stale_data = [{"prompt": f"Stale Q{i}", "correctAnswer": "A"} for i in range(1, 7)]
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(stale_data, f)

        # Mock urllib.request.urlopen returning HTTP 200 with empty list []
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([]).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = self.db.get_questions(quarter=4)

        self.assertEqual(result, [], "Must return empty list [] from authoritative cloud response")
        self.assertTrue(os.path.exists(cache_path))
        with open(cache_path, "r", encoding="utf-8") as f:
            saved_cache = json.load(f)
        self.assertEqual(saved_cache, [], "Stale cache must be cleanly overwritten with []")

        # Now simulate offline mode (URLError) -> should return [] from the updated cache
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Offline")):
            offline_result = self.db.get_questions(quarter=4)
        self.assertEqual(offline_result, [], "Offline get_questions must return [] from synced empty cache")

    # ------------------------------------------------------------------
    # 2. map_cloud_questions Parser Fidelity
    # ------------------------------------------------------------------
    def test_map_cloud_questions_edge_cases(self):
        """Verify that words ending in A-D and numeric choices are not misclassified."""
        raw_rows = [
            {
                "prompt": "What is the measurement of the surface inside a shape?",
                "optionA": "Perimeter",
                "optionB": "Area",
                "optionC": "Volume",
                "optionD": "Length",
                "correctAnswer": "Area",
                "hint": "Think about square units!"
            },
            {
                "prompt": "What is 1 + 1?",
                "optionA": "1",
                "optionB": "2",
                "optionC": "3",
                "optionD": "4",
                "correctAnswer": "2",
                "hint": "Count on your fingers!"
            },
            {
                "prompt": "Which shape is like a diamond?",
                "optionA": "Rhombus",
                "optionB": "Circle",
                "optionC": "Square",
                "optionD": "Triangle",
                "correctAnswer": "Diamond",  # Not in options, should fallback or match safely
                "hint": "Look at the sides!"
            }
        ]

        mapped = map_cloud_questions(raw_rows)
        self.assertEqual(len(mapped), 3)

        # Question 1: correctAnswer is "Area" (ends in 'A'). Must map to optionB (index 1), NOT optionA (0)!
        self.assertEqual(mapped[0]["correct"], 1, "'Area' must match Option B (index 1), not Option A")
        self.assertEqual(mapped[0]["choices"][1], "B. Area")

        # Question 2: correctAnswer is "2". Option B is "2". Must match Option B (index 1), NOT fallback index 2!
        self.assertEqual(mapped[1]["correct"], 1, "'2' must match Option B (index 1), not index 2")

        # Identification support when allow_ident=True
        ident_rows = [{"prompt": "Type the number 5", "correctAnswer": "5"}]
        mapped_ident = map_cloud_questions(ident_rows, allow_ident=True)
        self.assertEqual(mapped_ident[0]["q_type"], "identification")
        self.assertIn("5", mapped_ident[0]["ident_answers"])

    # ------------------------------------------------------------------
    # 3. Quarter 1: Zero Cloud Questions Flexibility
    # ------------------------------------------------------------------
    def test_quarter1_zero_cloud_questions(self):
        """When Quarter 1 has 0 cloud questions:
        - 0 station NPCs spawn
        - River bridge auto-satisfies
        - Old Man dialogue and exit portals are immediately accessible without soft locks."""
        with patch.object(Database, "get_questions", return_value=[]):
            q1 = Quarter1(screen, self.mock_menu, map_name="map1.txt")

        self.assertEqual(q1.active_station_count, 0)
        self.assertEqual(len(q1.quiz_questions), 0)
        self.assertEqual(len(q1.quiz_stations), 0)
        self.assertEqual(len(q1.shape_npcs), 0)
        self.assertEqual(q1.quiz_station_index, 6)

        # Bridge tiles in rows 3 and 4, cols 37..46 must be 'B'
        for col in range(37, 47):
            self.assertEqual(q1.game_map[3][col], 'B')
            self.assertEqual(q1.game_map[4][col], 'B')

        # Portals spawned and accessible
        self.assertGreaterEqual(len(q1.portals), 1)

        # Objectives panel and update/draw run cleanly
        q1.update()
        q1.draw()

    # ------------------------------------------------------------------
    # 4. Quarter 2: Zero Cloud Questions Flexibility
    # ------------------------------------------------------------------
    def test_quarter2_zero_cloud_questions(self):
        """When Quarter 2 has 0 cloud questions:
        - 0 stall NPCs spawn
        - Bahay Kubo is fully built (5/5 pieces)
        - Knight Guardian Currency Trial is directly accessible."""
        with patch.object(Database, "get_questions", return_value=[]):
            q2 = Quarter2(screen, self.mock_menu, map_name="map5.txt")

        self.assertEqual(q2.active_station_count, 0)
        self.assertEqual(len(q2.quiz_questions), 0)
        self.assertEqual(len(q2.quiz_stations), 0)
        self.assertEqual(len(q2.station_npc_info), 0)
        self.assertEqual(q2.quiz_station_index, 6)
        self.assertEqual(q2.kubo_pieces_collected, 5)
        self.assertTrue(q2.kubo_built)
        self.assertEqual(q2.guardian_knight_state, 1)
        self.assertIn("NO CLOUD QUESTIONS", q2.banner_text)

        q2.update()
        q2.draw()

    # ------------------------------------------------------------------
    # 5. Quarter 3: Zero Cloud Questions Flexibility
    # ------------------------------------------------------------------
    def test_quarter3_zero_cloud_questions(self):
        """When Quarter 3 has 0 cloud questions:
        - 0 station NPCs spawn
        - Aqueduct bridge tiles are all 'B'
        - Skeleton Guardian Fraction Bakery is directly accessible."""
        with patch.object(Database, "get_questions", return_value=[]):
            q3 = Quarter3(screen, self.mock_menu, map_name="map8.txt")

        self.assertEqual(q3.active_station_count, 0)
        self.assertEqual(len(q3.quiz_questions), 0)
        self.assertEqual(len(q3.quiz_stations), 0)
        self.assertEqual(len(q3.station_npcs), 0)
        self.assertEqual(q3.quiz_station_index, 6)
        self.assertEqual(q3.guardian_skeleton_state, 1)

        for bx, by in q3.bridge_tiles:
            self.assertEqual(q3.game_map[by][bx], 'B')
            self.assertEqual(q3.render_map[by][bx], 'B')

        self.assertIn("NO CLOUD QUESTIONS", q3.caravan_upgrade_banner_text)

        q3.update()
        q3.draw()

    # ------------------------------------------------------------------
    # 6. Quarter 4: Zero Cloud Questions Flexibility (Map 10 & Map 12)
    # ------------------------------------------------------------------
    def test_quarter4_zero_cloud_questions(self):
        """When Quarter 4 has 0 cloud questions:
        - 0 station NPCs spawn
        - PathfinderGuide targets Guardian Bromen directly
        - Map 10: Bromen dialogue triggers Key Puzzle with 6 ceremonial keys
        - Map 12: Raft untethers and sails cleanly to East Pier portal."""
        with patch.object(Database, "get_questions", return_value=[]):
            q4 = Quarter4(screen, self.mock_menu, map_name="map10.txt")

        self.assertEqual(q4.active_station_count, 0)
        self.assertEqual(len(q4.quiz_questions), 0)
        self.assertEqual(len(q4.quiz_stations), 0)
        self.assertEqual(len(q4.station_npcs), 0)

        # PathfinderGuide should target Guardian Bromen directly (not Station 1)
        target = q4.path_guide.get_active_hierarchy_target()
        self.assertIsNotNone(target)
        self.assertEqual(target[2], "Guardian Bromen")

        # Approach Guardian Bromen
        q4.instruction_modal.hide()
        q4.player_x = q4.npc_bromen_x
        q4.player_y = q4.npc_bromen_y
        q4.update()
        self.assertEqual(q4.bromen_dialogue_state, 2)

        # Map 12 Lotus Raft test with 0 questions
        with patch.object(Database, "get_questions", return_value=[]):
            q4_m12 = Quarter4(screen, self.mock_menu, map_name="map12.txt")
        self.assertEqual(q4_m12.active_station_count, 0)
        q4_m12.instruction_modal.hide()
        q4_m12.player_x = q4_m12.npc_bromen_x
        q4_m12.player_y = q4_m12.npc_bromen_y
        q4_m12.update()
        self.assertEqual(q4_m12.bromen_dialogue_state, 2)

        # Solving the addition helm untethers the raft (transitions to ready_to_sail or sails if player is at dock)
        q4_m12.key_puzzle_solved = True
        q4_m12.bromen_dialogue_state = 3
        q4_m12.update()
        self.assertIn(q4_m12.raft_state, ("docked_west", "ready_to_sail", "sailing"))

        q4.draw()
        q4_m12.draw()

    # ------------------------------------------------------------------
    # 7. Partial Cloud Questions Scaling (e.g., 3 Questions)
    # ------------------------------------------------------------------
    def test_partial_cloud_questions_scaling(self):
        """When 3 cloud questions exist:
        - active_station_count == 3
        - Clearing station 3 builds all 5 bridge/kubo segments."""
        mock_3_qs = [
            {"prompt": f"Partial Q{i}", "optionA": "1", "optionB": "2", "optionC": "3", "optionD": "4", "correctAnswer": "A"}
            for i in range(1, 4)
        ]

        # Quarter 1 with 3 questions
        with patch.object(Database, "get_questions", return_value=mock_3_qs):
            q1 = Quarter1(screen, self.mock_menu, map_name="map1.txt")
        self.assertEqual(q1.active_station_count, 3)
        self.assertEqual(len(q1.quiz_stations), 3)

        # Quarter 2 with 3 questions
        with patch.object(Database, "get_questions", return_value=mock_3_qs):
            q2 = Quarter2(screen, self.mock_menu, map_name="map5.txt")
        self.assertEqual(q2.active_station_count, 3)
        self.assertEqual(len(q2.quiz_stations), 3)

        # Quarter 3 with 3 questions
        with patch.object(Database, "get_questions", return_value=mock_3_qs):
            q3 = Quarter3(screen, self.mock_menu, map_name="map8.txt")
        self.assertEqual(q3.active_station_count, 3)
        self.assertEqual(len(q3.quiz_stations), 3)

        # Quarter 4 with 3 questions
        with patch.object(Database, "get_questions", return_value=mock_3_qs):
            q4 = Quarter4(screen, self.mock_menu, map_name="map10.txt")
        self.assertEqual(q4.active_station_count, 3)
        self.assertEqual(len(q4.quiz_stations), 3)

    # ------------------------------------------------------------------
    # 8. VictoryReportCard & Grade Upload Skip for 0 Cloud Questions
    # ------------------------------------------------------------------
    def test_victory_report_card_and_save_skip_when_zero_questions(self):
        """VictoryReportCard handles total_questions=0 cleanly with 3 stars and 100%,
        and saving results does not upload 0/0 score to the database."""
        card = VictoryReportCard(screen, 1280, 720, self.mock_menu)
        card.show(total_questions=0, correct_first_try=0, score=100)
        self.assertTrue(card.no_cloud_questions)
        self.assertEqual(card.percentage, 100.0)
        self.assertEqual(card.stars_earned, 3)
        self.assertEqual(card.score, 100)

        # Draw report card without error
        card.draw(screen)

        # Verify that _run_save_results_to_database and _run_save_quarter4_game_result skip db.save_game_result
        mock_db = MagicMock()
        with patch("screens.quarter1.db", mock_db), patch.object(Database, "get_questions", return_value=[]):
            q1 = Quarter1(screen, self.mock_menu, map_name="map1.txt")
            q1._run_save_results_to_database()
            mock_db.save_game_result.assert_not_called()

        with patch("screens.quarter4.db", mock_db), patch.object(Database, "get_questions", return_value=[]):
            q4 = Quarter4(screen, self.mock_menu, map_name="map10.txt")
            q4._run_save_quarter4_game_result()
            mock_db.save_game_result.assert_not_called()


if __name__ == "__main__":
    unittest.main()
