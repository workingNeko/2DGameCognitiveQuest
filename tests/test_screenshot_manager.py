import unittest
import os
import pygame
from unittest.mock import patch, MagicMock

pygame.init()
if pygame.display.get_surface() is None:
    pygame.display.set_mode((640, 480))

from core.screenshot_manager import (
    capture_screenshot,
    get_screenshots_directory,
    copy_surface_to_windows_clipboard
)


class TestScreenshotManager(unittest.TestCase):
    def setUp(self):
        self.surface = pygame.Surface((320, 240))
        self.surface.fill((50, 100, 150))

    def test_get_screenshots_directory(self):
        target_dir = get_screenshots_directory()
        self.assertTrue(os.path.isdir(target_dir))

    def test_capture_screenshot(self):
        filepath, success = capture_screenshot(self.surface)
        self.assertTrue(success)
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith(".png"))
        self.assertGreater(os.path.getsize(filepath), 0)

        # Cleanup test file
        try:
            os.remove(filepath)
        except Exception:
            pass

    def test_copy_surface_to_windows_clipboard(self):
        result = copy_surface_to_windows_clipboard(self.surface)
        if os.name == 'nt':
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
