# tests/test_quarter_pathfinding_guide.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
import pygame
from core.pathfinder_guide import QuestPathfinderGuide, THEME_TRAIL_COLORS, STATION_NAMES

class MockQuarter:
    def __init__(self, quarter_id="quarter1", map_name="map1.txt"):
        self.screen = pygame.Surface((1280, 720))
        self.width = 1280
        self.height = 720
        self.quarter_id = quarter_id
        self.map_name = map_name
        self.player_x = 32 * 2
        self.player_y = 32 * 2
        self.camera_x = 0
        self.camera_y = 0
        self.quiz_station_index = 1
        self.quiz_state = 0
        self.quiz_stations = {
            1: (5, 5),
            2: (10, 5),
            3: (15, 8),
            4: (20, 10),
            5: (25, 12)
        }
        self.npc_oldman_found = True
        self.npc_oldman_tile_x = 30
        self.npc_oldman_tile_y = 5
        self.oldman_riddle_answered = False
        self.portal_tile_x = 35
        self.portal_tile_y = 5
        self.portals = []

        # Simple 15x40 walkable map
        self.ROWS = 15
        self.COLS = 40
        self.game_map = ["G" * self.COLS for _ in range(self.ROWS)]
        self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "P", "B", "r", "l", "u", "d"}

