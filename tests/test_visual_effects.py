# tests/test_visual_effects.py
import unittest
import os
import pygame
from PIL import Image
import numpy as np
from collections import deque

from core.visual_effects import (
    DustParticleSystem,
    SparkleParticleSystem,
    ScreenShake,
    SceneTransition,
    get_pulse_value,
    draw_aura_glow,
    draw_beacon_marker
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestVisualEffects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        pygame.display.set_mode((800, 600))

    def setUp(self):
        self.surface = pygame.Surface((800, 600))

    def test_dust_particle_system(self):
        dust = DustParticleSystem(max_particles=50)
        self.assertEqual(len(dust.particles), 0)

        # Emit normal footstep
        dust.emit_footstep(100, 100, speed_boost=False)
        self.assertGreaterEqual(len(dust.particles), 2)

        # Emit sprint boost footstep
        initial_count = len(dust.particles)
        dust.emit_footstep(200, 200, speed_boost=True)
        self.assertGreater(len(dust.particles), initial_count)

        # Test update and drawing
        dust.update(0.05)
        dust.draw(self.surface, camera_offset=(0, 0))

        # Test clear
        dust.clear()
        self.assertEqual(len(dust.particles), 0)

    def test_sparkle_particle_system(self):
        sparkles = SparkleParticleSystem(max_particles=80)
        self.assertEqual(len(sparkles.particles), 0)

        # Spawn ambient aura
        sparkles.spawn_ambient_aura(400, 300, radius=30, count=5)
        self.assertEqual(len(sparkles.particles), 5)

        # Spawn burst
        sparkles.spawn_burst(400, 300, count=10)
        self.assertEqual(len(sparkles.particles), 15)

        # Test update and drawing
        sparkles.update(0.016)
        sparkles.draw(self.surface, camera_offset=(0, 0))

        # Test full life cycle expiration
        sparkles.update(2.0)
        self.assertEqual(len(sparkles.particles), 0)

    def test_screen_shake_trauma(self):
        shake = ScreenShake(max_offset=12.0, max_angle=0.04, decay_rate=2.0)
        self.assertEqual(shake.trauma, 0.0)
        self.assertEqual(shake.get_offset(), (0, 0))

        # Add trauma
        shake.add_trauma(0.5)
        self.assertAlmostEqual(shake.trauma, 0.5, places=3)

        # Update shake
        shake.update(0.016)
        dx, dy = shake.get_offset()
        # Should produce non-zero displacement when trauma > 0
        self.assertTrue(abs(dx) <= 12 and abs(dy) <= 12)

        # Test trauma capping at 1.0
        shake.add_trauma(1.5)
        self.assertEqual(shake.trauma, 1.0)

        # Test decay over time to zero
        shake.update(2.0)
        self.assertEqual(shake.trauma, 0.0)
        self.assertEqual(shake.get_offset(), (0, 0))

    def test_scene_transition_fade(self):
        transition = SceneTransition(screen_size=(800, 600))
        self.assertFalse(transition.is_active())

        # Fade out
        callback_called = []
        transition.start_fade_out(duration=0.2, on_faded=lambda: callback_called.append(True))
        self.assertTrue(transition.is_active())
        self.assertEqual(transition.state, SceneTransition.FADING_OUT)

        # Halfway update
        transition.update(0.1)
        self.assertGreater(transition.alpha, 0)
        self.assertLess(transition.alpha, 255)
        transition.draw(self.surface)

        # Complete fade out
        transition.update(0.15)
        self.assertEqual(transition.state, SceneTransition.FADED_BLACK)
        self.assertEqual(transition.alpha, 255.0)
        self.assertTrue(len(callback_called) == 1)

        # Fade in
        transition.start_fade_in(duration=0.2)
        self.assertEqual(transition.state, SceneTransition.FADING_IN)
        transition.update(0.25)
        self.assertEqual(transition.state, SceneTransition.IDLE)
        self.assertFalse(transition.is_active())

    def test_pulse_and_aura_helpers(self):
        val = get_pulse_value(frequency=2.0, min_val=0.5, max_val=1.0)
        self.assertTrue(0.5 <= val <= 1.0)

        # Test draw aura glow and beacon marker
        draw_aura_glow(self.surface, (100, 100), radius=20, color=(255, 215, 0))
        draw_beacon_marker(self.surface, 150, 150, beacon_type="exclamation")
        draw_beacon_marker(self.surface, 200, 200, beacon_type="question")

    def test_all_player_sprites_have_zero_internal_holes(self):
        """Verifies that all boy, female, and girl sprite assets have zero internal transparency holes."""
        player_dir = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "player")
        sprite_files = [f for f in os.listdir(player_dir) if f.endswith(".png") and "spritesheet" not in f]
        self.assertGreater(len(sprite_files), 10, "Expected player sprites in directory.")

        for fname in sprite_files:
            fpath = os.path.join(player_dir, fname)
            img = Image.open(fpath)
            arr = np.array(img)
            self.assertEqual(arr.shape[2], 4, f"{fname} must be RGBA.")
            alpha = arr[:, :, 3]

            is_transparent = (alpha == 0)
            visited = np.zeros_like(is_transparent, dtype=bool)
            queue = deque()
            h, w = is_transparent.shape
            for x in range(w):
                if is_transparent[0, x]: queue.append((0, x)); visited[0, x] = True
                if is_transparent[h - 1, x]: queue.append((h - 1, x)); visited[h - 1, x] = True
            for y in range(h):
                if is_transparent[y, 0]: queue.append((y, 0)); visited[y, 0] = True
                if is_transparent[y, w - 1]: queue.append((y, w - 1)); visited[y, w - 1] = True

            while queue:
                cy, cx = queue.popleft()
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        if is_transparent[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            queue.append((ny, nx))

            internal_holes = is_transparent & (~visited)
            hole_count = int(np.sum(internal_holes))
            self.assertEqual(hole_count, 0, f"{fname} has {hole_count} internal transparency holes!")


if __name__ == "__main__":
    unittest.main()
