"""Tests for UI State Machine and Pushdown Automata (PDA) in Cognitive Quest.
Verifies input isolation, PDA state transitions, and universal pause menu access across all quarters.
"""

import unittest
import pygame
from core.state_machine import State, UIStateMachine, BaseState, ExplorationState, PuzzleState, DialogueState
from core.pause_menu import InGamePauseMenu
from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4


class MockMainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.current_screen = "menu"
        self.audio_manager = None
        self.selected_student = {"id": "1", "name": "Test Student"}
        self.stage_select_data = {}


class TestUIStateMachinePDA(unittest.TestCase):
    """Unit tests for UIStateMachine PDA lifecycle and state queries."""

    def setUp(self):
        self.sm = UIStateMachine(initial_state=State.Exploration)

    def test_initial_state_is_exploration(self):
        self.assertEqual(self.sm.current_state, State.Exploration)
        self.assertEqual(self.sm.stack_depth, 1)
        self.assertTrue(self.sm.allows_movement())
        self.assertTrue(self.sm.allows_menus())
        self.assertTrue(self.sm.allows_camera_pan())
        self.assertFalse(self.sm.is_world_paused())
        self.assertFalse(self.sm.should_dim_world())

    def test_push_and_pop_pda(self):
        # Push CognitivePuzzle
        pushed = self.sm.push(State.CognitivePuzzle)
        self.assertEqual(self.sm.current_state, State.CognitivePuzzle)
        self.assertEqual(self.sm.stack_depth, 2)
        self.assertFalse(self.sm.allows_movement())
        self.assertFalse(self.sm.allows_camera_pan())
        self.assertTrue(self.sm.is_world_paused())
        self.assertTrue(self.sm.should_dim_world())

        # Push Dialogue on top
        self.sm.push(State.Dialogue)
        self.assertEqual(self.sm.current_state, State.Dialogue)
        self.assertEqual(self.sm.stack_depth, 3)
        self.assertFalse(self.sm.allows_movement())
        self.assertFalse(self.sm.allows_camera_pan())
        self.assertFalse(self.sm.is_world_paused())

        # Pop Dialogue -> returns to CognitivePuzzle
        popped = self.sm.pop()
        self.assertEqual(popped.name, State.Dialogue)
        self.assertEqual(self.sm.current_state, State.CognitivePuzzle)
        self.assertEqual(self.sm.stack_depth, 2)
        self.assertTrue(self.sm.is_world_paused())

        # Pop CognitivePuzzle -> returns to Exploration
        popped2 = self.sm.pop()
        self.assertEqual(popped2.name, State.CognitivePuzzle)
        self.assertEqual(self.sm.current_state, State.Exploration)
        self.assertEqual(self.sm.stack_depth, 1)
        self.assertTrue(self.sm.allows_movement())

    def test_base_exploration_state_cannot_be_popped(self):
        # Popping empty/base stack retains Exploration and returns current state
        popped = self.sm.pop()
        self.assertEqual(popped, State.Exploration)
        self.assertEqual(self.sm.current_state, State.Exploration)
        self.assertEqual(self.sm.stack_depth, 1)

    def test_set_state(self):
        self.sm.set_state(State.Dialogue)
        self.assertEqual(self.sm.current_state, State.Dialogue)
        self.assertEqual(self.sm.stack_depth, 2)
        self.assertFalse(self.sm.allows_movement())

        self.sm.set_state(State.Exploration)
        self.assertEqual(self.sm.current_state, State.Exploration)
        self.assertEqual(self.sm.stack_depth, 1)
        self.assertTrue(self.sm.allows_movement())


class TestQuarter1InputBleedingFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.mm = MockMainMenu(self.screen)
        self.q1 = Quarter1(self.screen, self.mm, "map1.txt")
        self.q1.instruction_modal.hide()

    def test_exploration_allows_movement_and_pause_menu(self):
        self.assertEqual(self.q1.state_machine.current_state, State.Exploration)
        self.assertTrue(self.q1.state_machine.allows_movement())
        self.assertTrue(self.q1.state_machine.allows_menus())

    def test_cognitive_puzzle_locks_movement_while_pause_menu_remains_universal(self):
        """When jigsaw puzzle is active, player cannot walk, click-to-move is cleared, and pause menu works universally."""
        # Activate jigsaw puzzle
        self.q1.puzzle_active = True
        self.q1.sync_ui_state()

        self.assertEqual(self.q1.state_machine.current_state, State.CognitivePuzzle)
        self.assertFalse(self.q1.state_machine.allows_movement())

        # Set a lingering click destination
        self.q1.click_dest = (500, 400)
        orig_x, orig_y = self.q1.player_x, self.q1.player_y

        # Update movement -> Should reset click_dest to None and not change player position
        self.q1.update_player_movement()
        self.assertIsNone(self.q1.click_dest)
        self.assertEqual(self.q1.player_x, orig_x)
        self.assertEqual(self.q1.player_y, orig_y)

        # Pause menu must work all the time, including during Cognitive Puzzle
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        res = self.q1.handle_event(esc_event)
        self.assertTrue(self.q1.pause_menu.is_paused, "Pause menu must open during Cognitive Puzzle")

        # Resume game
        self.q1.pause_menu.close()
        self.assertFalse(self.q1.pause_menu.is_paused)

        # Dismiss puzzle
        self.q1.puzzle_active = False
        self.q1.sync_ui_state()
        self.assertEqual(self.q1.state_machine.current_state, State.Exploration)
        self.assertTrue(self.q1.state_machine.allows_movement())


