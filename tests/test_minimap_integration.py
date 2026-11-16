# tests/test_minimap_integration.py
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


class DummyMainMenu:
    def __init__(self):
        self.cursor_pos = (640, 360)
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.current_gesture = "NO HAND"
        self.hand_detected = False
        self.student_id = "test_student"
        self.selected_student = {"first_name": "Test", "last_name": "Student", "grade": 2}
        self.audio_manager = None
        self.current_screen = "stageselect"
        self.stageselect = None


class TestMiniMapIntegration(unittest.TestCase):
    def setUp(self):
        self.dummy_menu = DummyMainMenu()

    def test_stageselect_minimap(self):
        from screens.stageselect import StageSelect
        ss = StageSelect(screen, self.dummy_menu)
        self.assertTrue(hasattr(ss, "minimap"))
        self.assertIsInstance(ss.minimap, MiniMap)
        self.assertEqual(ss.minimap.theme, "sanctuary")
        self.assertTrue(ss.minimap.visible)

        # Toggle via K_m
        ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        res = ss.handle_event(ev)
        self.assertEqual(res, "minimap_toggle")
        self.assertFalse(ss.minimap.visible)

        # Draw without errors
        ss.draw()

    def test_quarter1_minimap(self):
        from screens.quarter1 import Quarter1
        q1 = Quarter1(screen, self.dummy_menu, "map1.txt", summative_num=1)
        self.assertTrue(hasattr(q1, "minimap"))
        self.assertIsInstance(q1.minimap, MiniMap)
        self.assertEqual(q1.minimap.theme, "sanctuary")
        self.assertTrue(q1.minimap.visible)

        # Toggle via K_m
        ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        res = q1.handle_event(ev)
        self.assertEqual(res, "minimap_toggle")
        self.assertFalse(q1.minimap.visible)

        # Draw without errors
        q1.draw()

    def test_quarter2_minimap(self):
        from screens.quarter2 import Quarter2
        q2 = Quarter2(screen, self.dummy_menu, "map4.txt", summative_num=1)
        self.assertTrue(hasattr(q2, "minimap"))
        self.assertIsInstance(q2.minimap, MiniMap)
        self.assertEqual(q2.minimap.theme, "kalye")
        self.assertTrue(q2.minimap.visible)

        # Toggle via K_m
        ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        res = q2.handle_event(ev)
        self.assertEqual(res, "minimap_toggle")
        self.assertFalse(q2.minimap.visible)

        # Draw without errors
        q2.draw()

    def test_quarter3_minimap(self):
        from screens.quarter3 import Quarter3
        q3 = Quarter3(screen, self.dummy_menu, "map7.txt", summative_num=1)
        self.assertTrue(hasattr(q3, "minimap"))
        self.assertIsInstance(q3.minimap, MiniMap)
        self.assertEqual(q3.minimap.theme, "desert")
        self.assertTrue(q3.minimap.visible)

        # Toggle via K_m
        ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        res = q3.handle_event(ev)
        self.assertEqual(res, "minimap_toggle")
        self.assertFalse(q3.minimap.visible)

        # Draw without errors
        q3.draw()

    def test_quarter4_minimap(self):
        from screens.quarter4 import Quarter4
        q4 = Quarter4(screen, self.dummy_menu, "map10.txt")
        self.assertTrue(hasattr(q4, "minimap"))
        self.assertIsInstance(q4.minimap, MiniMap)
        self.assertEqual(q4.minimap.theme, "water")
        self.assertTrue(q4.minimap.visible)

        # Toggle via K_m
        ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        res = q4.handle_event(ev)
        self.assertEqual(res, "minimap_toggle")
        self.assertFalse(q4.minimap.visible)

        # Draw without errors
        q4.draw()


if __name__ == "__main__":
    unittest.main()
