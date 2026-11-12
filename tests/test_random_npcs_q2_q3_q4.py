"""
Unit tests verifying NPC randomization applied ONLY to Quarter 2, Quarter 3, and Summative Assessment (Quarter 4),
while Quarter 1 remains in its original authentic order.
"""
import unittest
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4

class DummyMainMenu:
    def __init__(self):
        self.selected_student = {"first_name": "TestStudent"}
        self.student_code = "TEST01"
        self.audio_manager = DummyAudio()

class DummyAudio:
    def play_sfx(self, *args, **kwargs): pass
    def stop_music(self): pass
    def play_music(self, *args, **kwargs): pass
    def get_sound(self, *args, **kwargs): return None

class TestRandomNPCsQuarters234(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screen = pygame.display.set_mode((1280, 720))

    def test_quarter1_remains_original_and_unrandomized(self):
        q1 = Quarter1(self.screen, DummyMainMenu(), map_name="map1.txt")
        # In original Quarter 1, stations 1..5 are strictly circle, heart, square, star, diamond
        expected_order = {1: "circle", 2: "heart", 3: "square", 4: "star", 5: "diamond"}
        for st_id, expected_name in expected_order.items():
            if st_id in q1.shape_npcs:
                self.assertEqual(q1.shape_npcs[st_id]["name"], expected_name)

    def test_quarter2_random_filipino_npcs_up_to_15(self):
        q2 = Quarter2(self.screen, DummyMainMenu(), map_name="map4.txt")
        mock_questions = [
            {"question": f"Q2 Question {i}?", "choices": ["A", "B", "C", "D"], "correct": 0}
            for i in range(1, 16)
        ]
        q2.cloud_sync_quarter2_questions(mock_questions)
        self.assertEqual(q2.active_station_count, 15)
        self.assertEqual(len(q2.station_npc_info), 15)

        assigned_chars = []
        for i in range(1, 16):
            self.assertIn(i, q2.station_npc_info)
            info = q2.station_npc_info[i]
            char_id = info.get("char_id")
            self.assertIn(char_id, [1, 2, 3, 4, 5])
            self.assertEqual(len(info["frames"]), 8)
            assigned_chars.append(char_id)

        # Check all 5 authentic Filipino characters appear across 15 questions
        self.assertEqual(len(set(assigned_chars)), 5)
        # Check no adjacent identical NPCs
        for i in range(len(assigned_chars) - 1):
            self.assertNotEqual(assigned_chars[i], assigned_chars[i + 1])

    def test_quarter3_random_number_npcs_up_to_15(self):
        q3 = Quarter3(self.screen, DummyMainMenu(), map_name="map7.txt")
        mock_questions = [
            {"question": f"Q3 Question {i}?", "choices": ["A", "B", "C", "D"], "correct": 0}
            for i in range(1, 16)
        ]
        q3.cloud_sync_quarter3_questions(mock_questions)
        self.assertEqual(q3.active_station_count, 15)
        self.assertEqual(len(q3.station_npcs), 15)

        assigned_nums = []
        for i in range(1, 16):
            self.assertIn(i, q3.station_npcs)
            info = q3.station_npcs[i]
            char_id = info.get("char_id")
            self.assertIn(char_id, [1, 2, 3, 4, 5])
            self.assertEqual(len(info["frames"]), 8)
            assigned_nums.append(char_id)

        # Check all 5 authentic Number characters appear across 15 questions
        self.assertEqual(len(set(assigned_nums)), 5)
        # Check no adjacent identical NPCs
        for i in range(len(assigned_nums) - 1):
            self.assertNotEqual(assigned_nums[i], assigned_nums[i + 1])

    def test_quarter4_summative_random_water_guardians_up_to_15(self):
        q4 = Quarter4(self.screen, DummyMainMenu(), map_name="map10.txt")
        mock_questions = [
            {"question": f"Summative Question {i}?", "choices": ["A", "B", "C", "D"], "correct": 0}
            for i in range(1, 16)
        ]
        q4.cloud_sync_quarter4_questions(mock_questions)
        self.assertEqual(q4.active_station_count, 15)
        self.assertEqual(len(q4.station_npcs), 15)

        assigned_guardians = []
        for i in range(1, 16):
            self.assertIn(i, q4.station_npcs)
            info = q4.station_npcs[i]
            guardian_id = info.get("guardian_id")
            self.assertIn(guardian_id, [1, 2, 3, 4, 5, 6])
            self.assertEqual(len(info["frames"]), 8)
            assigned_guardians.append(guardian_id)

        # Check all 6 authentic Water Guardians appear across 15 questions
        self.assertEqual(len(set(assigned_guardians)), 6)
        # Check no adjacent identical NPCs
        for i in range(len(assigned_guardians) - 1):
            self.assertNotEqual(assigned_guardians[i], assigned_guardians[i + 1])

if __name__ == "__main__":
    unittest.main()

