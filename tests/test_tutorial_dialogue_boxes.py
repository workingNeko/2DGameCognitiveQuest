import unittest
import pygame
from screens.tutorial import TutorialScreen

class TestTutorialDialogueBoxes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        from screens.main_menu import MainMenu
        self.main_menu = MainMenu(self.screen)
        self.tut = TutorialScreen(self.screen, self.main_menu)
        self.tut.intro_anim_active = False
        self.tut.demo_video_active = False
        self.main_menu.tutorial = self.tut
        self.main_menu.current_screen = "tutorial"

    def test_01_welcome_dialog_initial_state(self):
        """Initial tutorial state must have intro_dialog_open = True and render without errors"""
        self.assertTrue(self.tut.intro_dialog_open, "intro_dialog_open must be True at tutorial start")
        self.assertEqual(self.tut.phase, 1)
        self.assertEqual(self.tut.quiz_state, 0)
        
        # Test rendering of welcome dialogue box
        self.tut.draw()

    def test_02_welcome_dialog_dismiss_via_keypress(self):
        """Pressing Space or Enter dismisses the welcome dialogue box cleanly"""
        self.assertTrue(self.tut.intro_dialog_open)
        
        space_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE})
        self.tut.handle_event(space_event)
        self.assertFalse(self.tut.intro_dialog_open, "Space must dismiss intro_dialog_open")

    def test_03_welcome_dialog_dismiss_via_movement(self):
        """Walking or steering the character dismisses the welcome dialogue box cleanly"""
        self.assertTrue(self.tut.intro_dialog_open)
        
        # Move cursor to steer right
        pl_screen_x = (self.tut.player_x - self.tut.camera_x + 16) * 1.5
        pl_screen_y = (self.tut.player_y - self.tut.camera_y + 16) * 1.5
        self.tut.cursor_pos = (int(pl_screen_x + 100), int(pl_screen_y))
        self.tut.update_gesture(self.tut.cursor_pos, 0, 0.9, "NO HAND")
        self.tut.update_player_movement()
        
        self.assertFalse(self.tut.intro_dialog_open, "Player movement must dismiss intro_dialog_open")

    def test_04_dialog_sequence_rendering(self):
        """All tutorial dialogue boxes (Welcome, Quiz, Wrong, Correct) render without exception"""
        # 1. Welcome dialog
        self.tut.intro_dialog_open = True
        self.tut.phase = 1
        self.tut.quiz_state = 0
        self.tut.draw()
        
        # 2. Sample Quiz dialog
        self.tut.intro_dialog_open = False
        self.tut.phase = 3
        self.tut.quiz_state = 1
        self.tut.draw()
        
        # 3. Wrong Feedback dialog
        self.tut.quiz_state = 2
        self.tut.draw()
        
        # 4. Mastered Correct dialog
        self.tut.quiz_state = 3
        self.tut.draw()

if __name__ == '__main__':
    unittest.main()
