"""
tests/test_autostart.py - Comprehensive Unit Tests for Windows Boot Autorun Feature
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.autostart_manager import (
    is_windows,
    is_autostart_supported,
    get_application_directory,
    get_executable_command,
    is_autostart_enabled,
    enable_autostart,
    disable_autostart,
    toggle_autostart,
    get_status_text,
)


class TestAutostartManager(unittest.TestCase):
    """Test core/autostart_manager functionality and Windows Registry integration."""

    TEST_KEY = "CognitivePlay_UnitTest_Key"

    def tearDown(self):
        """Always clean up test registry key if created."""
        if is_autostart_supported():
            disable_autostart(self.TEST_KEY)

    def test_environment_detection(self):
        """Verify Windows platform detection and registry support check."""
        self.assertTrue(is_windows(), "Expected Windows platform for these tests")
        self.assertTrue(is_autostart_supported(), "winreg should be supported on Windows")

    def test_application_directory(self):
        """Verify root directory resolution matches project workspace."""
        app_dir = get_application_directory()
        self.assertTrue(os.path.exists(app_dir))
        self.assertTrue(os.path.exists(os.path.join(app_dir, "main.py")))

    def test_executable_command_dev_mode(self):
        """Verify executable command in development mode produces valid string."""
        cmd = get_executable_command()
        self.assertIsInstance(cmd, str)
        self.assertGreater(len(cmd), 0)
        # Should contain either run_game.bat, pythonw.exe, python.exe, or .exe
        self.assertTrue(
            "run_game.bat" in cmd or "python" in cmd.lower() or ".exe" in cmd.lower(),
            f"Unexpected launch command: {cmd}"
        )

    def test_executable_command_frozen_mode(self):
        """Verify executable command when running as compiled standalone .exe (sys.frozen)."""
        mock_exe = r"C:\Games\CognitivePlay\CognitivePlay.exe"
        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", mock_exe):
            cmd = get_executable_command()
            self.assertEqual(cmd, f'"{mock_exe}"')

    def test_registry_lifecycle(self):
        """Test enabling, querying, toggling, and disabling an autostart registry entry."""
        if not is_autostart_supported():
            self.skipTest("Autostart is not supported on this platform")

        # 1. Ensure initially disabled
        disable_autostart(self.TEST_KEY)
        self.assertFalse(is_autostart_enabled(self.TEST_KEY))
        self.assertIn("Disabled", get_status_text(self.TEST_KEY))

        # 2. Enable autostart with a dummy test command
        dummy_cmd = r'"C:\Games\CognitivePlay\CognitivePlay.exe"'
        success, msg = enable_autostart(self.TEST_KEY, custom_command=dummy_cmd)
        self.assertTrue(success, f"Failed to enable: {msg}")
        self.assertTrue(is_autostart_enabled(self.TEST_KEY))
        self.assertIn("Enabled", get_status_text(self.TEST_KEY))

        # 3. Toggle off
        new_state, msg = toggle_autostart(self.TEST_KEY)
        self.assertFalse(new_state)
        self.assertFalse(is_autostart_enabled(self.TEST_KEY))

        # 4. Toggle on
        new_state, msg = toggle_autostart(self.TEST_KEY)
        self.assertTrue(new_state)
        self.assertTrue(is_autostart_enabled(self.TEST_KEY))

        # 5. Disable and verify cleanup
        success, msg = disable_autostart(self.TEST_KEY)
        self.assertTrue(success)
        self.assertFalse(is_autostart_enabled(self.TEST_KEY))


class TestMainMenuSettingsIntegration(unittest.TestCase):
    """Test Main Menu settings modal integration for the autostart toggle."""

    @classmethod
    def setUpClass(cls):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        import pygame
        pygame.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def test_settings_modal_toggle_click(self):
        """Test clicking inside the settings modal autostart toggle trigger."""
        from screens.main_menu import MainMenu
        mm = MainMenu(self.screen)
        mm.open_audio_settings()
        self.assertEqual(mm.popup_state, "audio_settings")

        # Calculate exact toggle position
        box_w, box_h = 600, 440
        box_x = (mm.w - box_w) // 2
        box_y = (mm.h - box_h) // 2
        toggle_x = box_x + box_w - 180 + 20
        toggle_y = box_y + 248 + 15

        with patch("core.autostart_manager.toggle_autostart", return_value=(True, "Toggled!")) as mock_toggle:
            mm.handle_popup_click((toggle_x, toggle_y))
            mock_toggle.assert_called_once()
            self.assertEqual(mm.autostart_status_msg, "Toggled!")


if __name__ == "__main__":
    unittest.main()
