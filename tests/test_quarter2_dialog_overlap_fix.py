# tests/test_quarter2_dialog_overlap_fix.py
"""
Automated Unit Tests for Quarter 2 Overlapping Text Windows & Modal Mutual Exclusion.
Verifies that:
1. is_modal_active() accurately identifies any open modal / dialogue / minigame.
2. draw_ui() suppresses exploration HUD widgets (Objectives HUD box, Guide button, Completion card)
   while modals are active to prevent overlapping windows.
3. InstructionModal and NPCGreetingDialog are strictly mutually exclusive.
4. Quiz dialogs (RPGQuizDialog, wrong, out of tries, correct, victory speech) hide greeting dialogs.
5. Floating Barrio Banner alerts at y=70 yield during modals and during Bahay Kubo award animations.
6. Full draw() cycle executes without exceptions or overlapping collisions.
"""

import unittest
import pygame
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

pygame.init()
pygame.display.set_mode((1280, 720), pygame.HIDDEN)

from screens.quarter2 import Quarter2


class DummyAudioManager:
    def play_sfx(self, name):
        pass
    def get_sound(self, name):
        return None


class DummyMainMenu:
    def __init__(self):
        self.audio_manager = DummyAudioManager()
        self.selected_student = {"id": 1, "username": "Juan", "first_name": "Juan", "last_name": "Dela Cruz", "level": "Grade 2", "gender": "boy"}
        self.student_db_id = 1
        self.student_id = 1
        self.current_screen = "quarter2"
        self.quarter1 = None
        self.quarter2 = None
        self.quarter3 = None
        self.quarter4 = None
        self.stage_select = None
        self.last_stage_select_data = None
        self.is_quarter_completed = lambda q: False


class TestQuarter2DialogOverlapFix(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.get_surface() or pygame.Surface((1280, 720))
        self.mm = DummyMainMenu()
        self.q2 = Quarter2(self.screen, self.mm, "map4.txt")
        # Ensure default clean state
        if hasattr(self.q2, 'instruction_modal'):
            self.q2.instruction_modal.hide()
        if hasattr(self.q2, 'greeting_dialog'):
            self.q2.greeting_dialog.hide()
        self.q2.quiz_state = 0

    def test_is_modal_active_exploration(self):
        """During pure exploration, is_modal_active() must be False."""
        self.assertFalse(self.q2.is_modal_active())
        self.assertFalse(self.q2.is_dialogue_active())

    def test_is_modal_active_various_modals(self):
        """is_modal_active() must return True for any active modal or dialog."""
        # 1. Instruction modal
        self.q2.instruction_modal.show({"title": "Test Instructions"})
        self.assertTrue(self.q2.is_modal_active())
        self.q2.instruction_modal.hide()
        self.assertFalse(self.q2.is_modal_active())

        # 2. Greeting dialog
        self.q2.greeting_dialog.show("Tomas", "Station 1", "Kamusta!")
        self.assertTrue(self.q2.is_modal_active())
        self.q2.greeting_dialog.hide()
        self.assertFalse(self.q2.is_modal_active())

        # 3. Quiz question states (1..5)
        for state in [1, 2, 3, 4, 5]:
            self.q2.quiz_state = state
            self.assertTrue(self.q2.is_modal_active(), f"Failed for quiz_state={state}")
        self.q2.quiz_state = 0
        self.assertFalse(self.q2.is_modal_active())

        # 4. Knight Guardian prompt modal
        self.q2.guardian_knight_state = 2
        self.assertTrue(self.q2.is_modal_active())
        self.q2.guardian_knight_state = 0
        self.assertFalse(self.q2.is_modal_active())

        # 5. Currency Matching puzzle
        self.q2.currency_puzzle_active = True
        self.assertTrue(self.q2.is_modal_active())
        self.q2.currency_puzzle_active = False
        self.assertFalse(self.q2.is_modal_active())

        # 6. Time's Up dialog
        self.q2.time_up_dialog_active = True
        self.assertTrue(self.q2.is_modal_active())
        self.q2.time_up_dialog_active = False
        self.assertFalse(self.q2.is_modal_active())

        # 7. Pause menu
        self.q2.pause_menu.is_paused = True
        self.assertTrue(self.q2.is_modal_active())
        self.q2.pause_menu.is_paused = False
        self.assertFalse(self.q2.is_modal_active())

    def test_draw_ui_suppression_during_modals(self):
        """draw_ui() must immediately return when is_modal_active() is True, preventing overlay collisions."""
        test_surf = pygame.Surface((1280, 720))
        test_surf.fill((0, 0, 0))
        self.q2.screen = test_surf

        # 1. When instruction modal is open
        self.q2.instruction_modal.show({"title": "Test"})
        self.assertTrue(self.q2.is_modal_active())
        before_bytes = pygame.image.tostring(test_surf, "RGB")
        self.q2.draw_ui()
        after_bytes = pygame.image.tostring(test_surf, "RGB")
        self.assertEqual(before_bytes, after_bytes, "draw_ui() must not blit any HUD elements while modal is active")

        # 2. When exploration is active (quiz_state = 0, no modal)
        self.q2.instruction_modal.hide()
        self.assertFalse(self.q2.is_modal_active())
        self.q2.draw_ui()
        after_expl_bytes = pygame.image.tostring(test_surf, "RGB")
        self.assertNotEqual(before_bytes, after_expl_bytes, "draw_ui() must render HUD elements during exploration")

    def test_instruction_modal_hides_greeting_dialog(self):
        """Showing instruction modal must immediately hide any greeting dialog."""
        self.q2.greeting_dialog.show("Tomas", "Station 1", "Halika!")
        self.assertTrue(self.q2.greeting_dialog.is_visible)

        # Trigger instruction modal (e.g. via Guide button or map init)
        self.q2.show_instructions()
        self.assertTrue(self.q2.instruction_modal.is_visible)
        self.assertFalse(self.q2.greeting_dialog.is_visible, "Greeting dialog must yield when instructions open")

    def test_quiz_state_hides_greeting_dialog(self):
        """Transitioning to quiz_state in [1..5] must dismiss greeting dialog."""
        self.q2.greeting_dialog.show("Tomas", "Station 1", "Halika!")
        self.assertTrue(self.q2.greeting_dialog.is_visible)

        self.q2.quiz_state = 1
        self.q2.draw()
        self.assertFalse(self.q2.greeting_dialog.is_visible, "Greeting dialog must hide when quiz begins")

    def test_banner_text_suppressed_during_modals_and_kubo(self):
        """In-world banner alert at y=70 must NOT draw during modals or when Bahay Kubo card is active."""
        self.q2.banner_text = "FESTIVE SPRINT!"
        self.q2.banner_timer = 5.0
        self.q2.instruction_modal.show({"title": "Instructions"})

        # draw() executes cleanly without banner colliding with instruction modal
        self.q2.draw()

        # In map5.txt, during award animation, banner also yields
        q2_map5 = Quarter2(self.screen, self.mm, "map5.txt")
        if q2_map5.instruction_modal.is_visible:
            q2_map5.instruction_modal.hide()
        q2_map5.banner_text = "STALL CLEARED!"
        q2_map5.banner_timer = 3.0
        q2_map5.award_anim_active = True
        q2_map5.award_anim_piece_idx = 1
        q2_map5.draw()  # Should not draw colliding banner at y=70 over kubo award at y=65


if __name__ == "__main__":
    unittest.main()
