"""Comprehensive unit and integration tests verifying that the In-Game Pause Menu
works ALL THE TIME across Quarter 4 and all gameplay states.
"""

import unittest
from unittest.mock import MagicMock, patch
import pygame

# Initialize headless pygame display
pygame.init()
if pygame.display.get_surface() is None:
    pygame.display.set_mode((1280, 720))

from core.pause_menu import InGamePauseMenu
from screens.quarter4 import Quarter4


class MockMainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.current_screen = "quarter4"
        self.audio_manager = MagicMock()
        self.selected_student = {"id": "1", "name": "Test Student"}
        self.student_id = "1"
        self.student_db_id = 1
        self.stage_select_data = {}
        self.popup_state = None

    def open_audio_settings(self):
        self.popup_state = "audio_settings"


class TestQuarter4PauseMenuUniversal(unittest.TestCase):
    """Test suite ensuring Pause Menu works ALL THE TIME in Quarter 4."""

    @classmethod
    def setUpClass(cls):
        cls.screen = pygame.display.get_surface()

    def setUp(self):
        self.mm = MockMainMenu(self.screen)
        self.q4 = Quarter4(self.screen, self.mm, "map10.txt")

    def test_01_pause_menu_works_on_level_start_with_instruction_modal(self):
        """When Quarter 4 initializes, the instruction modal is visible. The pause menu must still work!"""
        self.assertTrue(self.q4.instruction_modal.is_visible)
        self.assertFalse(self.q4.pause_menu.is_paused)

        # 1. Click on Pause button while instruction modal is visible
        pause_pos = self.q4.pause_menu.pause_btn_rect.center
        self.q4.trigger_click(pause_pos)
        self.assertTrue(self.q4.pause_menu.is_paused, "Clicking Pause button with instruction modal open must pause game!")

        # 2. Click Resume to unpause
        resume_pos = self.q4.pause_menu.resume_rect.center
        self.q4.trigger_click(resume_pos)
        self.assertFalse(self.q4.pause_menu.is_paused, "Clicking Resume must unpause the game!")

        # 3. ESC key must also toggle pause while instruction modal is visible
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.q4.handle_event(esc_event)
        self.assertTrue(self.q4.pause_menu.is_paused, "Pressing ESC with instruction modal open must pause game!")

    def test_02_pause_menu_works_during_overworld_exploration(self):
        """During normal exploration, clicking Pause button and pressing ESC / P toggles pause."""
        self.q4.instruction_modal.hide()
        self.assertFalse(self.q4.pause_menu.is_paused)

        # Keyboard 'P' pauses
        p_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
        self.q4.handle_event(p_event)
        self.assertTrue(self.q4.pause_menu.is_paused)

        # Keyboard 'P' resumes
        self.q4.handle_event(p_event)
        self.assertFalse(self.q4.pause_menu.is_paused)

        # Mouse click pauses
        pause_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=self.q4.pause_menu.pause_btn_rect.center)
        self.q4.handle_event(pause_click)
        self.assertTrue(self.q4.pause_menu.is_paused)

    def test_03_pause_menu_works_during_greeting_dialog(self):
        """When talking to a station NPC (greeting dialog visible), pause menu must work."""
        self.q4.instruction_modal.hide()
        self.q4.greeting_dialog.show("Water Guardian", "Station 1", "Welcome to the trial!")
        self.assertTrue(self.q4.greeting_dialog.is_visible)

        # Press ESC to pause
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.q4.handle_event(esc_event)
        self.assertTrue(self.q4.pause_menu.is_paused, "ESC must open pause menu during greeting dialog!")

        # Click outside modal while paused -> does NOT dismiss greeting dialog behind
        self.q4.trigger_click((100, 100))
        self.assertTrue(self.q4.pause_menu.is_paused)
        self.assertTrue(self.q4.greeting_dialog.is_visible)

        # Resume
        self.q4.trigger_click(self.q4.pause_menu.resume_rect.center)
        self.assertFalse(self.q4.pause_menu.is_paused)
        self.assertTrue(self.q4.greeting_dialog.is_visible)

    def test_04_pause_menu_works_during_quiz_question_dialog(self):
        """When answering an active quiz question (quiz_state = 1), pause menu must work without losing question."""
        self.q4.instruction_modal.hide()
        self.q4.quiz_state = 1
        self.q4.quiz_station_index = 2

        # Click pause button
        pause_pos = self.q4.pause_menu.pause_btn_rect.center
        self.q4.trigger_click(pause_pos)
        self.assertTrue(self.q4.pause_menu.is_paused, "Pause button must work during active quiz question!")

        # Resume -> Quiz question remains active
        resume_pos = self.q4.pause_menu.resume_rect.center
        self.q4.trigger_click(resume_pos)
        self.assertFalse(self.q4.pause_menu.is_paused)
        self.assertEqual(self.q4.quiz_state, 1, "Quiz question state must be preserved when unpausing!")
        self.assertEqual(self.q4.quiz_station_index, 2)

    def test_05_pause_menu_works_during_bromen_dialogue(self):
        """When speaking to Bromen (Bromen dialogue state 1 or 2), pause menu must work."""
        self.q4.instruction_modal.hide()
        self.q4.bromen_dialogue_state = 2

        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.q4.handle_event(esc_event)
        self.assertTrue(self.q4.pause_menu.is_paused, "Pause menu must open during Bromen dialogue!")

        self.q4.pause_menu.close()
        self.assertFalse(self.q4.pause_menu.is_paused)

    def test_06_pause_menu_works_during_key_lock_puzzle(self):
        """When Key Lock Box puzzle is active on Map 10, pause menu must work."""
        self.q4.instruction_modal.hide()
        self.q4.key_puzzle_active = True
        self.q4.sync_ui_state()

        # Keyboard ESC pauses
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.q4.handle_event(esc_event)
        self.assertTrue(self.q4.pause_menu.is_paused, "Pause menu must open during Key Lock puzzle!")

        # Pause button click while paused does not leak to puzzle
        self.q4.trigger_click(self.q4.pause_menu.resume_rect.center)
        self.assertFalse(self.q4.pause_menu.is_paused)
        self.assertTrue(self.q4.key_puzzle_active, "Puzzle remains active after resuming!")

    def test_07_pause_menu_works_during_addition_puzzle_on_map12(self):
        """When on Map 12 with the Addition Helm puzzle active, pause menu must work."""
        q4_map12 = Quarter4(self.screen, self.mm, "map12.txt")
        q4_map12.instruction_modal.hide()
        q4_map12.emblem_puzzle_active = True
        q4_map12.init_addition_puzzle()
        q4_map12.sync_ui_state()

        # Click pause button
        q4_map12.trigger_click(q4_map12.pause_menu.pause_btn_rect.center)
        self.assertTrue(q4_map12.pause_menu.is_paused, "Pause button must work during Addition puzzle on Map 12!")

        # Resume
        q4_map12.trigger_click(q4_map12.pause_menu.resume_rect.center)
        self.assertFalse(q4_map12.pause_menu.is_paused)
        self.assertTrue(q4_map12.emblem_puzzle_active)

    def test_08_pause_menu_works_during_lotus_raft_sailing(self):
        """When player is sailing on the Lotus Raft down the canal, pause menu must work."""
        q4_map12 = Quarter4(self.screen, self.mm, "map12.txt")
        q4_map12.instruction_modal.hide()
        q4_map12.raft_state = "sailing"
        q4_map12.player_on_raft = True

        # Press P to pause
        p_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
        q4_map12.handle_event(p_event)
        self.assertTrue(q4_map12.pause_menu.is_paused, "Must be able to pause while sailing on Lotus Raft!")

    def test_09_pause_menu_works_during_time_up_dialog(self):
        """When stage timer expires and Time's Up dialog is active, pause menu must still work."""
        self.q4.instruction_modal.hide()
        self.q4.time_up_dialog_active = True

        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.q4.handle_event(esc_event)
        self.assertTrue(self.q4.pause_menu.is_paused, "Must be able to pause when Time's Up dialog is shown!")

    def test_10_stage_timer_freezes_while_paused(self):
        """The 10-minute stage timer must strictly freeze while paused."""
        self.q4.instruction_modal.hide()
        initial_time = self.q4.stage_time_remaining
        self.q4.pause_menu.open()

        # Run several updates while paused
        for _ in range(10):
            self.q4.update()

        self.assertEqual(self.q4.stage_time_remaining, initial_time, "Stage timer must NOT decrement while paused!")

        # Unpause and run update -> Timer resumes
        self.q4.pause_menu.close()
        self.q4.update()
        self.assertLess(self.q4.stage_time_remaining, initial_time, "Stage timer must resume after unpausing!")

    def test_11_restart_level_callback(self):
        """Clicking Restart Level cleanly reloads the Quarter 4 level."""
        self.q4.instruction_modal.hide()
        self.q4.pause_menu.open()

        restart_pos = self.q4.pause_menu.restart_rect.center
        self.q4.trigger_click(restart_pos)

        # Main menu's quarter4 should now be a fresh instance
        self.assertIsNotNone(self.mm.quarter4)
        self.assertFalse(self.mm.quarter4.pause_menu.is_paused)

    def test_12_return_to_stage_select_callback(self):
        """Clicking Return to Stage Select exits cleanly to stage select."""
        self.q4.instruction_modal.hide()
        self.q4.pause_menu.open()

        exit_pos = self.q4.pause_menu.exit_rect.center
        self.q4.trigger_click(exit_pos)

        self.assertEqual(self.mm.current_screen, "stage_select")
        self.assertIsNone(self.mm.quarter4)

    def test_13_audio_settings_button(self):
        """Clicking Audio Settings opens the audio popup modal."""
        self.q4.instruction_modal.hide()
        self.q4.pause_menu.open()

        audio_pos = self.q4.pause_menu.audio_rect.center
        self.q4.trigger_click(audio_pos)

        self.assertEqual(self.mm.popup_state, "audio_settings")

    def test_14_controls_guide_sub_modal(self):
        """Clicking Controls Guide displays controls guide and back button returns to pause menu."""
        self.q4.instruction_modal.hide()
        self.q4.pause_menu.open()
        self.assertFalse(self.q4.pause_menu.showing_controls)

        # Click Controls Guide
        controls_pos = self.q4.pause_menu.controls_rect.center
        self.q4.trigger_click(controls_pos)
        self.assertTrue(self.q4.pause_menu.showing_controls)

        # Click Back button
        back_pos = self.q4.pause_menu.guide_back_rect.center
        self.q4.trigger_click(back_pos)
        self.assertFalse(self.q4.pause_menu.showing_controls)
        self.assertTrue(self.q4.pause_menu.is_paused)

    def test_15_pause_menu_draws_button_and_modal_without_crash(self):
        """Drawing pause button and modal executes cleanly without crashes."""
        # Unpaused: Draws button
        self.q4.draw()

        # Paused: Draws modal on top
        self.q4.pause_menu.open()
        self.q4.draw()


if __name__ == "__main__":
    unittest.main()
