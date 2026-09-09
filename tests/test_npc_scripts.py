# tests/test_npc_scripts.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from core.npc_scripts import (
    get_map_instructions,
    get_station_script,
    get_mentor_script,
    MAP_INSTRUCTIONS_DATA,
    STATION_SCRIPTS_DATA,
    MENTOR_SCRIPTS_DATA
)

class TestNPCScripts(unittest.TestCase):
    def test_map_instructions_all_maps(self):
        # Maps 1 to 12
        for m in ["map1.txt", "map2.txt", "map3.txt", "map4.txt", "map5.txt", "map6.txt"]:
            inst = get_map_instructions("quarter1" if "map1" in m or "map2" in m or "map3" in m else "quarter2", m, "Hero")
            self.assertIn("title", inst)
            self.assertIn("subtitle", inst)
            self.assertIn("Hero", inst["subtitle"])
            self.assertTrue(len(inst["steps"]) >= 2)

        # Quarter 3 and Quarter 4
        for q, maps in [("quarter3", ["map7.txt", "map8.txt", "map9.txt"]), ("quarter4", ["map10.txt", "map11.txt", "map12.txt"])]:
            for m in maps:
                inst = get_map_instructions(q, m, "Hero")
                self.assertIn("title", inst)
                self.assertIn("Hero", inst["subtitle"])
                self.assertTrue(len(inst["steps"]) >= 2)

    def test_station_scripts_q1(self):
        # Map 1 has specific guardians: Circle, Heart, Square, Star, Diamond
        expected_names = ["Circle Guardian", "Heart Guardian", "Square Guardian", "Star Guardian", "Diamond Guardian"]
        for st in range(1, 6):
            data = get_station_script("quarter1", "map1.txt", st, "Hero")
            self.assertEqual(data["name"], expected_names[st - 1])
            self.assertTrue(len(data["greeting"]) > 10)
            self.assertTrue(len(data["wrong_retry"]) > 5)
            self.assertTrue(len(data["out_of_tries"]) > 10)
            self.assertTrue(len(data["correct_praise"]) > 10)

    def test_station_scripts_q2(self):
        # Map 4 has vendors
        expected_vendors = [
            "Aling Nena (Sari-Sari Store)",
            "Mang Pedring (Sorbetes Cart)",
            "Kuya Jomar (Jeepney Terminal)",
            "Ate Maria (Market Fruit Stand)",
            "Mang Carding (Parol Workshop)"
        ]
        for st in range(1, 6):
            data = get_station_script("quarter2", "map4.txt", st, "Hero")
            self.assertEqual(data["name"], expected_vendors[st - 1])
            self.assertTrue(len(data["greeting"]) > 10)
            self.assertTrue(len(data["wrong_retry"]) > 5)
            self.assertTrue(len(data["out_of_tries"]) > 10)
            self.assertTrue(len(data["correct_praise"]) > 10)

    def test_station_scripts_q3_and_q4(self):
        for st in range(1, 6):
            data3 = get_station_script("quarter3", "map7.txt", st, "Hero")
            self.assertEqual(data3["name"], "Desert Sage")
            self.assertTrue("trade tablet" in data3["greeting"] or "sands" in data3["greeting"])

            data4 = get_station_script("quarter4", "map10.txt", st, "Hero")
            self.assertEqual(data4["name"], "Water Guardian")
            self.assertTrue("waters" in data4["greeting"] or "deep" in data4["greeting"])

    def test_mentors(self):
        m1 = get_mentor_script("quarter1", "map1.txt", "Hero")
        self.assertEqual(m1["name"], "Old Man")
        self.assertTrue("bridge first" in m1["incomplete"])

        m4 = get_mentor_script("quarter2", "map4.txt", "Hero")
        self.assertEqual(m4["name"], "Barrio Leader")
        self.assertTrue("all 5 vendors" in m4["incomplete"])

        m5 = get_mentor_script("quarter2", "map5.txt", "Hero")
        self.assertEqual(m5["name"], "Master Carpenter")

        m6 = get_mentor_script("quarter2", "map6.txt", "Hero")
        self.assertEqual(m6["name"], "Hermano Mayor")

        m7 = get_mentor_script("quarter3", "map7.txt", "Hero")
        self.assertEqual(m7["name"], "Desert Vault Keeper")

        m10 = get_mentor_script("quarter4", "map10.txt", "Hero")
        self.assertEqual(m10["name"], "Temple Elder")

    def test_polymorphic_calls_and_aliases(self):
        # Test 2-arg get_map_instructions
        inst = get_map_instructions("map10.txt", "Alice")
        self.assertIn("THE WATER TEMPLE SANCTUARY", inst["title"])
        self.assertIn("Alice", inst["subtitle"])

        # Test 2-arg get_station_script and key aliases
        st = get_station_script("map4.txt", 2, "Alice")
        self.assertEqual(st["name"], "Mang Pedring (Sorbetes Cart)")
        self.assertEqual(st["npc_name"], st["name"])
        self.assertEqual(st["role"], st["npc_title"])
        self.assertEqual(st["wrong_retry"], st["retry_line"])
        self.assertEqual(st["out_of_tries"], st["out_of_tries_line"])
        self.assertEqual(st["correct_praise"], st["praise_line"])
        self.assertEqual(st["item_awarded"], "Pure Coconut Milk")

        # Test 2-arg get_mentor_script and key aliases
        m = get_mentor_script("map7.txt", "Alice")
        self.assertEqual(m["name"], "Desert Vault Keeper")
        self.assertEqual(m["mentor_name"], m["name"])
        self.assertEqual(m["role"], m["mentor_title"])
        self.assertEqual(m["complete"], m["complete_dialogue"])
        self.assertEqual(m["incomplete"], m["incomplete_dialogue"])

    def test_dialog_system_components(self):
        import pygame
        pygame.init()
        screen = pygame.Surface((800, 600))
        from core.npc_dialog_system import InstructionModal, NPCGreetingDialog

        modal = InstructionModal(screen, 800, 600)
        self.assertFalse(modal.is_visible)
        inst_data = get_map_instructions("map1.txt", "Tester")
        modal.show(inst_data)
        self.assertTrue(modal.is_visible)
        modal.update(0.016, (400, 300), fist_hold_pct=0.5)
        modal.draw((400, 300))
        modal.hide()
        self.assertFalse(modal.is_visible)

        greeting = NPCGreetingDialog(screen, 800, 600)
        self.assertFalse(greeting.is_visible)
        greeting.show("Guardian Bromen", "Water Temple Guardian", "Greetings!")
        self.assertTrue(greeting.is_visible)
        greeting.update(0.016, (400, 300), fist_hold_pct=0.5)
        greeting.draw((400, 300))
        greeting.hide()
        self.assertFalse(greeting.is_visible)

if __name__ == "__main__":
    unittest.main()
