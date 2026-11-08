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
        cls.screen = pygame.display.set_mode((1280, 720), pygame.HIDDEN)

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
        """Test that init_solar_array_puzzle initializes the 4-Card Sun Temple Fraction Match cleanly"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.init_solar_array_puzzle()

        self.assertEqual(len(q3.solar_array_puzzle_slots), 4, "Must have 4 target fraction slots")
        self.assertEqual(len(q3.solar_array_puzzle_pieces), 4, "Must have 4 draggable visual fraction cards")

        # Ensure all 4 sampled fractions are non-equivalent values (no 1/2 + 2/4 collision)
        values = [round(s["data"]["num"] / s["data"]["denom"], 4) for s in q3.solar_array_puzzle_slots]
        self.assertEqual(len(values), len(set(values)), "All 4 sampled fractions in a round must be non-equivalent")

        # Verify zero Measurement & Time content in pool or active slots
        banned_time_words = ("minute", "hour", "clock", "sundial", "60 min")
        for item in q3.SUN_TEMPLE_FRACTION_POOL:
            combined = f"{item['fraction_str']} {item['word_name']} {item['parts_hint']} {item['desc']}".lower()
            for bw in banned_time_words:
                self.assertNotIn(bw, combined, f"Measurement & Time term '{bw}' must not appear in Quarter 3 pool")

        # Verify pieces and slots have pre-baked surfaces and valid initial state
        for slot in q3.solar_array_puzzle_slots:
            self.assertIsNotNone(slot["empty_surf"])
            self.assertIsNotNone(slot["hover_surf"])
            self.assertIsNotNone(slot["matched_surf"])
            self.assertFalse(slot["matched"])

        for piece in q3.solar_array_puzzle_pieces:
            self.assertIsNotNone(piece["gem_surf"])
            self.assertIsNotNone(piece["token_surf"])
            self.assertIsNotNone(piece["hover_surf"])
            self.assertIsNotNone(piece["selected_surf"])
            self.assertIsNotNone(piece["placed_surf"])
            self.assertFalse(piece["is_placed"])

    def test_solar_array_puzzle_randomization_across_maps_and_sessions(self):
        """Test that map7, map8, and map9 all initialize unified 4-card Sun Temple Fraction Match rounds"""
        for map_file in ["map7.txt", "map8.txt", "map9.txt"]:
            q3_map = Quarter3(self.screen, self.main_menu, map_file)
            q3_map.init_solar_array_puzzle()
            self.assertIn("=", q3_map.solar_array_target_equation)
            self.assertEqual(len(q3_map.solar_array_puzzle_slots), 4)
            self.assertEqual(len(q3_map.solar_array_puzzle_pieces), 4)

    def test_solar_array_puzzle_matching_and_reset(self):
        """Test wrong-slot bounce-back, matching visual fraction card to target slot, and resetting tray"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.init_solar_array_puzzle()

        target_slot = q3.solar_array_puzzle_slots[0]
        matching_piece = next(p for p in q3.solar_array_puzzle_pieces if p["id"] == target_slot["id"])
        wrong_slot = next(s for s in q3.solar_array_puzzle_slots if s["id"] != matching_piece["id"])

        # 1. Dropping card onto a non-matching slot must bounce back to tray
        handled = q3.handle_solar_array_mouse_down((matching_piece["x"] + 5, matching_piece["y"] + 5))
        self.assertTrue(handled, "Mouse down on visual fraction card should initiate drag")
        self.assertEqual(q3.dragged_solar_piece, matching_piece)

        matching_piece["x"] = wrong_slot["rect"].centerx - matching_piece["w"] // 2
        matching_piece["y"] = wrong_slot["rect"].centery - matching_piece["h"] // 2
        q3.release_dragged_solar_piece()

        self.assertFalse(wrong_slot["matched"], "Wrong slot must not accept non-matching fraction card")
        self.assertFalse(matching_piece["is_placed"], "Card dropped on wrong slot must remain unplaced")
        self.assertEqual((matching_piece["x"], matching_piece["y"]), (matching_piece["orig_x"], matching_piece["orig_y"]))

        # 2. Dragging card onto its matching fraction slot must snap into place
        handled = q3.handle_solar_array_mouse_down((matching_piece["x"] + 5, matching_piece["y"] + 5))
        self.assertTrue(handled)
        matching_piece["x"] = target_slot["rect"].centerx - matching_piece["w"] // 2
        matching_piece["y"] = target_slot["rect"].centery - matching_piece["h"] // 2
        q3.release_dragged_solar_piece()

        self.assertTrue(target_slot["matched"])
        self.assertTrue(matching_piece["is_placed"])

        # 3. Reset tray returns all cards to original tray positions
        q3.reset_solar_array_puzzle()
        self.assertFalse(target_slot["matched"])
        self.assertFalse(matching_piece["is_placed"])
        self.assertEqual(matching_piece["x"], matching_piece["orig_x"])
        self.assertEqual(matching_piece["y"], matching_piece["orig_y"])

    def test_solar_array_puzzle_gesture_drag_and_drop(self):
        """Test MediaPipe closed-fist grab, motion, and open-hand drop into matching fraction slot"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.init_solar_array_puzzle()

        target_slot = q3.solar_array_puzzle_slots[0]
        matching_piece = next(p for p in q3.solar_array_puzzle_pieces if p["id"] == target_slot["id"])

        # Fist closed over matching card
        q3.cursor_pos = (matching_piece["x"] + 10, matching_piece["y"] + 10)
        q3.fist_closed = True
        q3.update_solar_array_puzzle(0.016)
        self.assertEqual(q3.dragged_solar_piece, matching_piece, "Closed fist over card must grab it")

        # Move cursor to matching target slot center
        q3.cursor_pos = target_slot["rect"].center
        q3.update_solar_array_puzzle(0.016)

        # Open fist to drop
        q3.fist_closed = False
        q3.update_solar_array_puzzle(0.016)

        self.assertTrue(target_slot["matched"], "Target fraction slot must match upon gesture drop")
        self.assertTrue(matching_piece["is_placed"], "Card must be marked placed")

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
        self.assertTrue(q3.solar_array_puzzle_active, "Sun Temple Fraction Match must be active")

        # Solve all 4 fraction cards via auto solve
        q3.auto_solve_solar_array_puzzle()
        self.assertTrue(q3.solar_array_puzzle_all_placed)

        # Click Unlock Portal button
        self.assertIsNotNone(q3.solar_puzzle_continue_btn_rect)
        q3.trigger_click(q3.solar_puzzle_continue_btn_rect.center)

        self.assertTrue(q3.solar_array_puzzle_solved, "Sun Temple Fraction Match must be marked solved")
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

    def test_draw_when_objective_completed_and_talking_to_skeleton(self):
        """Test that drawing Quarter3 does not crash across all guardian and fraction-match states"""
        for map_file in ["map7.txt", "map8.txt", "map9.txt"]:
            q3 = Quarter3(self.screen, self.main_menu, map_file)
            # 1. Test drawing when stations 1-5 cleared (guardian waiting)
            q3.quiz_station_index = 6
            q3.guardian_skeleton_state = 1
            q3.draw()

            # 2. Test drawing when talking to guardian (prompt modal open)
            q3.guardian_skeleton_state = 2
            q3.draw()

            # 3. Test drawing during Sun Temple Fraction Match (normal, selected, and solved states)
            q3.guardian_skeleton_state = 3
            q3.solar_array_puzzle_active = True
            q3.init_solar_array_puzzle()
            q3.draw()

            q3.selected_fraction_piece = q3.fraction_match_pieces[0]
            q3.draw()

            q3.auto_solve_solar_array_puzzle()
            q3.draw()

            # 4. Test drawing when objective solved and stage complete (quiz_state = 6)
            q3.solar_array_puzzle_active = False
            q3.fraction_match_active = False
            q3.fraction_bakery_active = False
            q3.solar_array_puzzle_solved = True
            q3.guardian_skeleton_state = 5
            q3.quiz_state = 6
            q3.draw()

    def test_solar_array_puzzle_click_to_place_accessibility(self):
        """Test two-tap accessibility: click card in tray to select, then click matching fraction slot"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.init_solar_array_puzzle()

        piece = q3.solar_array_puzzle_pieces[0]
        matching_slot = next(s for s in q3.solar_array_puzzle_slots if s["id"] == piece["id"])
        wrong_slot = next(s for s in q3.solar_array_puzzle_slots if s["id"] != piece["id"])

        # Step 1: Click card in tray -> selects card
        q3.trigger_click((piece["x"] + 10, piece["y"] + 10))
        self.assertEqual(q3.selected_fraction_piece, piece, "First click on tray card must select it")
        self.assertFalse(piece["is_placed"])

        # Step 2: Clicking a non-matching slot keeps card selected and shows feedback
        q3.trigger_click(wrong_slot["rect"].center)
        self.assertFalse(wrong_slot["matched"])
        self.assertFalse(piece["is_placed"])
        self.assertEqual(q3.fraction_match_feedback_kind, "wrong")

        # Step 3: Clicking matching slot snaps card into place
        q3.trigger_click(matching_slot["rect"].center)
        self.assertTrue(matching_slot["matched"], "Matching slot must fill on second click")
        self.assertTrue(piece["is_placed"], "Card must be marked placed")
        self.assertEqual(piece["target_slot_id"], matching_slot["id"])

    def test_solar_array_puzzle_row_beam_activation(self):
        """Test matching all 4 fraction cards activates completion flags and unlocks portal button"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.init_solar_array_puzzle()

        for slot in q3.solar_array_puzzle_slots:
            piece = next(p for p in q3.solar_array_puzzle_pieces if p["id"] == slot["id"])
            piece["x"] = slot["rect"].centerx - piece["w"] // 2
            piece["y"] = slot["rect"].centery - piece["h"] // 2
            q3.dragged_solar_piece = piece
            q3.release_dragged_solar_piece()

        self.assertTrue(q3.fraction_match_all_placed)
        self.assertTrue(q3.solar_array_puzzle_all_placed)
        self.assertTrue(q3.solar_matrix_row_completed[0], "Completion flag must be activated")
        self.assertGreater(q3.solar_matrix_beam_alphas[0], 0.0, "Beam alpha compatibility flag must be > 0")

    def test_talk_to_skeleton_guardian_accesses_mini_game(self):
        """Test talking to the Skeleton Guardian opens dialogue and launches Sun Temple Fraction Match"""
        q3 = Quarter3(self.screen, self.main_menu, "map7.txt")
        q3.instruction_modal.hide()
        q3.greeting_dialog.hide()

        # 1. Player clicks directly on the Skeleton Guardian sprite
        sx = int((q3.npc_skeleton_x - q3.camera_x) * 1.50) + 16
        sy = int((q3.npc_skeleton_y - q3.camera_y) * 1.50) + 16
        q3.trigger_click((sx, sy))

        self.assertEqual(q3.guardian_skeleton_state, 2, "Clicking Skeleton Guardian must open dialogue modal (state 2)")
        self.assertIsNotNone(q3.guardian_skeleton_btn_rect, "Trial button must exist")

        # 2. Click trial button to begin Sun Temple Fraction Match
        q3.trigger_click(q3.guardian_skeleton_btn_rect.center)
        self.assertEqual(q3.guardian_skeleton_state, 3, "Clicking trial button must enter mini-game (state 3)")
        self.assertTrue(q3.solar_array_puzzle_active, "Sun Temple Fraction Match must be active")

        # 3. Test Escape key closes puzzle and returns to desert
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        q3.handle_event(escape_event)
        self.assertFalse(q3.solar_array_puzzle_active, "Escape must close Sun Temple Fraction Match")

        # 4. Move player close to Skeleton Guardian and press 'E' to talk
        q3.player_x = q3.npc_skeleton_x
        q3.player_y = q3.npc_skeleton_y
        e_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        q3.handle_event(e_event)
        self.assertEqual(q3.guardian_skeleton_state, 2, "Pressing E near Skeleton Guardian must open dialogue")

        # 5. Press Return/Space in dialogue to enter mini-game
        return_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        q3.handle_event(return_event)
        self.assertEqual(q3.guardian_skeleton_state, 3, "Pressing Return in dialogue must enter mini-game")
        self.assertTrue(q3.solar_array_puzzle_active)


if __name__ == "__main__":
    unittest.main()
