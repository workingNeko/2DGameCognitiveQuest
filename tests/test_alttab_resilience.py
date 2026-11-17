# tests/test_alttab_resilience.py
"""
Unit tests for Alt+Tab window focus transitions, surface context preservation,
input state clearing, and drawing exception absorption.
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

from screens.main_menu import MainMenu
from screens.stageselect import StageSelect


class TestAltTabResilience(unittest.TestCase):

    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))
        self.main_menu = MainMenu(self.screen, enable_camera=False)

    def test_clear_input_states_resets_all_flags(self):
        """Verify clear_input_states thoroughly resets held gestures, clicks, and paths."""
        self.main_menu.fist_start_time = 12345.6
        self.main_menu.peace_start_time = 78910.1
        self.main_menu.mouse_active = True
        self.main_menu.current_gesture = "FIST"

        # Initialize stage_select
        self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
        self.main_menu.stage_select.click_dest = (500, 300)
        self.main_menu.stage_select.path = [(500, 300), (520, 320)]
        self.main_menu.stage_select.fist_start_time = 999.0
        self.main_menu.stage_select.peace_start_time = 888.0
        self.main_menu.stage_select.moving = True
        if hasattr(self.main_menu.stage_select, 'lol_camera') and self.main_menu.stage_select.lol_camera:
            self.main_menu.stage_select.lol_camera.is_middle_dragging = True

        # Call clear_input_states
        self.main_menu.clear_input_states()

        self.assertEqual(self.main_menu.fist_start_time, 0)
        self.assertEqual(self.main_menu.peace_start_time, 0)
        self.assertFalse(self.main_menu.mouse_active)
        self.assertEqual(self.main_menu.current_gesture, "NO HAND")

        self.assertIsNone(self.main_menu.stage_select.click_dest)
        self.assertEqual(self.main_menu.stage_select.path, [])
        self.assertEqual(self.main_menu.stage_select.fist_start_time, 0)
        self.assertEqual(self.main_menu.stage_select.peace_start_time, 0)
        self.assertFalse(self.main_menu.stage_select.moving)
        if hasattr(self.main_menu.stage_select, 'lol_camera') and self.main_menu.stage_select.lol_camera:
            self.assertFalse(self.main_menu.stage_select.lol_camera.is_middle_dragging)

    def test_activeevent_and_window_focus_events(self):
        """Verify MainMenu handles window focus lost/gained events without crashing."""
        self.main_menu.fist_start_time = 500.0

        # Simulate WINDOWFOCUSLOST
        if hasattr(pygame, 'WINDOWFOCUSLOST'):
            focus_lost_ev = pygame.event.Event(pygame.WINDOWFOCUSLOST)
            self.main_menu.handle_event(focus_lost_ev)
            self.assertEqual(self.main_menu.fist_start_time, 0)

        # Simulate WINDOWMINIMIZED
        self.main_menu.fist_start_time = 700.0
        if hasattr(pygame, 'WINDOWMINIMIZED'):
            min_ev = pygame.event.Event(pygame.WINDOWMINIMIZED)
            self.main_menu.handle_event(min_ev)
            self.assertEqual(self.main_menu.fist_start_time, 0)

        # Simulate ACTIVEEVENT (focus lost: state=2, gain=0)
        self.main_menu.fist_start_time = 800.0
        active_lost_ev = pygame.event.Event(pygame.ACTIVEEVENT, {'state': 2, 'gain': 0})
        self.main_menu.handle_event(active_lost_ev)
        self.assertEqual(self.main_menu.fist_start_time, 0)

        # Simulate ACTIVEEVENT (focus gained: state=2, gain=1)
        active_gained_ev = pygame.event.Event(pygame.ACTIVEEVENT, {'state': 2, 'gain': 1})
        self.main_menu.handle_event(active_gained_ev)

    def test_set_screen_updates_references(self):
        """Verify set_screen re-points all screen references to the new surface."""
        new_surface = pygame.Surface((1920, 1080))
        self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
        self.main_menu.set_screen(new_surface)

        self.assertIs(self.main_menu.screen, new_surface)
        self.assertEqual(self.main_menu.w, 1920)
        self.assertEqual(self.main_menu.h, 1080)
        self.assertIs(self.main_menu.stage_select.screen, new_surface)

    def test_safe_draw_rect_and_primitives_swallow_corrupted_surface_errors(self):
        """Verify drawing primitives smoothly handle corrupted/unsupported surfaces without crashing."""
        test_surf = pygame.Surface((100, 100))

        # Normal drawing
        pygame.draw.rect(test_surf, (255, 0, 0), (10, 10, 50, 50), border_radius=5)
        pygame.draw.circle(test_surf, (0, 255, 0), (50, 50), 20)
        pygame.draw.line(test_surf, (0, 0, 255), (0, 0), (50, 50))
        pygame.draw.lines(test_surf, (255, 255, 0), True, [(0, 0), (20, 0), (20, 20)])
        pygame.draw.polygon(test_surf, (0, 255, 255), [(10, 10), (30, 10), (20, 30)])
        pygame.draw.ellipse(test_surf, (255, 0, 255), (10, 10, 40, 40))

        # Pass a mock or bad object that triggers ValueError/TypeError
        class MockCorruptedSurface:
            pass

        bad_surf = MockCorruptedSurface()
        # None of these should raise unhandled exceptions
        self.assertIsNone(pygame.draw.rect(bad_surf, (255, 0, 0), (0, 0, 10, 10), border_radius=3))
        self.assertIsNone(pygame.draw.circle(bad_surf, (255, 0, 0), (10, 10), 5))
        self.assertIsNone(pygame.draw.line(bad_surf, (255, 0, 0), (0, 0), (10, 10)))
        self.assertIsNone(pygame.draw.lines(bad_surf, (255, 0, 0), True, [(0, 0), (10, 10)]))
        self.assertIsNone(pygame.draw.polygon(bad_surf, (255, 0, 0), [(0, 0), (10, 0), (0, 10)]))
        self.assertIsNone(pygame.draw.ellipse(bad_surf, (255, 0, 0), (0, 0, 10, 10)))


if __name__ == '__main__':
    unittest.main()
