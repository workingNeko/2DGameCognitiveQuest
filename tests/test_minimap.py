# tests/test_minimap.py
import os
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from core.minimap import MiniMap


class TestMiniMap(unittest.TestCase):
    def setUp(self):
        self.sample_map = [
            "GGGGGGGGGG",
            "G########G",
            "G#1####2#G",
            "G########G",
            "GGGGGGGGGG",
        ]
        self.walkable = {"#", "1", "2"}

    def test_minimap_initialization(self):
        mm = MiniMap(self.sample_map, self.walkable, tile_size=32)
        self.assertEqual(mm.map_rows, 5)
        self.assertEqual(mm.map_cols, 10)
        self.assertTrue(mm.visible)
        self.assertIsNotNone(mm._base_map_surf)
        self.assertIsNotNone(mm._frame_surf)
        self.assertIsNotNone(mm._pill_surf)

    def test_minimap_toggle(self):
        mm = MiniMap(self.sample_map, self.walkable)
        self.assertTrue(mm.visible)
        mm.toggle()
        self.assertFalse(mm.visible)
        mm.toggle()
        self.assertTrue(mm.visible)

    def test_minimap_keyboard_and_click_event(self):
        mm = MiniMap(self.sample_map, self.walkable)
        
        # Test K_m keydown
        key_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        handled = mm.handle_event(key_event)
        self.assertTrue(handled)
        self.assertFalse(mm.visible)

        # Test click on pill when minimized
        click_pill = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=mm.pill_rect.center)
        handled_click = mm.handle_event(click_pill)
        self.assertTrue(handled_click)
        self.assertTrue(mm.visible)

    def test_world_to_map_bounds(self):
        mm = MiniMap(self.sample_map, self.walkable, tile_size=32)
        # Point (0, 0)
        mx, my = mm.world_to_map(0, 0)
        self.assertGreaterEqual(mx, mm.container_x)
        self.assertGreaterEqual(my, mm.container_y)

        # Far point (10 * 32, 5 * 32)
        mx_far, my_far = mm.world_to_map(320, 160)
        self.assertLessEqual(mx_far, mm.container_x + mm.width)
        self.assertLessEqual(my_far, mm.container_y + mm.height)

    def test_minimap_draw_pipeline(self):
        mm = MiniMap(self.sample_map, self.walkable, tile_size=32)
        markers = [
            {"x": 64, "y": 64, "type": "station", "status": "active"},
            {"x": 128, "y": 64, "type": "station", "status": "completed"},
            {"x": 200, "y": 64, "type": "portal", "status": "unlocked"},
            {"x": 250, "y": 64, "type": "goal"},
        ]
        # Expanded draw
        mm.draw(
            screen,
            player_pos=(80, 80),
            camera_pos=(50, 50),
            zoom=1.5,
            markers=markers,
            cursor_pos=(100, 100),
            hold_pct=0.2,
        )

        # Minimized draw
        mm.toggle()
        mm.draw(
            screen,
            player_pos=(80, 80),
            camera_pos=(50, 50),
            zoom=1.5,
            markers=markers,
            cursor_pos=mm.pill_rect.center,
            hold_pct=0.5,
        )


if __name__ == "__main__":
    unittest.main()
