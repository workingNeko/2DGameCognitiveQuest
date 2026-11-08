# tests/test_quarter3_quarter4_fixes.py
import unittest
import os
import sys
import pygame

# Initialize headless pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))

from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4, TILE_SIZE
from core.state_machine import State


class DummyMainMenu:
    def __init__(self, quarter=3):
        self.current_student = {"id": 1, "name": "Tester", "quarter": quarter}
        self.active_quarter = quarter
        self.camera_controller = None
        self.is_tracking = False
        self.audio_manager = None


class TestQuarter3AndQuarter4Fixes(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.Surface((1280, 720))

    def test_q4_addition_puzzle_gesture_drag_coordinates_update(self):
        """Verify hand gesture fist drag updates addition piece coordinates to follow cursor."""
        menu = DummyMainMenu(quarter=4)
        q4 = Quarter4(self.screen, menu, map_name="map12.txt")
        q4.instruction_modal.hide()
        q4.init_addition_puzzle()
        q4.key_puzzle_active = True
        q4.sync_ui_state()

        self.assertEqual(q4.state_machine.current_state, State.CognitivePuzzle)
        self.assertGreater(len(q4.addition_pieces), 0)

        # Place cursor over the first piece and make a fist
        first_piece = q4.addition_pieces[0]
        q4.cursor_pos = (first_piece["x"] + 10, first_piece["y"] + 10)
        q4.hand_detected = True
        q4.fist_closed = True

        # First frame: picks up the piece
        q4.update_addition_puzzle()
        self.assertIs(q4.dragged_addition_piece, first_piece)

        # Move cursor to a new location
        new_cursor_x = q4.cursor_pos[0] + 150
        new_cursor_y = q4.cursor_pos[1] + 80
        q4.cursor_pos = (new_cursor_x, new_cursor_y)

        # Second frame: position must update to follow cursor
        q4.update_addition_puzzle()
        expected_x = new_cursor_x + q4.drag_offset_x
        expected_y = new_cursor_y + q4.drag_offset_y
        self.assertEqual(first_piece["x"], expected_x)
        self.assertEqual(first_piece["y"], expected_y)

        # Release fist: piece should be dropped
        q4.fist_closed = False
        q4.update_addition_puzzle()
        self.assertIsNone(q4.dragged_addition_piece)

    def test_q4_addition_puzzle_hand_loss_graceful_drop(self):
        """Verify that losing hand detection drops any dragged addition piece without freezing."""
        menu = DummyMainMenu(quarter=4)
        q4 = Quarter4(self.screen, menu, map_name="map12.txt")
        q4.instruction_modal.hide()
        q4.init_addition_puzzle()
        q4.key_puzzle_active = True

        piece = q4.addition_pieces[0]
        q4.cursor_pos = (piece["x"] + 10, piece["y"] + 10)
        q4.hand_detected = True
        q4.fist_closed = True
        q4.update_addition_puzzle()
        self.assertIs(q4.dragged_addition_piece, piece)

        # Hand lost (e.g. out of camera view)
        q4.hand_detected = False
        q4.update_addition_puzzle()
        self.assertIsNone(q4.dragged_addition_piece, "Losing hand tracking must safely drop dragged piece")

    def test_q4_addition_puzzle_click_to_place_and_return(self):
        """Verify clicking an unplaced piece snaps to an empty slot, and clicking a placed piece returns it to tray."""
        menu = DummyMainMenu(quarter=4)
        q4 = Quarter4(self.screen, menu, map_name="map12.txt")
        q4.instruction_modal.hide()
        q4.init_addition_puzzle()
        q4.key_puzzle_active = True
        q4.sync_ui_state()

        piece = q4.addition_pieces[0]
        self.assertFalse(piece["is_placed"])
        orig_home_x, orig_home_y = piece["home_x"], piece["home_y"]

        # Click on the unplaced piece
        q4.trigger_click((piece["x"] + 10, piece["y"] + 10))
        self.assertTrue(piece["is_placed"], "Clicking an unplaced piece must snap it to an empty slot")
        self.assertIsNotNone(piece["slot_id"])
        self.assertNotEqual((piece["x"], piece["y"]), (orig_home_x, orig_home_y))

        # Click on the placed piece
        q4.trigger_click((piece["x"] + 10, piece["y"] + 10))
        self.assertFalse(piece["is_placed"], "Clicking a placed piece must return it to tray")
        self.assertEqual(piece["x"], orig_home_x)
        self.assertEqual(piece["y"], orig_home_y)

    def test_q4_key_puzzle_click_to_place_and_return(self):
        """Verify click-to-place on key lockbox pieces snaps to keyhole slot and returns to deck."""
        menu = DummyMainMenu(quarter=4)
        q4 = Quarter4(self.screen, menu, map_name="map10.txt")
        q4.instruction_modal.hide()
        q4.init_key_puzzle()
        q4.key_puzzle_active = True
        q4.sync_ui_state()

        key = q4.key_puzzle_pieces[0]
        self.assertFalse(key["is_placed"])
        orig_deck_x, orig_deck_y = key["deck_x"], key["deck_y"]

        # Click unplaced key
        q4.trigger_click((key["x"] + 10, key["y"] + 10))
        self.assertTrue(key["is_placed"], "Clicking unplaced key must snap into first empty slot")
        self.assertTrue(key["inserting"])

        # Click placed key
        q4.trigger_click((key["x"] + 10, key["y"] + 10))
        self.assertFalse(key["is_placed"], "Clicking placed key must return it to deck")
        self.assertEqual(key["x"], orig_deck_x)
        self.assertEqual(key["y"], orig_deck_y)

    def test_q4_map12_raft_not_unlocked_until_puzzle_solved_with_bromen(self):
        """Verify that answering all stations does NOT unlock the Lotus Raft if Bromen is present and puzzle not yet solved."""
        menu = DummyMainMenu(quarter=4)
        q4 = Quarter4(self.screen, menu, map_name="map12.txt")
        q4.instruction_modal.hide()
        q4.npc_bromen_found = True
        q4.raft_state = "docked_west"

        # Simulate clearing all stations
        tot_st = q4.active_station_count if q4.active_station_count > 0 else 6
        q4.answered_stations = set(range(1, tot_st + 1))
        q4.key_puzzle_solved = False
        q4.addition_puzzle_solved = False

        q4.update()
        self.assertEqual(q4.raft_state, "docked_west", "Raft must remain docked at West Pier until addition puzzle is solved")

        # Now solve addition puzzle
        q4.addition_puzzle_solved = True
        q4.key_puzzle_solved = True
        q4.update()
        self.assertEqual(q4.raft_state, "ready_to_sail", "Raft must become ready to sail after solving addition puzzle")

    def test_q3_skeleton_guardian_proximity_cooldown_on_cancel(self):
        """Verify that closing or pressing ESC on Skeleton Guardian dialog sets proximity cooldown and prevents instant re-opening."""
        menu = DummyMainMenu(quarter=3)
        q3 = Quarter3(self.screen, menu, map_name="map7.txt")
        q3.instruction_modal.hide()
        q3.quiz_station_index = 6  # All stations cleared
        q3.guardian_skeleton_state = 2  # Dialog open

        # Close via close button click
        q3.guardian_skeleton_close_btn_rect = pygame.Rect(400, 400, 100, 50)
        q3.trigger_click((450, 425))

        self.assertEqual(q3.guardian_skeleton_state, 1)
        self.assertGreater(q3.guardian_skeleton_proximity_cooldown, 0.0, "Dismissing trial modal must activate proximity cooldown")

        # Simulate next frame update while standing near Skeleton Guardian
        q3.player_x = q3.npc_skeleton_x
        q3.player_y = q3.npc_skeleton_y
        q3.update()

        # State must remain 1 (NOT immediately re-opening state 2)
        self.assertEqual(q3.guardian_skeleton_state, 1, "Skeleton Guardian must NOT immediately re-trap player after dismissal")

    def test_q3_clear_portal_overlapping_tiles_updates_game_map(self):
        """Verify clear_portal_overlapping_tiles clears wall obstacles from both render_map AND game_map."""
        menu = DummyMainMenu(quarter=3)
        q3 = Quarter3(self.screen, menu, map_name="map7.txt")
        self.assertGreater(len(q3.portals), 0)
        portal = q3.portals[0]

        # Force a wall tile at portal coordinate
        px, py = portal.x, portal.y
        row_list = list(q3.render_map[py])
        row_list[px] = 'Z'
        q3.render_map[py] = ''.join(row_list)

        game_row_list = list(q3.game_map[py])
        game_row_list[px] = 'Z'
        q3.game_map[py] = ''.join(game_row_list)

        # Clear portal tiles
        q3.clear_portal_overlapping_tiles()

        self.assertEqual(q3.render_map[py][px], 'G')
        self.assertEqual(q3.game_map[py][px], 'G', "game_map must be cleared so player collision allows entering portal")


if __name__ == "__main__":
    unittest.main()

