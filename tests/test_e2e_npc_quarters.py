# tests/test_e2e_npc_quarters.py
import os
import sys
import unittest
import pygame

# Use headless video driver for testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.main_menu import MainMenu
from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4
from core.npc_scripts import get_map_instructions, get_station_script, get_mentor_script

class TestE2ENPCQuarters(unittest.TestCase):
    def setUp(self):
        self.screen = screen
        self.mm = MainMenu(self.screen)
        self.mm.selected_student = {"id": 1, "student_id": "1001", "first_name": "HeroTester"}

    def test_quarter1_npc_integration(self):
        q1 = Quarter1(self.screen, self.mm, "map1.txt")
        # Check instruction modal
        self.assertTrue(hasattr(q1, "instruction_modal"))
        self.assertTrue(q1.instruction_modal.is_visible)
        self.assertIn("HeroTester", q1.instruction_modal.subtitle)

        # Fist hold dismissal test (0.95s fist hold)
        fist_dismissed = q1.instruction_modal.handle_fist_hold(True, 0.95, 0.90)
        self.assertTrue(fist_dismissed)
        self.assertFalse(q1.instruction_modal.is_visible)

        # Check guide button re-opens
        q1.show_instructions()
        self.assertTrue(q1.instruction_modal.is_visible)

        # Press space to dismiss modal
        space_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        dismissed = q1.instruction_modal.handle_event(space_event)
        self.assertTrue(dismissed)
        self.assertFalse(q1.instruction_modal.is_visible)

        # Check greeting dialog exists
        self.assertTrue(hasattr(q1, "greeting_dialog"))

        # Verify scripts for map1
        st1_script = get_station_script("quarter1", "map1.txt", 1, "HeroTester")
        self.assertEqual(st1_script["name"], "Circle Guardian")
        self.assertIn("Circle Guardian", st1_script["greeting"])

        # Test draw methods do not crash
        q1.quiz_station_index = 1
        q1.draw_wrong_dialog()
        q1.draw_out_of_tries_dialog()
        q1.draw_correct_dialog()

    def test_quarter2_npc_integration(self):
        q2 = Quarter2(self.screen, self.mm, "map4.txt")
        self.assertTrue(hasattr(q2, "instruction_modal"))
        self.assertTrue(q2.instruction_modal.is_visible)
        self.assertIn("HeroTester", q2.instruction_modal.subtitle)

        # Dismiss modal via fist hold
        fist_dismissed = q2.instruction_modal.handle_fist_hold(True, 0.95, 0.90)
        self.assertTrue(fist_dismissed)
        self.assertFalse(q2.instruction_modal.is_visible)

        # Check greeting dialog exists
        self.assertTrue(hasattr(q2, "greeting_dialog"))

        # Check Map 4 vendors
        for i, expected_name in enumerate(["Aling Nena", "Mang Pedring", "Kuya Jomar", "Ate Maria", "Mang Carding"], 1):
            sc = get_station_script("quarter2", "map4.txt", i, "HeroTester")
            self.assertIn(expected_name, sc["name"])

        # Check Map 5 mentor (Knight Guardian)
        m5 = get_mentor_script("quarter2", "map5.txt", "HeroTester")
        self.assertEqual(m5["name"], "Knight Guardian")

        # Test drawing feedback dialogs
        q2.quiz_station_index = 1
        q2.draw_wrong_dialog()
        q2.draw_out_of_tries_dialog()
        q2.draw_correct_dialog()

    def test_quarter3_npc_integration(self):
        q3 = Quarter3(self.screen, self.mm, "map7.txt")
        self.assertTrue(hasattr(q3, "instruction_modal"))
        self.assertTrue(q3.instruction_modal.is_visible)
        self.assertIn("HeroTester", q3.instruction_modal.subtitle)

        q3.instruction_modal.hide()
        self.assertFalse(q3.instruction_modal.is_visible)

        self.assertTrue(hasattr(q3, "greeting_dialog"))

        # Check Desert Sage script
        sc = get_station_script("quarter3", "map7.txt", 1, "HeroTester")
        self.assertEqual(sc["name"], "Desert Sage")
        self.assertIn("trade tablet", sc["greeting"])

        # Check Desert Vault Keeper mentor
        m7 = get_mentor_script("quarter3", "map7.txt", "HeroTester")
        self.assertEqual(m7["name"], "Desert Vault Keeper")

        # Test drawing feedback dialogs
        q3.quiz_station_index = 1
        q3.draw_wrong_dialog()
        q3.draw_out_of_tries_dialog()
        q3.draw_correct_dialog()

    def test_quarter4_npc_integration(self):
        q4 = Quarter4(self.screen, self.mm, "map10.txt")
        self.assertTrue(hasattr(q4, "instruction_modal"))
        self.assertTrue(q4.instruction_modal.is_visible)
        self.assertIn("HeroTester", q4.instruction_modal.subtitle)

        q4.instruction_modal.hide()
        self.assertFalse(q4.instruction_modal.is_visible)

        self.assertTrue(hasattr(q4, "greeting_dialog"))

        # Check Water Guardian script
        sc = get_station_script("quarter4", "map10.txt", 1, "HeroTester")
        self.assertEqual(sc["name"], "Water Guardian")
        self.assertIn("waters", sc["greeting"])

        # Check Temple Elder mentor
        m10 = get_mentor_script("quarter4", "map10.txt", "HeroTester")
        self.assertEqual(m10["name"], "Temple Elder")

        # Test drawing feedback dialogs
        q4.quiz_station_index = 1
        q4.draw_wrong_dialog()
        q4.draw_out_of_tries_dialog()
        q4.draw_correct_dialog()

if __name__ == "__main__":
    unittest.main()