class TestQuarterPathfindingGuide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_theme_palettes_exist(self):
        for theme in ["forest", "fiesta", "desert", "water"]:
            self.assertIn(theme, THEME_TRAIL_COLORS)
            self.assertIn("trail", THEME_TRAIL_COLORS[theme])
            self.assertIn("glow", THEME_TRAIL_COLORS[theme])
            self.assertIn("chevron", THEME_TRAIL_COLORS[theme])

    def test_station_names_hierarchy(self):
        for qid in ["quarter1", "quarter2", "quarter3", "quarter4"]:
            self.assertIn(qid, STATION_NAMES)
            self.assertTrue(len(STATION_NAMES[qid]) >= 5)

    def test_hierarchy_target_progression(self):
        mock_q = MockQuarter(quarter_id="quarter1", map_name="map1.txt")
        guide = QuestPathfinderGuide(mock_q, quarter_id="quarter1", theme="forest")

        # Step 1: Target should be Station 1
        target = guide.get_active_hierarchy_target()
        self.assertIsNotNone(target)
        self.assertEqual((target[0], target[1]), (5, 5))
        self.assertEqual(target[2], "Circle Guardian")

        # Step 2: Advance to Station 2
        mock_q.quiz_station_index = 2
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (10, 5))
        self.assertEqual(target[2], "Heart Guardian")

        # Step 3: Advance through all stations to Old Man
        mock_q.quiz_station_index = 6
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (30, 5))
        self.assertIn("Mentor", target[2])

        # Step 4: After Riddle solved, target is Goal Portal (Portal to Map 2)
        mock_q.oldman_riddle_answered = True
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (35, 5))
        self.assertIn("Portal", target[2])

    def test_bfs_pathfinding_and_trail_generation(self):
        mock_q = MockQuarter(quarter_id="quarter2", map_name="map4.txt")
        guide = QuestPathfinderGuide(mock_q, quarter_id="quarter2", theme="fiesta")

        # Create an obstacle wall in the middle
        # Row 3 to 10 has a wall at col 7 with a gap at row 8
        for r in range(3, 11):
            if r != 8:
                row_list = list(mock_q.game_map[r])
                row_list[7] = 'X'  # Non-walkable obstacle
                mock_q.game_map[r] = "".join(row_list)

        path = guide.find_walkable_path((2, 2), (10, 5))
        self.assertTrue(len(path) > 2)
        self.assertEqual(path[0], (2, 2))
        self.assertEqual(path[-1], (10, 5))

        # Check update and simplify
        guide.update(0.016)
        self.assertTrue(len(guide.cached_path_world) >= 2)

        # Check drawing without throwing exceptions
        guide.draw()

    def test_stage_select_hierarchy_progression(self):
        class MockStageSelect:
            def __init__(self):
                self.screen = pygame.Surface((1280, 720))
                self.width = 1280
                self.height = 720
                self.player_x = 32 * 26
                self.player_y = 32 * 13
                self.camera_x = 0
                self.camera_y = 0
                self.completed = {"quarter1": False, "quarter2": False, "quarter3": False, "quarter4": False}
                self.oldman_dialogue_state = 0
                self.knight_dialogue_state = 0
                self.skeleton_dialogue_state = 0
                self.bromen_dialogue_state = 0
                self.npc_oldman_tile_x = 5
                self.npc_oldman_tile_y = 12
                self.npc_knight_tile_x = 25
                self.npc_knight_tile_y = 23
                self.npc_skeleton_tile_x = 47
                self.npc_skeleton_tile_y = 12
                self.npc_bromen_tile_x = 25
                self.npc_bromen_tile_y = 3

                class MockPortal:
                    def __init__(self, x, y, direction):
                        self.x = x
                        self.y = y
                        self.direction = direction

                self.portals = [
                    MockPortal(0, 12, 'left'),
                    MockPortal(25, 25, 'up'),
                    MockPortal(52, 12, 'right'),
                    MockPortal(25, 0, 'down')
                ]
                self.game_map = ["G" * 54 for _ in range(27)]
                self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "P", "l", "r", "u", "d"}

            def is_quarter_completed(self, qid):
                return self.completed.get(qid, False)

        ss = MockStageSelect()
        guide = QuestPathfinderGuide(ss, quarter_id="stageselect", theme="forest")

        # Step 1: Initial state -> Old Man (Q1 Guide)
        target = guide.get_active_hierarchy_target()
        self.assertIsNotNone(target)
        self.assertEqual((target[0], target[1]), (5, 12))
        self.assertIn("Old Man", target[2])

        # Step 1b: Talked to Old Man -> Q1 Portal
        ss.oldman_dialogue_state = 1
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (0, 12))
        self.assertIn("Quarter 1", target[2])

        # Step 2: Quarter 1 completed -> Knight (Q2 Guardian)
        ss.completed["quarter1"] = True
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (25, 23))
        self.assertIn("Knight", target[2])

        # Step 2b: Talked to Knight -> Q2 Portal
        ss.knight_dialogue_state = 1
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (25, 25))
        self.assertIn("Quarter 2", target[2])

        # Step 3: Quarter 2 completed -> Skeleton (Q3 Guardian)
        ss.completed["quarter2"] = True
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (47, 12))
        self.assertIn("Skeleton", target[2])

        # Step 3b: Talked to Skeleton -> Q3 Portal
        ss.skeleton_dialogue_state = 1
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (52, 12))
        self.assertIn("Quarter 3", target[2])

        # Step 4: Quarter 3 completed -> Bromen (Q4 Guardian)
        ss.completed["quarter3"] = True
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (25, 3))
        self.assertIn("Bromen", target[2])

        # Step 4b: Talked to Bromen -> Q4 Portal
        ss.bromen_dialogue_state = 1
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (25, 0))
        self.assertIn("Quarter 4", target[2])

        # Step 5: All completed -> Victory Sanctuary
        ss.completed["quarter4"] = True
        target = guide.get_active_hierarchy_target()
        self.assertEqual((target[0], target[1]), (5, 12))
        self.assertIn("Sanctuary", target[2])

    def test_quarter1_map_specific_targets(self):
        class MockQ1Map:
            def __init__(self, map_name):
                self.screen = pygame.Surface((1280, 720))
                self.width = 1280
                self.height = 720
                self.map_name = map_name
                self.player_x = 32 * 51
                self.player_y = 32 * 18
                self.camera_x = 0
                self.camera_y = 0
                self.quiz_station_index = 6
                self.quiz_state = 0
                self.quiz_stations = {1: (47, 18), 2: (52, 13), 3: (26, 7), 4: (1, 3), 5: (24, 4)}
                self.npc_oldman_tile_x = 49
                self.npc_oldman_tile_y = 2
                self.oldman_riddle_answered = False
                self.puzzle_solved = False

                class MockPortal:
                    def __init__(self, x, y):
                        self.x = x
                        self.y = y

                self.portals = [MockPortal(52, 3)]
                self.locked_portals = []
                self.game_map = ["G" * 54 for _ in range(20)]
                self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "P", "B", "r", "l", "u", "d"}

        # Map 1: Stations finished, riddle unanswered -> Old Man at (49, 2)
        q1_map1 = MockQ1Map("map1.txt")
        guide1 = QuestPathfinderGuide(q1_map1, quarter_id="quarter1", theme="forest")
        t1 = guide1.get_active_hierarchy_target()
        self.assertEqual((t1[0], t1[1]), (49, 2))
        self.assertEqual(t1[2], "Forest Mentor (Old Man)")

        # Map 1: Riddle answered -> Portal to Map 2 at (52, 3) (NOT (1, 0)!)
        q1_map1.oldman_riddle_answered = True
        t1_portal = guide1.get_active_hierarchy_target()
        self.assertEqual((t1_portal[0], t1_portal[1]), (52, 3))
        self.assertEqual(t1_portal[2], "Portal to Map 2")

    def test_all_quarters_integration(self):
        for qid, theme, map_file in [
            ("quarter1", "forest", "map1.txt"),
            ("quarter2", "fiesta", "map4.txt"),
            ("quarter3", "desert", "map7.txt"),
            ("quarter4", "water", "map10.txt"),
            ("stageselect", "forest", "map.txt")
        ]:
            mock_q = MockQuarter(quarter_id=qid, map_name=map_file)
            if qid == "quarter4":
                mock_q.quiz_stations[6] = (28, 14)
            guide = QuestPathfinderGuide(mock_q, quarter_id=qid, theme=theme)
            target = guide.get_active_hierarchy_target()
            self.assertIsNotNone(target)
            guide.update(0.016)
            guide.draw()

if __name__ == "__main__":
    unittest.main()