class TestQuarter2InputBleedingFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.mm = MockMainMenu(self.screen)
        self.q2 = Quarter2(self.screen, self.mm, "map4.txt")
        self.q2.instruction_modal.hide()

    def test_currency_puzzle_locks_movement_while_pause_menu_remains_universal(self):
        """When Philippine currency puzzle is active, movement is locked but pause menu works universally."""
        self.q2.currency_puzzle_active = True
        self.q2.sync_ui_state()

        self.assertEqual(self.q2.state_machine.current_state, State.CognitivePuzzle)
        self.assertFalse(self.q2.state_machine.allows_movement())

        # Set click destination
        self.q2.click_dest = (300, 300)
        orig_x = self.q2.player_x
        self.q2.update_player_movement()
        self.assertIsNone(self.q2.click_dest)
        self.assertEqual(self.q2.player_x, orig_x)

        # Verify pause menu can be opened at all times
        self.assertTrue(self.q2.pause_menu.open())
        self.assertTrue(self.q2.pause_menu.is_paused)

    def test_finishing_all_questions_keeps_movement_enabled_for_exploration(self):
        """When all 5 questions are answered, guardian_knight_state becomes 1 (awaiting challenge at portal) and movement must remain enabled."""
        self.q2.currency_puzzle_active = False
        self.q2.quiz_station_index = 6
        self.q2.current_question_index = 5
        self.q2.quiz_state = 0
        self.q2.guardian_knight_state = 1  # Awaiting challenge at exit portal

        self.q2.sync_ui_state()

        self.assertEqual(self.q2.state_machine.current_state, State.Exploration)
        self.assertTrue(self.q2.state_machine.allows_movement(), "Player must be free to walk to the Knight Guardian after questions")

        # Also verify state 5 (portal unlocked after currency puzzle) allows movement
        self.q2.guardian_knight_state = 5
        self.q2.quiz_state = 6
        self.q2.sync_ui_state()
        self.assertEqual(self.q2.state_machine.current_state, State.Exploration)
        self.assertTrue(self.q2.state_machine.allows_movement(), "Player must be free to walk through unlocked portal")


class TestQuarter3InputBleedingFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.mm = MockMainMenu(self.screen)
        self.q3 = Quarter3(self.screen, self.mm, "map7.txt")
        self.q3.instruction_modal.hide()

    def test_solar_array_and_mini_puzzle_lock_movement_and_camera(self):
        """When Fraction Bakery / Solar Array / Mini-Puzzle is active, movement and camera pan are locked."""
        # 1. Mini-Puzzle active
        self.q3.mini_puzzle_active = True
        self.q3.sync_ui_state()
        self.assertEqual(self.q3.state_machine.current_state, State.CognitivePuzzle)
        self.assertFalse(self.q3.state_machine.allows_movement())
        self.assertFalse(self.q3.state_machine.allows_camera_pan())

        self.q3.click_dest = (450, 450)
        self.q3.update_player_movement()
        self.assertIsNone(self.q3.click_dest)

        self.q3.mini_puzzle_active = False

        # 2. Solar Array / Fraction Bakery active
        self.q3.solar_array_puzzle_active = True
        self.q3.sync_ui_state()
        self.assertEqual(self.q3.state_machine.current_state, State.CognitivePuzzle)
        self.assertFalse(self.q3.state_machine.allows_movement())
        self.assertFalse(self.q3.state_machine.allows_camera_pan())


class TestQuarter4InputBleedingFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.mm = MockMainMenu(self.screen)
        self.q4 = Quarter4(self.screen, self.mm, "map10.txt")
        self.q4.instruction_modal.hide()

    def test_key_puzzle_locks_movement_while_pause_menu_works(self):
        """When Key Lock Box Puzzle is active, movement and camera pan are blocked, but pause menu works all the time."""
        self.q4.key_puzzle_active = True
        self.q4.sync_ui_state()

        self.assertEqual(self.q4.state_machine.current_state, State.CognitivePuzzle)
        self.assertFalse(self.q4.state_machine.allows_movement())
        self.assertFalse(self.q4.state_machine.allows_camera_pan())

        self.q4.click_dest = (200, 200)
        self.q4.update_player_movement()
        self.assertIsNone(self.q4.click_dest)

        # Verify pause menu works all the time
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.q4.handle_event(esc_event)
        self.assertTrue(self.q4.pause_menu.is_paused, "Pause menu must open on ESC during Key Puzzle")


if __name__ == "__main__":
    unittest.main()
