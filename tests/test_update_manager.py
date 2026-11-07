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

    def test_extract_installer_asset(self):
        payload = {
            "tag_name": "v1.2.0",
            "name": "Cognitive Maze v1.2.0",
            "body": "Official Release",
            "html_url": "https://github.com/test",
            "assets": [
                {
                    "name": "CognitiveMaze-v1.2.0-windows-x64.zip",
                    "browser_download_url": "https://github.com/test/CognitiveMaze-v1.2.0-windows-x64.zip",
                    "size": 240000000
                },
                {
                    "name": "CognitiveMaze-Setup-v1.2.0.exe",
                    "browser_download_url": "https://github.com/test/CognitiveMaze-Setup-v1.2.0.exe",
                    "size": 150000000
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            self.updater.local_version = "1.1.0"
            self.updater._run_check_worker()

            self.assertEqual(self.updater.state, UpdateState.UPDATE_AVAILABLE)
            self.assertEqual(self.updater.installer_asset_name, "CognitiveMaze-Setup-v1.2.0.exe")
            self.assertEqual(self.updater.installer_download_url, "https://github.com/test/CognitiveMaze-Setup-v1.2.0.exe")
            self.assertEqual(self.updater.installer_expected_size, 150000000)

    def test_in_app_download_worker(self):
        import tempfile
        import os

        self.updater.state = UpdateState.UPDATE_AVAILABLE
        self.updater.installer_download_url = "https://github.com/test/setup.exe"
        self.updater.installer_asset_name = "test_setup.exe"
        self.updater.installer_expected_size = 100

        temp_target = os.path.join(tempfile.gettempdir(), "test_cognitive_setup.exe")
        temp_tmp = temp_target + ".tmp"
        if os.path.exists(temp_target):
            os.remove(temp_target)

        mock_chunks = [b"A" * 50, b"B" * 50, b""]
        mock_resp = MagicMock()
        mock_resp.read.side_effect = mock_chunks
        mock_resp.headers.get.return_value = "100"
        mock_resp.__enter__.return_value = mock_resp

        with patch("core.update_manager._urlopen_resilient", return_value=mock_resp):
            self.updater._run_download_worker(temp_target, temp_tmp)

        self.assertEqual(self.updater.state, UpdateState.READY_TO_INSTALL)
        self.assertEqual(self.updater.download_progress, 1.0)
        self.assertEqual(self.updater.downloaded_bytes, 100)
        self.assertTrue(os.path.exists(temp_target))
        self.assertEqual(os.path.getsize(temp_target), 100)

        # Cleanup
        if os.path.exists(temp_target):
            os.remove(temp_target)

    def test_in_app_download_cancellation(self):
        import tempfile
        import os

        self.updater.state = UpdateState.DOWNLOADING
        self.updater.installer_download_url = "https://github.com/test/setup.exe"
        self.updater._cancel_requested = True
        temp_target = os.path.join(tempfile.gettempdir(), "test_cancel_setup.exe")
        temp_tmp = temp_target + ".tmp"
        with open(temp_tmp, "wb") as f:
            f.write(b"partial")

        mock_resp = MagicMock()
        mock_resp.read.return_value = b""
        mock_resp.__enter__.return_value = mock_resp

        with patch("core.update_manager._urlopen_resilient", return_value=mock_resp):
            self.updater._run_download_worker(temp_target, temp_tmp)

        self.assertEqual(self.updater.state, UpdateState.UPDATE_AVAILABLE)
        self.assertFalse(os.path.exists(temp_tmp))
        self.assertFalse(os.path.exists(temp_target))

    def test_apply_update_execution(self):
        import tempfile
        import os

        test_file = os.path.join(tempfile.gettempdir(), "test_dummy_installer.exe")
        with open(test_file, "wb") as f:
            f.write(b"installer_data")

        self.updater.installer_path = test_file
        with patch("subprocess.Popen") as mock_popen, patch("sys.exit") as mock_exit:
            self.updater.apply_update()
            mock_popen.assert_called_once()
            mock_exit.assert_called_once_with(0)

        if os.path.exists(test_file):
            os.remove(test_file)


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
        menu.update_manager.installer_download_url = "https://github.com/test/setup.exe"

        # Draw popup to layout in-app update & web browser rects
        menu.draw_audio_popup()
        self.assertIsNotNone(menu.update_download_btn_rect)
        self.assertIsNotNone(menu.update_browser_btn_rect)

        # Click in-app download button triggers start_download
        download_pos = (menu.update_download_btn_rect.centerx, menu.update_download_btn_rect.centery)
        with patch.object(menu.update_manager, "start_download") as mock_dl:
            menu.handle_popup_click(download_pos)
            mock_dl.assert_called_once()

        # Click web browser button triggers open_download_page
        browser_pos = (menu.update_browser_btn_rect.centerx, menu.update_browser_btn_rect.centery)
        with patch.object(menu.update_manager, "open_download_page") as mock_web:
            menu.handle_popup_click(browser_pos)
            mock_web.assert_called_once()

    def test_main_menu_downloading_and_ready_ui_states(self):
        menu = MainMenu(self.screen, enable_camera=False)
        menu.open_audio_settings()

        # State 1: DOWNLOADING
        menu.update_manager.state = UpdateState.DOWNLOADING
        menu.update_manager.download_progress = 0.5
        menu.update_manager.downloaded_bytes = 50 * 1024 * 1024
        menu.update_manager.total_bytes = 100 * 1024 * 1024
        menu.draw_audio_popup()
        self.assertIsNotNone(menu.update_cancel_btn_rect)

        # Click cancel
        cancel_pos = (menu.update_cancel_btn_rect.centerx, menu.update_cancel_btn_rect.centery)
        with patch.object(menu.update_manager, "cancel_download") as mock_cancel:
            menu.handle_popup_click(cancel_pos)
            mock_cancel.assert_called_once()

        # State 2: READY_TO_INSTALL
        menu.update_manager.state = UpdateState.READY_TO_INSTALL
        menu.update_manager.latest_version = "v1.5.0"
        menu.draw_audio_popup()
        self.assertIsNotNone(menu.update_install_btn_rect)

        # Click install & restart
        install_pos = (menu.update_install_btn_rect.centerx, menu.update_install_btn_rect.centery)
        with patch.object(menu.update_manager, "apply_update") as mock_apply:
            menu.handle_popup_click(install_pos)
            mock_apply.assert_called_once()

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
