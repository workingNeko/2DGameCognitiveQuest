# tests/test_quarter4_raft_movement.py
import unittest
import os
import sys
import pygame

# Initialize headless pygame environment
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))

from screens.quarter4 import Quarter4, TILE_SIZE
from core.state_machine import State


class DummyMainMenu:
    def __init__(self):
        self.current_student = {"id": 1, "name": "Tester", "quarter": 4}
        self.active_quarter = 4
        self.camera_controller = None
        self.is_tracking = False


class TestQuarter4RaftMovement(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.Surface((1280, 720))
        self.main_menu = DummyMainMenu()
        self.q4 = Quarter4(self.screen, self.main_menu, map_name="map12.txt")
        # Hide objective modal so testing focuses on raft and post-puzzle states
        self.q4.instruction_modal.hide()
        self.q4.sync_ui_state()

    def test_puzzle_completion_and_dismiss_resets_dialogue_state(self):
        # Simulate puzzle completed
        self.q4.quiz_state = 5
        self.q4.bromen_dialogue_state = 3
        self.q4.sync_ui_state()

        # While bromen_dialogue_state is 3, dialogue should NOT be considered active
        # unless quiz_state is 5 (which is the completion modal)
        self.assertTrue(self.q4.is_dialogue_active())
        self.assertFalse(self.q4.state_machine.allows_movement())

        # Simulate dismissing final speech via trigger_click
        # Setup continue button
        self.q4.addition_continue_btn_rect = pygame.Rect(500, 500, 200, 50)
        self.q4.trigger_click((550, 525))

        # Check state after Bromen speech dismissed
        self.assertEqual(self.q4.quiz_state, 0)
        self.assertEqual(self.q4.raft_state, "ready_to_sail")
        self.assertEqual(self.q4.bromen_dialogue_state, 0)
        self.assertFalse(self.q4.is_dialogue_active())
        self.assertTrue(self.q4.state_machine.allows_movement())
        self.assertEqual(self.q4.state_machine.current_state, State.Exploration)

    def test_raft_voyage_and_post_disembark_movement(self):
        # Bromen dismissed, raft ready to sail
        self.q4.quiz_state = 0
        self.q4.raft_state = "ready_to_sail"
        self.q4.bromen_dialogue_state = 0
        self.q4.sync_ui_state()

        # Player steps onto raft at West Pier (x: 29 -> 30)
        self.q4.player_x = 30.0 * TILE_SIZE
        self.q4.player_y = 9.0 * TILE_SIZE
        self.q4.update()

        self.assertEqual(self.q4.raft_state, "sailing")
        self.assertTrue(self.q4.raft_passenger)

        # Raft reaches East Pier target
        self.q4.raft_x = self.q4.raft_target_x
        self.q4.update()

        self.assertEqual(self.q4.raft_state, "docked_east")
        self.assertFalse(self.q4.raft_passenger)
        self.assertEqual(self.q4.player_x, 37.0 * TILE_SIZE)
        self.assertEqual(self.q4.player_y, 9.0 * TILE_SIZE)
        self.assertEqual(self.q4.quiz_state, 6)
        self.assertEqual(self.q4.bromen_dialogue_state, 0)

        # CRITICAL ASSERTIONS:
        # Dialogue must be inactive and movement MUST be permitted
        self.assertFalse(self.q4.is_dialogue_active(), "Dialogue must be inactive after disembarking raft")
        self.assertTrue(self.q4.state_machine.allows_movement(), "Movement must be allowed after exiting raft")
        self.assertEqual(self.q4.state_machine.current_state, State.Exploration)

        # Test actual player movement rightwards toward the Goal Portal via click-to-move
        initial_x = self.q4.player_x
        self.q4.click_dest = (self.q4.player_x + 50, self.q4.player_y)
        self.q4.update_player_movement()

        self.assertGreater(self.q4.player_x, initial_x, "Player must move right after disembarking raft!")

        # Also test gesture movement
        initial_x2 = self.q4.player_x
        self.q4.hand_detected = True
        self.q4.current_gesture = "OPEN"
        # Position cursor far to the right of player's screen position
        player_screen_x = (self.q4.player_x - self.q4.camera_x) * 1.50
        player_screen_y = (self.q4.player_y - self.q4.camera_y) * 1.50
        self.q4.cursor_pos = (player_screen_x + 100, player_screen_y)
        self.q4.update_player_movement()

        self.assertGreater(self.q4.player_x, initial_x2, "Player must move right with hand gesture steering!")


if __name__ == "__main__":
    unittest.main()
