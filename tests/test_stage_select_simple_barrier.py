import os
import sys
from unittest.mock import MagicMock, patch
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()


class TestStageSelectSimpleBarrier(unittest.TestCase):
    def setUp(self):
        self.surface = pygame.display.set_mode((1280, 720))
        self.mock_menu = MagicMock()
        self.mock_menu.screen = self.surface
        self.mock_menu.student_id = "test_student"
        self.mock_menu.selected_student = {"first_name": "Hero"}
        self.mock_menu.audio_manager = MagicMock()

    def test_draw_corridor_barriers_simple_and_cached(self):
        """Verify draw_corridor_barriers creates simple static cached barrier surfaces without animation loops."""
        from screens.stageselect import StageSelect

        with patch("db.save_system.get_completed_quarters", return_value={}):
            ss = StageSelect(self.surface, self.mock_menu)
            ss.barriers_lifted = False

            # Initial cache should be empty
            self.assertEqual(len(ss._barrier_cache), 0)

            # Move camera so corridor barriers are in viewport
            ss.camera_x = 25 * 32
            ss.camera_y = 14 * 32

            # First draw call
            ss.draw_corridor_barriers()

            # Surfaces should be created and cached for horizontal and vertical barriers
            self.assertGreater(len(ss._barrier_cache), 0)
            for cache_key, surf in ss._barrier_cache.items():
                bw, bh, axis = cache_key
                self.assertIsInstance(surf, pygame.Surface)
                self.assertEqual(surf.get_size(), (bw, bh))
                self.assertIn(axis, ("horizontal", "vertical"))

            initial_cached_instances = dict(ss._barrier_cache)

            # Second draw call (should reuse cached surfaces exactly with zero re-creation)
            ss.draw_corridor_barriers()
            self.assertEqual(ss._barrier_cache, initial_cached_instances)

    def test_barriers_lifted_draws_nothing(self):
        """When barriers are lifted or quarters unlocked, no barriers should be drawn."""
        from screens.stageselect import StageSelect

        completed_data = {
            "quarter1": {"completed": True},
            "quarter2": {"completed": True},
            "quarter3": {"completed": True},
            "quarter4": {"completed": True}
        }
        with patch("db.save_system.get_completed_quarters", return_value=completed_data):
            ss = StageSelect(self.surface, self.mock_menu)
            ss.barriers_lifted = True

            # Clear cache
            ss._barrier_cache.clear()

            # Draw
            ss.draw_corridor_barriers()

            # Nothing should be cached or drawn because all corridors are open
            self.assertEqual(len(ss._barrier_cache), 0)


if __name__ == "__main__":
    unittest.main()
