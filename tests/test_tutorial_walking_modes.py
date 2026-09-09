import unittest
import pygame
from screens.tutorial import TutorialScreen

class TestTutorialWalkingModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        from screens.main_menu import MainMenu
        self.main_menu = MainMenu(self.screen)
        self.tut = TutorialScreen(self.screen, self.main_menu)
        self.main_menu.tutorial = self.tut
        self.main_menu.current_screen = "tutorial"

    def test_01_mouse_cursor_steering_without_webcam(self):
        """Moving the mouse cursor (NO HAND) outside 45px deadzone must steer the player."""
        self.tut.phase = 1
        self.tut.quiz_state = 0
        self.tut.click_dest = None

        # Position camera and compute player screen position
        self.tut.update()
        pl_screen_x = (self.tut.player_x - self.tut.camera_x + 16) * 1.5
        pl_screen_y = (self.tut.player_y - self.tut.camera_y + 16) * 1.5

        # 1. Move mouse cursor to the right
        self.tut.cursor_pos = (int(pl_screen_x + 100), int(pl_screen_y))
        self.tut.update_gesture(self.tut.cursor_pos, 0, 0.9, "NO HAND")
        
        start_x = self.tut.player_x
        self.tut.update_player_movement()
        self.assertGreater(self.tut.player_x, start_x, "Mouse cursor to the right must move player right")
        self.assertEqual(self.tut.player_dir, "right")

        # 2. Move mouse cursor down
        self.tut.cursor_pos = (int(pl_screen_x), int(pl_screen_y + 100))
        self.tut.update_gesture(self.tut.cursor_pos, 0, 0.9, "NO HAND")
        start_y = self.tut.player_y
        self.tut.update_player_movement()
        self.assertGreater(self.tut.player_y, start_y, "Mouse cursor down must move player down")
        self.assertEqual(self.tut.player_dir, "down")

        # 3. Inside deadzone (cursor right on player)
        self.tut.cursor_pos = (int(pl_screen_x), int(pl_screen_y))
        self.tut.update_gesture(self.tut.cursor_pos, 0, 0.9, "NO HAND")
        cur_x, cur_y = self.tut.player_x, self.tut.player_y
        self.tut.update_player_movement()
        self.assertEqual(self.tut.player_x, cur_x, "Inside deadzone player must stay still")
        self.assertEqual(self.tut.player_y, cur_y, "Inside deadzone player must stay still")

    def test_02_hand_gesture_steering(self):
        """Open hand tracking gesture must steer the player."""
        self.tut.phase = 1
        self.tut.quiz_state = 0
        self.tut.click_dest = None

        self.tut.update()
        pl_screen_x = (self.tut.player_x - self.tut.camera_x + 16) * 1.5
        pl_screen_y = (self.tut.player_y - self.tut.camera_y + 16) * 1.5

        # Open hand to the right
        self.tut.cursor_pos = (int(pl_screen_x + 120), int(pl_screen_y))
        self.tut.update_gesture(self.tut.cursor_pos, 0, 0.9, "OPEN")
        self.assertTrue(self.tut.hand_detected)

        start_x = self.tut.player_x
        self.tut.update_player_movement()
        self.assertGreater(self.tut.player_x, start_x, "Hand gesture right must move player right")

    def test_03_click_dest_clears_on_collision_block(self):
        """If click_dest leads directly into an obstacle, it must safely clear instead of deadlocking."""
        self.tut.phase = 1
        self.tut.quiz_state = 0

        # Set click_dest inside top wall / tree at row 0 (world y = 10)
        self.tut.click_dest = (self.tut.player_x, 10)
        
        # Advance until collision
        for _ in range(30):
            self.tut.update()

        # click_dest must be cleared or not prevent manual steering
        pl_screen_x = (self.tut.player_x - self.tut.camera_x + 16) * 1.5
        pl_screen_y = (self.tut.player_y - self.tut.camera_y + 16) * 1.5

        # User now steers right with mouse/hand
        self.tut.cursor_pos = (int(pl_screen_x + 120), int(pl_screen_y))
        self.tut.update_gesture(self.tut.cursor_pos, 0, 0.9, "NO HAND")
        
        start_x = self.tut.player_x
        self.tut.update()
        self.assertGreater(self.tut.player_x, start_x, "Steering right must work even after hitting obstacle")

if __name__ == '__main__':
    unittest.main()
