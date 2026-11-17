import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
from unittest.mock import MagicMock
import pygame

from core.dynamic_quiz_manager import allocate_dynamic_stations
from screens.quarter3 import Quarter3

class TestQuarter3Bridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def test_allocate_dynamic_stations_map8_no_stations_across_bridge(self):
        """Test that dynamic stations on map8.txt are never placed across the bridge (x >= 40, y <= 14)."""
        with open("assets/map/Quarter3Maps/map8.txt", "r") as f:
            game_map = [line.rstrip() for line in f]

        bridge_tiles = [(40, 7), (41, 7), (42, 7), (43, 7), (44, 7)]
        for bx, by in bridge_tiles:
            game_map[by] = game_map[by][:bx] + "w" + game_map[by][bx+1:]

        stations = {
            1: (33, 18),
            2: (14, 18),
            3: (3, 11),
            4: (3, 3),
            5: (35, 3),
        }

        forbidden = set(bridge_tiles)
        for fx in range(40, len(game_map[0])):
            for fy in range(0, min(15, len(game_map))):
                forbidden.add((fx, fy))

        allocated = allocate_dynamic_stations(
            game_map,
            stations,
            10,
            forbidden_tiles=forbidden
        )

        self.assertEqual(len(allocated), 10)
        for sid, (sx, sy) in allocated.items():
            self.assertFalse(
                sx >= 40 and sy <= 14,
                f"Station {sid} at ({sx}, {sy}) was placed across the unbuilt bridge!"
            )

    def test_quarter3_map8_reachability_from_player_start(self):
        """Test that all 10 allocated stations are in the same walkable connected component as the player start."""
        with open("assets/map/Quarter3Maps/map8.txt", "r") as f:
            game_map = [line.rstrip() for line in f]

        bridge_tiles = [(40, 7), (41, 7), (42, 7), (43, 7), (44, 7)]
        for bx, by in bridge_tiles:
            game_map[by] = game_map[by][:bx] + "w" + game_map[by][bx+1:]

        stations = {
            1: (33, 18),
            2: (14, 18),
            3: (3, 11),
            4: (3, 3),
            5: (35, 3),
        }

        forbidden = set(bridge_tiles)
        for fx in range(40, len(game_map[0])):
            for fy in range(0, min(15, len(game_map))):
                forbidden.add((fx, fy))

        allocated = allocate_dynamic_stations(
            game_map,
            stations,
            10,
            forbidden_tiles=forbidden
        )

        # BFS from player start (47, 18)
        walkable_chars = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "9", "P", "B", "r", "l", "u", "d"}
        player_start = (47, 18)
        visited = set([player_start])
        queue = [player_start]
        rows = len(game_map)

        while queue:
            cx, cy = queue.pop(0)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < rows and 0 <= nx < len(game_map[ny]):
                    if (nx, ny) not in visited and game_map[ny][nx] in walkable_chars:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        for sid, pos in allocated.items():
            self.assertIn(
                pos,
                visited,
                f"Station {sid} at {pos} is not pathfindable from player start!"
            )

    def test_quarter3_bridge_completion_after_all_stations_solved(self):
        """Simulate solving all stations and verify bridge tiles are converted to 'B' (walkable)."""
        tot_st = 10
        bridge_tiles = [(40, 7), (41, 7), (42, 7), (43, 7), (44, 7)]
        game_map = ["G" * 50 for _ in range(20)]
        for bx, by in bridge_tiles:
            game_map[by] = game_map[by][:bx] + "w" + game_map[by][bx+1:]

        built_bridge_count = 0
        answered_stations = set()

        for st in range(1, tot_st + 1):
            answered_stations.add(st)
            ans_count = len(answered_stations)
            target_bridges = max(1, min(len(bridge_tiles), int(round(ans_count * len(bridge_tiles) / float(tot_st)))))
            if ans_count >= tot_st:
                target_bridges = len(bridge_tiles)
            if target_bridges > built_bridge_count:
                for b_idx in range(built_bridge_count, target_bridges):
                    bx, by = bridge_tiles[b_idx]
                    game_map[by] = game_map[by][:bx] + "B" + game_map[by][bx+1:]
                built_bridge_count = target_bridges

        self.assertEqual(built_bridge_count, len(bridge_tiles))
        for bx, by in bridge_tiles:
            self.assertEqual(game_map[by][bx], "B")

    def test_quarter3_instance_dynamic_sync_isolation(self):
        """Instantiate Quarter3 on map8.txt, sync 10 questions, and assert all stations are mainland."""
        mock_menu = MagicMock()
        mock_menu.screen = self.screen
        mock_menu.audio_manager = MagicMock()
        mock_menu.selected_student = {"id": 1, "name": "Tester"}

        q3 = Quarter3(self.screen, mock_menu, map_name="map8.txt", summative_num=1)
        fake_questions = [
            {"id": i, "question": f"Question {i}", "choices": ["A", "B", "C", "D"], "answer": "A", "station": i}
            for i in range(1, 11)
        ]
        q3.cloud_sync_quarter3_questions(fake_questions)

        self.assertEqual(len(q3.quiz_stations), 10)
        for sid, (sx, sy) in q3.quiz_stations.items():
            self.assertFalse(
                sx >= 40 and sy <= 14,
                f"Quarter3 Station {sid} spawned across the bridge at ({sx}, {sy})!"
            )

if __name__ == "__main__":
    unittest.main()
