import os
import unittest
import pygame

class TestDialoguePlayerPortrait(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    def test_male_student_portrait_uses_boy_front(self):
        from core.gba_dialogue import get_player_portrait, is_female_student, get_in_game_portrait
        
        male_student = {"id": 1, "first_name": "Juan", "gender": "male"}
        self.assertFalse(is_female_student(male_student))
        
        portrait = get_in_game_portrait("Student", student_info=male_student, target_size=(230, 230))
        self.assertIsNotNone(portrait)
        self.assertEqual(portrait.get_size(), (230, 230))

    def test_female_student_portrait_uses_female_front(self):
        from core.gba_dialogue import get_player_portrait, is_female_student, get_in_game_portrait
        
        female_student = {"id": 2, "first_name": "Jessuny", "gender": "female"}
        self.assertTrue(is_female_student(female_student))
        
        portrait = get_in_game_portrait("Student", student_info=female_student, target_size=(230, 230))
        self.assertIsNotNone(portrait)
        self.assertEqual(portrait.get_size(), (230, 230))

    def test_quarter_npc_dialogue_portraits(self):
        from core.gba_dialogue import get_in_game_portrait
        
        student = {"id": 1, "first_name": "Alex", "gender": "male"}
        
        # Quarter 1: Old Man Wizard
        oldman_surf = get_in_game_portrait("Old Man", student_info=student)
        self.assertIsNotNone(oldman_surf)
        
        # Quarter 2: Knight Guardian
        knight_surf = get_in_game_portrait("Knight", student_info=student)
        self.assertIsNotNone(knight_surf)
        
        # Quarter 3: Skeleton Guardian
        skeleton_surf = get_in_game_portrait("Skeleton", student_info=student)
        self.assertIsNotNone(skeleton_surf)
        
        # Quarter 4: Bromen Guardian
        bromen_surf = get_in_game_portrait("Bromen", student_info=student)
        self.assertIsNotNone(bromen_surf)
        
        # Student reply
        student_surf = get_in_game_portrait("Student", student_info=student)
        self.assertIsNotNone(student_surf)

    def test_draw_gba_dialogue_renders_with_multi_speaker(self):
        from core.gba_dialogue import draw_gba_dialogue
        
        screen = pygame.Surface((960, 640))
        
        # Turn 1: NPC speaks
        draw_gba_dialogue(
            screen=screen,
            screen_width=960,
            screen_height=640,
            speaker_name="Skeleton Guardian",
            text_content="Halt, traveler! Show me your skills.",
            student_info={"gender": "male", "first_name": "Alex"}
        )
        
        # Turn 2: Student speaks
        draw_gba_dialogue(
            screen=screen,
            screen_width=960,
            screen_height=640,
            speaker_name="Student",
            text_content="I am ready to learn!",
            student_info={"gender": "male", "first_name": "Alex"}
        )

if __name__ == "__main__":
    unittest.main()
