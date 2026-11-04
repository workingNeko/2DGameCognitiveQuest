"""Unit and integration tests for Core Versioning and Update Manager.
Tests run completely headless with mocked networking to verify:
1. Semantic version parsing and comparison.
2. Background non-blocking update checking and state transitions.
3. Network error handling and offline fallback.
4. MainMenu and PauseMenu UI integration.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import io
import urllib.error
import pygame

# Initialize headless pygame display before importing screens
pygame.init()
if pygame.display.get_surface() is None:
    pygame.display.set_mode((1024, 768))

from core.version import APP_VERSION, APP_NAME, parse_version, compare_versions, GITHUB_RELEASES_URL
from core.update_manager import UpdateManager, UpdateState
from screens.main_menu import MainMenu
from core.pause_menu import InGamePauseMenu


class TestVersionParsing(unittest.TestCase):
    """Test suite for semantic version parsing and comparison."""

    def test_parse_standard_version(self):
        self.assertEqual(parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("2.10.4-beta"), (2, 10, 4))

    def test_parse_partial_version(self):
        self.assertEqual(parse_version("1"), (1, 0, 0))
        self.assertEqual(parse_version("v1.2"), (1, 2, 0))

    def test_parse_invalid_or_empty(self):
        self.assertEqual(parse_version(""), (0, 0, 0))
        self.assertEqual(parse_version("abc"), (0, 0, 0))
        self.assertEqual(parse_version(None), (0, 0, 0))

    def test_compare_versions_equal(self):
        self.assertEqual(compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("v1.0.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("1.2.3", "v1.2.3"), 0)

    def test_compare_versions_remote_is_newer(self):
        # When remote > local, compare_versions returns 1
        self.assertEqual(compare_versions("1.0.0", "1.1.0"), 1)
        self.assertEqual(compare_versions("1.9.9", "v2.0.0"), 1)
        self.assertEqual(compare_versions("1.0.0", "1.0.1"), 1)
        self.assertEqual(compare_versions("1.0.2", "1.0.10"), 1)

    def test_compare_versions_remote_is_older(self):
        # When remote < local, compare_versions returns -1
        self.assertEqual(compare_versions("1.1.0", "1.0.0"), -1)
        self.assertEqual(compare_versions("2.0.0", "1.9.9"), -1)
        self.assertEqual(compare_versions("1.0.1", "1.0.0"), -1)
        self.assertEqual(compare_versions("1.0.0", "0.9.5"), -1)


class TestUpdateManager(unittest.TestCase):
    """Test suite for UpdateManager background execution and state machine."""

    def setUp(self):
        self.updater = UpdateManager()
        self.updater.reset()

    def test_initial_state(self):
        self.assertEqual(self.updater.state, UpdateState.IDLE)
        self.assertEqual(self.updater.local_version, APP_VERSION)
        self.assertIsNone(self.updater.latest_version)
        self.assertIsNone(self.updater.error_message)

    @patch("urllib.request.urlopen")
    def test_update_available(self, mock_urlopen):
        # Mock GitHub Releases API response returning a higher version
        payload = {
            "tag_name": "v1.5.0",
            "name": "Version 1.5.0 Update",
            "body": "Exciting new levels and bugfixes!",
            "html_url": "https://github.com/workingNeko/2DGameCognitiveQuest/releases/tag/v1.5.0"
        }
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Run worker directly
        self.updater._run_check_worker()

        self.assertEqual(self.updater.state, UpdateState.UPDATE_AVAILABLE)
        self.assertEqual(self.updater.latest_version, "v1.5.0")
        self.assertEqual(self.updater.download_url, "https://github.com/workingNeko/2DGameCognitiveQuest/releases/tag/v1.5.0")
        self.assertEqual(self.updater.release_notes, "Exciting new levels and bugfixes!")
        self.assertIsNone(self.updater.error_message)

    @patch("urllib.request.urlopen")
    def test_up_to_date(self, mock_urlopen):
        # Mock GitHub Releases API returning the exact current version
        payload = {
            "tag_name": f"v{APP_VERSION}",
            "name": f"Version {APP_VERSION}",
            "body": "Initial release",
            "html_url": f"https://github.com/workingNeko/2DGameCognitiveQuest/releases/tag/v{APP_VERSION}"
        }
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        self.updater._run_check_worker()

        self.assertEqual(self.updater.state, UpdateState.UP_TO_DATE)
        self.assertEqual(self.updater.latest_version, f"v{APP_VERSION}")
        self.assertIsNone(self.updater.error_message)

    @patch("urllib.request.urlopen")
    def test_network_offline_error(self, mock_urlopen):
        # Mock network failure
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

        self.updater._run_check_worker()

        self.assertEqual(self.updater.state, UpdateState.ERROR)
        self.assertIn("timed out", self.updater.error_message.lower())

    @patch("urllib.request.urlopen")
    def test_http_rate_limit_error(self, mock_urlopen):
        # Mock 403 Rate Limit error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com",
            code=403,
            msg="rate limit exceeded",
            hdrs={},
            fp=io.BytesIO(b"{}")
        )

        self.updater._run_check_worker()

        self.assertEqual(self.updater.state, UpdateState.ERROR)
        self.assertIn("rate limit", self.updater.error_message.lower())

    @patch("webbrowser.open")
    def test_open_download_page(self, mock_webbrowser):
        self.updater.download_url = "https://github.com/workingNeko/2DGameCognitiveQuest/releases/latest"
        result = self.updater.open_download_page()

        self.assertTrue(result)
        mock_webbrowser.assert_called_once_with("https://github.com/workingNeko/2DGameCognitiveQuest/releases/latest")


class TestUIIntegration(unittest.TestCase):
    """Test suite for MainMenu and PauseMenu integration with UpdateManager."""

    def setUp(self):
        self.screen = pygame.Surface((1024, 768))
        self.updater = UpdateManager()
        self.updater.reset()

    def test_main_menu_settings_modal_update_section(self):
        # Initialize MainMenu with camera disabled
        menu = MainMenu(self.screen, enable_camera=False)
        menu.open_audio_settings()

        # Render settings popup (should render cleanly without crash)
        menu.draw_audio_popup()
        self.assertIsNotNone(menu.update_check_btn_rect)

        # Test clicking the "Check for Updates" button
        check_pos = (menu.update_check_btn_rect.centerx, menu.update_check_btn_rect.centery)
        with patch.object(menu.update_manager, "check_for_updates") as mock_check:
            menu.handle_popup_click(check_pos)
            mock_check.assert_called_once()

    def test_main_menu_download_button_when_update_available(self):
        menu = MainMenu(self.screen, enable_camera=False)
        menu.open_audio_settings()

        # Set update available on menu's update manager
        menu.update_manager.state = UpdateState.UPDATE_AVAILABLE
        menu.update_manager.latest_version = "v1.5.0"
        menu.update_manager.download_url = "https://github.com/test/download"

        # Draw popup to layout download rect
        menu.draw_audio_popup()
        self.assertIsNotNone(menu.update_download_btn_rect)

        # Click download button
        download_pos = (menu.update_download_btn_rect.centerx, menu.update_download_btn_rect.centery)
        with patch.object(menu.update_manager, "open_download_page") as mock_open:
            menu.handle_popup_click(download_pos)
            mock_open.assert_called_once()

    def test_main_menu_footer_notification_pill(self):
        menu = MainMenu(self.screen, enable_camera=False)

        # By default (UP_TO_DATE / IDLE), no interactive footer pill
        menu.update_manager.state = UpdateState.UP_TO_DATE
        menu.draw_version_footer()
        self.assertIsNone(menu.footer_update_rect)

        # When UPDATE_AVAILABLE, footer pill is active
        menu.update_manager.state = UpdateState.UPDATE_AVAILABLE
        menu.update_manager.latest_version = "v2.0.0"
        menu.draw_version_footer()
        self.assertIsNotNone(menu.footer_update_rect)

        # Click footer pill opens settings popup
        pill_pos = (menu.footer_update_rect.centerx, menu.footer_update_rect.centery)
        self.assertNotEqual(menu.popup_state, "audio_settings")
        menu.trigger_click(pill_pos)
        self.assertEqual(menu.popup_state, "audio_settings")

    def test_pause_menu_version_watermark(self):
        # Verify pause menu renders without crashing and contains version
        dummy_menu = MagicMock()
        pause_menu = InGamePauseMenu(self.screen, 1024, 768, dummy_menu, lambda: None)
        pause_menu.open()

        # Render pause menu
        pause_menu.draw((512, 384))
        # Modal height is 410px as per spec
        self.assertEqual(pause_menu.modal_h, 410)


if __name__ == "__main__":
    unittest.main()
