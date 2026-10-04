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
        self.tut.intro_anim_active = False
        self.tut.demo_video_active = False
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
        self.tut.update_player_movement()
        self.assertGreater(self.tut.player_x, start_x, "Steering right must work even after hitting obstacle")

    def test_04_grade2_visual_rendering(self):
        """Verify all Grade 2 visual components (demonstration video, welcome dialog, hand tracker helper, markers, quiz, portal) render cleanly."""
        # 1. Test Demonstration Video Rendering across all 4 Chapters
        self.tut.demo_video_active = True
        for chap_idx in range(4):
            self.tut.demo_video_chapter = chap_idx
            self.tut.draw()

        self.tut.demo_video_active = False

        # 2. Test Welcome Dialog & Hand Tracker in Phase 1 with NO HAND
        self.tut.phase = 1
        self.tut.quiz_state = 0
        self.tut.intro_dialog_open = True
        self.tut.update_gesture((640, 360), 0, 0.9, "NO HAND")
        self.tut.draw()

        # 3. Test Welcome Dialog with FIST gesture
        self.tut.update_gesture((640, 360), 10.0, 0.9, "FIST")
        self.tut.draw()

        # 4. Test Gameplay with OPEN Hand (Walking & Bouncing Markers on Star)
        self.tut.intro_dialog_open = False
        self.tut.update_gesture((740, 360), 0, 0.9, "OPEN")
        self.tut.draw()

        # 5. Test Phase 3 Sample Quiz with Grade 2 Math Visual blocks & Gesture Demo
        self.tut.phase = 3
        self.tut.quiz_state = 1
        self.tut.draw()

        # 6. Test Phase 3 Wrong Dialog Feedback
        self.tut.quiz_state = 2
        self.tut.draw()

        # 7. Test Phase 3 Correct Dialog Feedback
        self.tut.quiz_state = 3
        self.tut.draw()

        # 8. Test Phase 4 Exit Portal Odyssey
        self.tut.phase = 4
        self.tut.quiz_state = 0
        self.tut.draw()

    def test_05_demonstration_video_navigation_and_controls(self):
        """Test demonstration video playback, chapter navigation, practice click, and skip"""
        self.tut.demo_video_active = True
        self.tut.demo_video_chapter = 0
        self.tut.demo_video_playing = True
        self.tut.demo_video_timer = 0.0

        # Update should advance timer
        self.tut.update()
        self.assertGreater(self.tut.demo_video_timer, 0.0)

        # Keyboard Right / D advances chapter
        right_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT})
        self.tut.handle_event(right_event)
        self.assertEqual(self.tut.demo_video_chapter, 1)

        # Keyboard Left / A moves back
        left_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT})
        self.tut.handle_event(left_event)
        self.assertEqual(self.tut.demo_video_chapter, 0)

        # Chapter 3 (Practice test click)
        self.tut.demo_video_chapter = 3
        vw = min(1060, self.tut.width - 40)
        vh = min(580, self.tut.height - 40)
        vx = (self.tut.width - vw) // 2
        vy = (self.tut.height - vh) // 2
        practice_click_pos = (vx + 100, vy + 300)
        self.tut.trigger_click(practice_click_pos)
        self.assertTrue(self.tut.demo_practice_clicked)

        # Skip video closes demo_video_active
        skip_click_pos = (vx + vw - 80, vy + 25)
        self.tut.trigger_click(skip_click_pos)
        self.assertFalse(self.tut.demo_video_active)

if __name__ == '__main__':
    unittest.main()

