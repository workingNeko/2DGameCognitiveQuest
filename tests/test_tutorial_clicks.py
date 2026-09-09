import unittest
import os
import pygame
import math

class TestTutorialClicks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        from screens.main_menu import MainMenu
        self.main_menu = MainMenu(self.screen)
        from screens.tutorial import TutorialScreen
        self.tut = TutorialScreen(self.screen, self.main_menu)
        self.main_menu.tutorial = self.tut
        self.main_menu.current_screen = "tutorial"

    def test_01_npc_click_opens_quiz_modal(self):
        """Clicking directly on the Guide Sage or nearby in Phase 1 must open the sample quiz modal"""
        self.assertEqual(self.tut.phase, 1)
        self.assertEqual(self.tut.quiz_state, 0)
        
        # Calculate screen coordinates of Guide Sage
        screen_npc_x = (self.tut.npc_tile_x * 32 - self.tut.camera_x) * 1.5
        screen_npc_y = (self.tut.npc_tile_y * 32 - self.tut.camera_y) * 1.5
        
        # Click on the Guide Sage
        self.tut.trigger_click((screen_npc_x, screen_npc_y))
        
        self.assertEqual(self.tut.phase, 3, "Phase must advance to 3 (Wisdom Trial)")
        self.assertEqual(self.tut.quiz_state, 1, "Quiz modal must open (quiz_state = 1)")

    def test_02_quiz_choice_selection_by_click(self):
        """Clicking on answer choices must submit the answer and update quiz state"""
        self.tut.phase = 3
        self.tut.quiz_state = 1
        self.tut.eliminated_choice = None
        
        box_w, box_h = 600, 390
        box_x = (1280 - box_w) // 2
        box_y = (720 - box_h) // 2
        button_w, button_h = 560, 50
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 142
        spacing = 56

        # 1. Click wrong answer (Choice A, index 0)
        choice_a_pos = (button_x + 50, button_y_start + 0 * spacing + 20)
        self.tut.trigger_click(choice_a_pos)
        self.assertEqual(self.tut.quiz_state, 2, "Wrong answer must switch quiz_state to 2 (Retry Dialog)")
        self.assertEqual(self.tut.eliminated_choice, 0, "Choice A must be eliminated")

        # 2. Click "Try Again"
        btn_retry = pygame.Rect(box_x + (box_w - 230) // 2, box_y + 180, 230, 48)
        self.tut.trigger_click(btn_retry.center)
        self.assertEqual(self.tut.quiz_state, 1, "Clicking Try Again must return to quiz question (quiz_state = 1)")

        # 3. Click correct answer (Choice B, index 1)
        choice_b_pos = (button_x + 50, button_y_start + 1 * spacing + 20)
        self.tut.trigger_click(choice_b_pos)
        self.assertEqual(self.tut.quiz_state, 3, "Correct answer must switch quiz_state to 3 (Mastered Dialog)")

        # 4. Click "Continue >>"
        btn_continue = pygame.Rect(box_x + (box_w - 240) // 2, box_y + 195, 240, 48)
        self.tut.trigger_click(btn_continue.center)
        self.assertEqual(self.tut.quiz_state, 0, "Clicking Continue must close modal")
        self.assertEqual(self.tut.phase, 4, "Phase must advance to 4 (Portal Odyssey)")

    def test_03_demo_card_click_selects_correct_answer(self):
        """Clicking on the tutorial helper card should also select Choice B"""
        self.tut.phase = 3
        self.tut.quiz_state = 1
        box_w, box_h = 600, 390
        box_x = (1280 - box_w) // 2
        box_y = (720 - box_h) // 2
        button_y_start = box_y + 142
        spacing = 56
        demo_card_x = box_x + box_w + 16
        demo_card_y = button_y_start + 1 * spacing - 24
        
        self.tut.trigger_click((demo_card_x + 20, demo_card_y + 20))
        self.assertEqual(self.tut.quiz_state, 3, "Clicking helper card must select correct answer B")

    def test_04_portal_click_finishes_tutorial(self):
        """Clicking on or near the exit portal in Phase 4 completes the tutorial"""
        self.tut.phase = 4
        self.tut.quiz_state = 0
        
        p_sx = (self.tut.portal_tile_x * 32 - self.tut.camera_x) * 1.5
        p_sy = (self.tut.portal_tile_y * 32 - self.tut.camera_y) * 1.5
        
        self.tut.trigger_click((p_sx, p_sy))
        self.assertEqual(self.main_menu.current_screen, "stage_select", "Clicking exit portal must open stage_select")

    def test_05_pause_menu_mouse_clicks_work(self):
        """Clicking buttons inside pause menu must not be blocked when paused"""
        self.assertFalse(self.tut.pause_menu.is_paused)
        # Open pause menu via click on pause button
        self.tut.trigger_click(self.tut.pause_menu.pause_btn_rect.center)
        self.assertTrue(self.tut.pause_menu.is_paused, "Pause button must pause the game")
        
        # Click Resume button inside the pause modal via handle_event
        resume_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.tut.pause_menu.resume_rect.center})
        self.tut.handle_event(resume_event)
        self.assertFalse(self.tut.pause_menu.is_paused, "Clicking Resume must unpause the game cleanly")

    def test_06_click_to_move_navigation(self):
        """Clicking walkable ground during phase 1 sets click_dest and player walks towards it"""
        self.tut.phase = 1
        self.tut.quiz_state = 0
        start_x, start_y = self.tut.player_x, self.tut.player_y
        
        # Click 150px to the right of the player on the screen
        pl_screen_x = (start_x - self.tut.camera_x + 16) * 1.5
        pl_screen_y = (start_y - self.tut.camera_y + 16) * 1.5
        target_click = (pl_screen_x + 150, pl_screen_y)
        
        self.tut.trigger_click(target_click)
        self.assertIsNotNone(self.tut.click_dest, "Clicking ground must set click_dest")
        
        # Update movement
        self.tut.update_player_movement()
        self.assertGreater(self.tut.player_x, start_x, "Player must move towards click destination")
        self.assertEqual(self.tut.player_dir, "right")

    def test_07_main_menu_cursor_pos_synchronization(self):
        """Mouse movement must immediately update main_menu cursor coordinates"""
        move_event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (345, 567), 'rel': (5, 5), 'buttons': (0, 0, 0)})
        self.main_menu.handle_event(move_event)
        self.assertEqual(self.main_menu.cursor_pos, (345, 567))
        self.assertEqual(self.tut.cursor_pos, (345, 567))

if __name__ == '__main__':
    unittest.main()
