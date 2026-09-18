import os
import unittest
import pygame

# Headless video driver
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

class TestMainMenuStudentDisplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        from screens.main_menu import MainMenu
        self.menu = MainMenu(self.screen)
        self.menu.dialogue_active = False

    def test_no_student_no_card(self):
        """Verify no extra student button/card is displayed when no student is selected"""
        self.menu.selected_student = None
        self.menu.student_id = None
        self.menu.setup_buttons()
        self.menu.draw()

        # Should only display current selected student; when none selected, no extra card/button
        self.assertIsNone(self.menu.student_card_rect)
        self.assertEqual(self.menu.select_student_btn.text, "SELECT STUDENT")

    def test_selected_student_profile_card(self):
        """Verify profile card renders cleanly when a student is selected"""
        self.menu.selected_student = {
            "id": 1,
            "student_id": "2024-001",
            "first_name": "Jessuny",
            "last_name": "Dado",
            "score": 250,
            "progress": 75,
            "level": "Grade 2",
            "gender": "male"
        }
        self.menu.student_id = "2024-001"
        self.menu.setup_buttons()
        self.menu.draw()

        self.assertIsNotNone(self.menu.student_card_rect)
        self.assertEqual(self.menu.select_student_btn.text, "CHANGE STUDENT")

    def test_student_card_is_display_only_not_button(self):
        """Verify the student profile card is display-only and does not act as another button"""
        self.menu.selected_student = {
            "id": 1,
            "student_id": "2024-001",
            "first_name": "Jessuny",
            "last_name": "Dado",
            "score": 100,
            "progress": 25,
            "level": "Grade 2",
            "gender": "female"
        }
        self.menu.student_id = "2024-001"
        self.menu.setup_buttons()
        self.menu.draw()

        card_center = self.menu.student_card_rect.center
        self.menu.trigger_click(card_center)
        # Clicking the card should NOT trigger student_select
        self.assertEqual(self.menu.current_screen, "menu")

    def test_buttons_are_centered(self):
        """Verify that buttons are placed in the center of the screen"""
        # Test without save (3 buttons)
        self.menu.selected_student = None
        self.menu.student_id = None
        self.menu.setup_buttons()
        
        bh = 58
        gap = 14
        total_h_3 = (bh * 3) + (gap * 2)
        expected_start_y_3 = (self.menu.h // 2) - (total_h_3 // 2)
        self.assertEqual(self.menu.select_student_btn.rect.y, expected_start_y_3)
        self.assertEqual(self.menu.select_student_btn.rect.x, self.menu.w // 2 - 440 // 2)

    def test_student_card_position_centered_between_title_and_buttons(self):
        """Verify the selected student details box is positioned in the exact middle of the Cognitive Maze title and the Buttons"""
        self.menu.selected_student = {
            "id": 1,
            "student_id": "2024-001",
            "first_name": "Jessuny",
            "last_name": "Dado",
            "score": 100,
            "progress": 25,
            "level": "Grade 2",
            "gender": "male"
        }
        self.menu.student_id = "2024-001"
        self.menu.setup_buttons()
        self.menu.draw()

        title_h = self.menu.title_font.size("COGNITIVE MAZE")[1]
        title_bottom = self.menu.title_y + title_h + 4
        buttons_top = self.menu.select_student_btn.rect.top

        card_rect = self.menu.student_card_rect
        self.assertIsNotNone(card_rect)

        gap_above = card_rect.top - title_bottom
        gap_below = buttons_top - card_rect.bottom

        # Verify the gaps above and below differ by at most 1px (due to integer division)
        self.assertLessEqual(abs(gap_above - gap_below), 1)
        self.assertGreaterEqual(gap_above, 10)
        self.assertGreaterEqual(gap_below, 10)

if __name__ == '__main__':
    unittest.main()
