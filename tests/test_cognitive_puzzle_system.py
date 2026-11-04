# tests/test_cognitive_puzzle_system.py - Unit & Integration Tests for Decoupled Puzzle Architecture
"""
Unit and Integration Tests for the Data-Driven Cognitive Puzzle Subsystem.

Verifies:
1. Dynamic puzzle instantiation via PuzzleFactory and PuzzleRegistry.
2. Loading from datasets/puzzles/*.json configuration files.
3. State machine lifecycle integration (open/close pushing & popping State.CognitivePuzzle).
4. Strict input isolation (events & clicks consumed, no bleed to player movement).
5. Completion and scoring telemetry.
"""

import os
import sys
import unittest
import pygame

# Set dummy drivers for headless CI / testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.state_machine import State, UIStateMachine
from core.puzzles import (
    BaseCognitivePuzzle,
    JigsawPuzzle,
    CurrencyPuzzle,
    ArrayMatrixPuzzle,
    LockboxPuzzle,
    PuzzleFactory,
    PuzzleRegistry
)


class TestCognitivePuzzleSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.state_machine = UIStateMachine(initial_state=State.Exploration)

    def test_puzzle_registry_and_factory_creation(self):
        """Verify PuzzleRegistry contains registered types and PuzzleFactory creates instances."""
        types = PuzzleRegistry.list_types()
        self.assertIn("jigsaw", types)
        self.assertIn("currency", types)
        self.assertIn("array_matrix", types)
        self.assertIn("lockbox", types)

        jigsaw = PuzzleFactory.create_puzzle("jigsaw", state_machine=self.state_machine)
        self.assertIsInstance(jigsaw, JigsawPuzzle)

        currency = PuzzleFactory.create_puzzle("currency", state_machine=self.state_machine)
        self.assertIsInstance(currency, CurrencyPuzzle)

        array = PuzzleFactory.create_puzzle("array_matrix", state_machine=self.state_machine)
        self.assertIsInstance(array, ArrayMatrixPuzzle)

        lockbox = PuzzleFactory.create_puzzle("lockbox", state_machine=self.state_machine)
        self.assertIsInstance(lockbox, LockboxPuzzle)

    def test_load_all_json_configurations(self):
        """Verify all 4 quarter JSON configuration files load and initialize properly."""
        configs = [
            ("quarter1_jigsaw.json", JigsawPuzzle, 1),
            ("quarter2_currency.json", CurrencyPuzzle, 2),
            ("quarter3_arrays.json", ArrayMatrixPuzzle, 3),
            ("quarter4_locks.json", LockboxPuzzle, 4),
        ]

        for fname, expected_cls, quarter in configs:
            fpath = os.path.join(BASE_DIR, "datasets", "puzzles", fname)
            self.assertTrue(os.path.exists(fpath), f"Missing JSON config: {fpath}")

            puzzle = PuzzleFactory.from_json(fpath, state_machine=self.state_machine)
            self.assertIsInstance(puzzle, expected_cls)
            self.assertEqual(puzzle.quarter, quarter)
            self.assertFalse(puzzle.is_active)
            self.assertFalse(puzzle.is_completed)

    def test_state_machine_pda_lifecycle_integration(self):
        """Verify opening and closing a puzzle strictly pushes/pops State.CognitivePuzzle."""
        fpath = os.path.join(BASE_DIR, "datasets", "puzzles", "quarter1_jigsaw.json")
        puzzle = PuzzleFactory.from_json(fpath, state_machine=self.state_machine)

        # Baseline: State.Exploration
        self.assertEqual(self.state_machine.current_state, State.Exploration)
        self.assertTrue(self.state_machine.allows_movement())
        self.assertTrue(self.state_machine.allows_menus())

        # Open puzzle
        puzzle.open()
        self.assertTrue(puzzle.is_active)
        self.assertEqual(self.state_machine.current_state, State.CognitivePuzzle)
        self.assertFalse(self.state_machine.allows_movement(), "Movement must be locked while puzzle open")
        self.assertFalse(self.state_machine.allows_menus(), "Menus must be locked while puzzle open")
        self.assertTrue(self.state_machine.should_dim_world(), "World must be dimmed while puzzle open")
        self.assertEqual(self.state_machine.stack_depth, 2)

        # Close puzzle
        puzzle.close()
        self.assertFalse(puzzle.is_active)
        self.assertEqual(self.state_machine.current_state, State.Exploration)
        self.assertTrue(self.state_machine.allows_movement())
        self.assertTrue(self.state_machine.allows_menus())
        self.assertEqual(self.state_machine.stack_depth, 1)

    def test_event_isolation_and_input_swallowing(self):
        """Verify active puzzle swallows events and does not allow bleeding."""
        fpath = os.path.join(BASE_DIR, "datasets", "puzzles", "quarter2_currency.json")
        puzzle = PuzzleFactory.from_json(fpath, state_machine=self.state_machine)

        # Inactive puzzle does not consume events
        key_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        self.assertFalse(puzzle.handle_event(key_event))

        # Open puzzle -> Now it consumes all events
        puzzle.open()
        self.assertTrue(puzzle.handle_event(key_event))

        # ESC closes puzzle
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        consumed = puzzle.handle_event(esc_event)
        self.assertTrue(consumed)
        self.assertFalse(puzzle.is_active)
        self.assertEqual(self.state_machine.current_state, State.Exploration)

    def test_jigsaw_puzzle_mechanics(self):
        """Verify jigsaw piece snap detection, completion, and scoring."""
        fpath = os.path.join(BASE_DIR, "datasets", "puzzles", "quarter1_jigsaw.json")
        puzzle = PuzzleFactory.from_json(fpath, state_machine=self.state_machine)
        puzzle.open()

        # Initially unsnapped
        self.assertFalse(puzzle.is_solved())
        self.assertGreater(len(puzzle.pieces), 0)

        # Simulate snapping all pieces
        for p in puzzle.pieces:
            p.current_rect.topleft = p.target_rect.topleft
            p.is_snapped = True

        # Trigger completion verification via simulated release
        release_event = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(0, 0))
        puzzle.dragged_piece = puzzle.pieces[0]
        puzzle.handle_event(release_event)

        self.assertTrue(puzzle.is_solved())
        score = puzzle.get_score()
        self.assertTrue(score["completed"])
        self.assertGreater(score["score"], 0)

    def test_currency_puzzle_mechanics(self):
        """Verify currency sum accumulation in target tray."""
        fpath = os.path.join(BASE_DIR, "datasets", "puzzles", "quarter2_currency.json")
        puzzle = PuzzleFactory.from_json(fpath, state_machine=self.state_machine)
        puzzle.open()

        self.assertFalse(puzzle.is_solved())
        self.assertEqual(puzzle.current_sum, 0)

        # Move bills into target tray to match target_value (175)
        # We need 100 + 50 + 20 + 5 = 175
        items_by_val = {item.value: item for item in puzzle.items}
        for val in [100, 50, 20, 5]:
            if val in items_by_val:
                items_by_val[val].is_in_tray = True

        puzzle._recalculate_sum()
        self.assertEqual(puzzle.current_sum, 175)
        self.assertTrue(puzzle.is_solved())

    def test_array_matrix_puzzle_mechanics(self):
        """Verify cell selection and verification in ArrayMatrixPuzzle."""
        fpath = os.path.join(BASE_DIR, "datasets", "puzzles", "quarter3_arrays.json")
        puzzle = PuzzleFactory.from_json(fpath, state_machine=self.state_machine)
        puzzle.open()

        self.assertFalse(puzzle.is_solved())
        self.assertEqual(puzzle.target_count, 12)

        # Select 12 cells
        for i in range(12):
            puzzle.cells[i].is_selected = True

        # Click submit button
        submit_click = puzzle.submit_btn_rect.center
        consumed = puzzle.handle_click(submit_click)
        self.assertTrue(consumed)
        self.assertTrue(puzzle.is_solved())

    def test_lockbox_puzzle_mechanics(self):
        """Verify deduction and key insertion in LockboxPuzzle."""
        fpath = os.path.join(BASE_DIR, "datasets", "puzzles", "quarter4_locks.json")
        puzzle = PuzzleFactory.from_json(fpath, state_machine=self.state_machine)
        puzzle.open()

        self.assertFalse(puzzle.is_solved())
        self.assertEqual(puzzle.target_solution, 5)

        # Find key with value 5
        key_5 = next(k for k in puzzle.keys if k.value == 5)
        puzzle.handle_click(key_5.rect.center)
        self.assertEqual(puzzle.selected_key, key_5)

        # Click unlock button
        puzzle.handle_click(puzzle.unlock_btn_rect.center)
        self.assertTrue(puzzle.is_solved())
        self.assertTrue(puzzle.get_score()["completed"])


if __name__ == "__main__":
    unittest.main()
