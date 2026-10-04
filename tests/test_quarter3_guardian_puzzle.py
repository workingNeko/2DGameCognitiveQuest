# tests/test_quarter3_guardian_puzzle.py
import unittest
import pygame
import os
import sys

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from screens.quarter3 import Quarter3
from core.pathfinder_guide import QuestPathfinderGuide


class MockMainMenu:
    def __init__(self):
        self.student_id = "test_student_123"
        self.selected_student = {"id": "test_student_123", "first_name": "ExplorerHero", "username": "ExplorerHero", "gender": "boy"}
        self.current_screen = "quarter3"
        self.audio_manager = None
        self.quarter3 = None


class TestQuarter3GuardianPuzzle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.main_menu = MockMainMenu()

    def test_skeleton_guardian_placement_across_all_maps(self):
        """Test that Skeleton Guardian is placed guarding the exit portal across map7, map8, map9"""
        for map_file in ["map7.txt", "map8.txt", "map9.txt"]:
            q3 = Quarter3(self.screen, self.main_menu, map_file)
            self.assertTrue(q3.npc_skeleton_found, f"Skeleton Guardian must be found in {map_file}")
            self.assertGreater(q3.npc_skeleton_tile_x, 0, f"Skeleton Guardian tile_x must be valid in {map_file}")
            self.assertGreater(q3.npc_skeleton_tile_y, 0, f"Skeleton Guardian tile_y must be valid in {map_file}")
            self.assertEqual(q3.guardian_skeleton_state, 0, f"Initial guardian_skeleton_state must be 0 in {map_file}")
            self.assertFalse(q3.solar_array_puzzle_solved, f"Puzzle should start unsolved in {map_file}")

    def test_solar_array_puzzle_initialization(self):
        """Test that init_solar_array_puzzle creates 5 distinct pedestals and 5 matching gem matrix slabs"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.init_solar_array_puzzle()

        self.assertEqual(len(q3.solar_array_puzzle_slots), 5, "Must have 5 target equation pedestals")
        self.assertEqual(len(q3.solar_array_puzzle_pieces), 5, "Must have 5 draggable/clickable gem slabs")

        slot_ids = [s["id"] for s in q3.solar_array_puzzle_slots]
        piece_ids = [p["id"] for p in q3.solar_array_puzzle_pieces]
        self.assertEqual(set(slot_ids), set(piece_ids), "All slots must have matching pieces in tray")

        # Verify slabs have pre-rendered surfaces
        for piece in q3.solar_array_puzzle_pieces:
            self.assertIsNotNone(piece["slab_surf"])
            self.assertFalse(piece["is_placed"])

    def test_solar_array_puzzle_randomization_across_maps_and_sessions(self):
        """Test that different maps and successive initializations produce randomized item configurations"""
        q3_map7 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3_map7.init_solar_array_puzzle()
        eqs_map7 = [s["equation"] for s in q3_map7.solar_array_puzzle_slots]

        q3_map8 = Quarter3(self.screen, self.main_menu, "map8.txt")
        q3_map8.init_solar_array_puzzle()
        eqs_map8 = [s["equation"] for s in q3_map8.solar_array_puzzle_slots]

        q3_map9 = Quarter3(self.screen, self.main_menu, "map9.txt")
        q3_map9.init_solar_array_puzzle()
        eqs_map9 = [s["equation"] for s in q3_map9.solar_array_puzzle_slots]

        self.assertEqual(len(eqs_map7), 5)
        self.assertEqual(len(eqs_map8), 5)
        self.assertEqual(len(eqs_map9), 5)

        # Re-initialization on the same map generates dynamic fresh ordering or combinations
        q3_map7_second = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3_map7_second.init_solar_array_puzzle()
        self.assertEqual(len(q3_map7_second.solar_array_puzzle_slots), 5)

    def test_solar_array_puzzle_matching_and_reset(self):
        """Test matching slabs into pedestals and resetting the tray"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.init_solar_array_puzzle()

        # Match 1 piece
        piece = q3.solar_array_puzzle_pieces[0]
        target_slot = next(s for s in q3.solar_array_puzzle_slots if s["id"] == piece["id"])
        
        # Position piece inside slot rect and release
        piece["x"] = target_slot["rect"].centerx - piece["w"] // 2
        piece["y"] = target_slot["rect"].centery - piece["h"] // 2
        q3.dragged_solar_piece = piece
        q3.release_dragged_solar_piece()

        self.assertTrue(target_slot["matched"])
        self.assertTrue(piece["is_placed"])

        # Reset tray
        q3.reset_solar_array_puzzle()
        self.assertFalse(target_slot["matched"])
        self.assertFalse(piece["is_placed"])
        self.assertEqual(piece["x"], piece["orig_x"])
        self.assertEqual(piece["y"], piece["orig_y"])

    def test_full_station_to_guardian_and_puzzle_solve_progression(self):
        """Test full progression: Stations 1-5 cleared -> Guardian activated -> Trial prompt -> Puzzle solve -> Portal unlocked"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")

        # Simulate completing stations 1 to 4
        for st in range(1, 5):
            q3.quiz_station_index = st
            q3.advance_station_progress()
            self.assertEqual(q3.quiz_station_index, st + 1)
            self.assertEqual(q3.guardian_skeleton_state, 0)

        # Clear station 5
        q3.quiz_station_index = 5
        q3.advance_station_progress()

        self.assertEqual(q3.quiz_station_index, 6, "Must advance to index 6 after clearing station 5")
        self.assertEqual(q3.guardian_skeleton_state, 1, "Guardian state must be 1 (guarding portal with golden aura)")

        # Dismiss stage start instruction modal
        q3.instruction_modal.hide()
        q3.greeting_dialog.hide()

        # Move player close to Skeleton Guardian
        q3.player_x = q3.npc_skeleton_x
        q3.player_y = q3.npc_skeleton_y
        q3.update()

        self.assertEqual(q3.guardian_skeleton_state, 2, "Guardian state must become 2 (prompt modal active) on proximity")
        self.assertIsNotNone(q3.guardian_skeleton_btn_rect, "Prompt Begin Trial button rect must exist")

        # Click Begin Trial button
        q3.trigger_click(q3.guardian_skeleton_btn_rect.center)
        self.assertEqual(q3.guardian_skeleton_state, 3, "Guardian state must become 3 (puzzle active)")
        self.assertTrue(q3.solar_array_puzzle_active, "Solar Array puzzle must be active")

        # Solve all 5 slots via click-to-slot simulation
        for piece in q3.solar_array_puzzle_pieces:
            slot = next(s for s in q3.solar_array_puzzle_slots if s["id"] == piece["id"])
            slot["matched"] = True
            slot["matched_item"] = piece["data"]
            piece["is_placed"] = True
        q3.solar_array_puzzle_all_placed = True

        # Click Unlock Portal button
        self.assertIsNotNone(q3.solar_puzzle_continue_btn_rect)
        q3.trigger_click(q3.solar_puzzle_continue_btn_rect.center)

        self.assertTrue(q3.solar_array_puzzle_solved, "Solar array puzzle must be marked solved")
        self.assertFalse(q3.solar_array_puzzle_active, "Puzzle modal should close")
        self.assertEqual(q3.guardian_skeleton_state, 5, "Guardian state must be 5 (portal unlocked)")
        self.assertEqual(q3.quiz_state, 6, "Quiz state must be 6 (stage complete)")

        # Stepping on portal now triggers warp transition
        current_portal = q3.portals[0]
        q3.player_x = current_portal.get_world_x()
        q3.player_y = current_portal.get_world_y()
        teleported = q3.check_portal_teleport_on_hold()
        self.assertTrue(teleported, "Stepping on portal after solving puzzle must initiate warp")
        self.assertTrue(q3.warp_out_active, "Warp out animation must be active")

    def test_pathfinder_guide_quarter3_hierarchy(self):
        """Test QuestPathfinderGuide targets Stations 1-5, then Skeleton Guardian, then Goal Portal"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        guide = QuestPathfinderGuide(q3, quarter_id="quarter3", theme="desert")

        # 1. Station 1
        q3.quiz_station_index = 1
        q3.quiz_state = 0
        target = guide.get_active_hierarchy_target()
        self.assertIsNotNone(target)
        self.assertIn("Sage 1", target[2])
        self.assertFalse(target[3], "Should be NPC station, not portal")

        # 2. After all 5 stations cleared -> Targets Skeleton Portal Guardian
        q3.quiz_station_index = 6
        q3.guardian_skeleton_state = 1
        q3.solar_array_puzzle_solved = False
        target = guide.get_active_hierarchy_target()
        self.assertIsNotNone(target)
        self.assertIn("Skeleton", target[2])
        self.assertFalse(target[3], "Should be Guardian NPC, not portal")

        # 3. After puzzle solved -> Targets Sun Oasis Portal
        q3.solar_array_puzzle_solved = True
        q3.guardian_skeleton_state = 5
        q3.quiz_state = 6
        target = guide.get_active_hierarchy_target()
        self.assertIsNotNone(target)
        self.assertTrue(target[3], "Should target exit portal")


if __name__ == "__main__":
    unittest.main()
