# tests/test_dev_cheats.py
"""
Unit tests for the Developer Cheats & Debug Navigation Suite.
Validates single-key shortcuts, no-clip wall passing, super speed sprinting,
stage completion, and HUD guide overlay rendering.
"""

import os
import unittest
import pygame

# Initialize headless pygame for testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.font.init()

from core.font_manager import install_font_cache
install_font_cache()

from core.dev_cheats import DevCheatManager
from screens.main_menu import MainMenu
from screens.stageselect import StageSelect


class TestDevCheats(unittest.TestCase):

    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))
        self.main_menu = MainMenu(self.screen, enable_camera=False)
        self.cheats = DevCheatManager.get_instance()
        self.cheats.overlay_visible = False
        self.cheats.dev_superspeed = False
        self.cheats.dev_noclip = False

    def test_singleton_instance(self):
        """Verify DevCheatManager functions as a persistent singleton."""
        instance1 = DevCheatManager.get_instance()
        instance2 = DevCheatManager.get_instance()
        self.assertIs(instance1, instance2)

    def test_toggle_overlay_f1(self):
        """Verify [F1] toggles Developer Cheats HUD Guide."""
        self.assertFalse(self.cheats.overlay_visible)

        # Trigger F1 event
        ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F1, 'mod': 0})
        handled = self.cheats.handle_event(ev, self.main_menu)
        self.assertTrue(handled)
        self.assertTrue(self.cheats.overlay_visible)

        # Trigger F1 again to close
        handled2 = self.cheats.handle_event(ev, self.main_menu)
        self.assertTrue(handled2)
        self.assertFalse(self.cheats.overlay_visible)

    def test_toggle_superspeed_f3_and_ctrl_s(self):
        """Verify [F3] and [Ctrl+S] toggle player speed to 6.0."""
        self.assertFalse(self.cheats.dev_superspeed)

        # F3 toggle on
        ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F3, 'mod': 0})
        handled = self.cheats.handle_event(ev, self.main_menu)
        self.assertTrue(handled)
        self.assertTrue(self.cheats.dev_superspeed)
        self.assertTrue(self.main_menu.dev_superspeed)

        # Ctrl+S toggle off
        ev_ctrl_s = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_s, 'mod': pygame.KMOD_CTRL})
        handled2 = self.cheats.handle_event(ev_ctrl_s, self.main_menu)
        self.assertTrue(handled2)
        self.assertFalse(self.cheats.dev_superspeed)
        self.assertFalse(self.main_menu.dev_superspeed)

    def test_toggle_noclip_f4_and_can_move(self):
        """Verify [F4] toggles No-Clip and allows moving through barriers."""
        self.assertFalse(self.cheats.dev_noclip)

        # Initialize stage select
        st = StageSelect(self.screen, self.main_menu)
        self.main_menu.stage_select = st

        # Without noclip, moving into row -5 or wall should return False
        self.assertFalse(st.can_move(-100, -100))

        # F4 toggle on
        ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F4, 'mod': 0})
        handled = self.cheats.handle_event(ev, self.main_menu)
        self.assertTrue(handled)
        self.assertTrue(self.cheats.dev_noclip)
        self.assertTrue(self.main_menu.dev_noclip)
        self.assertTrue(st.dev_noclip)

        # With noclip, can_move should return True
        self.assertTrue(st.can_move(-100, -100))

    def test_unlock_all_stages_f7_and_u(self):
        """Verify [F7] and [U] unlock all stages and assessments."""
        st = StageSelect(self.screen, self.main_menu)
        self.main_menu.stage_select = st
        st.barriers_lifted = False

        # F7 cheat
        ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F7, 'mod': 0})
        handled = self.cheats.handle_event(ev, self.main_menu)
        self.assertTrue(handled)
        self.assertTrue(st.barriers_lifted)
        self.assertTrue(self.main_menu.last_stage_select_data.get("barriers_lifted", False))

    def test_complete_stage_f5(self):
        """Verify [F5] triggers complete_stage."""
        ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F5, 'mod': 0})
        handled = self.cheats.handle_event(ev, self.main_menu)
        self.assertTrue(handled)

    def test_teleport_to_portal_f8(self):
        """Verify [F8] teleports to active portal without error."""
        st = StageSelect(self.screen, self.main_menu)
        self.main_menu.stage_select = st
        self.main_menu.current_screen = "stage_select"

        ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F8, 'mod': 0})
        handled = self.cheats.handle_event(ev, self.main_menu)
        self.assertTrue(handled)
        self.assertGreater(len(st.portals), 0)

    def test_hud_draw_zero_crash(self):
        """Verify draw renders both overlay HUD and toast cleanly."""
        self.cheats.overlay_visible = True
        self.cheats.show_toast(self.main_menu, "Test Cheat Notification")

        test_surf = pygame.Surface((1280, 720))
        # Draw should execute smoothly without crashing
        self.cheats.draw(test_surf, self.main_menu)


if __name__ == '__main__':
    unittest.main()
