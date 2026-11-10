import os
import sys
import unittest
import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'


class TestStudentSelectFilterSort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1024, 768))
        from screens.main_menu import MainMenu
        cls.menu = MainMenu(cls.screen)

    def setUp(self):
        from screens.studentselect import StudentSelect
        self.menu.selected_student = None
        self.menu.student_id = None
        self.menu.current_screen = "student_select"
        self.ss = StudentSelect(self.screen, self.menu)
        self.menu.student_select = self.ss

        # Predictable mock roster for filter & sort tests
        self.test_roster = [
            {"id": 1, "student_id": "S-001", "first_name": "Alice", "last_name": "Wonder", "score": 85, "progress": 50, "level": "Grade 2", "gender": "female", "section": "Rose"},
            {"id": 2, "student_id": "S-002", "first_name": "Bob", "last_name": "Builder", "score": 40, "progress": 25, "level": "Grade 2", "gender": "male", "section": "Tulip"},
            {"id": 3, "student_id": "S-003", "first_name": "Charlie", "last_name": "Brown", "score": 95, "progress": 90, "level": "Grade 2", "gender": "male", "section": "Daisy"},
            {"id": 4, "student_id": "S-004", "first_name": "Diana", "last_name": "Prince", "score": 70, "progress": 60, "level": "Grade 2", "gender": "female", "section": "Rose"},
            {"id": 5, "student_id": "S-005", "first_name": "Edward", "last_name": "Elric", "score": 90, "progress": 80, "level": "Grade 2", "gender": "male", "section": "Tulip"},
        ]
        self.ss.students = list(self.test_roster)
        self.ss.apply_filter_and_sort()

    def test_01_default_state(self):
        """Test default filter, sort and roster state"""
        self.assertEqual(self.ss.filter_gender, "all")
        self.assertEqual(self.ss.sort_by, "default")
        display = self.ss.get_display_students()
        self.assertEqual(len(display), 5)
        self.assertEqual(display[0]["first_name"], "Alice")

    def test_02_gender_filter_pills(self):
        """Test gender pills for boys and girls"""
        # Filter Boys
        self.ss.filter_gender = "male"
        self.ss.apply_filter_and_sort()
        boys = self.ss.get_display_students()
        self.assertEqual(len(boys), 3)
        for s in boys:
            self.assertEqual(s["gender"], "male")

        # Filter Girls
        self.ss.filter_gender = "female"
        self.ss.apply_filter_and_sort()
        girls = self.ss.get_display_students()
        self.assertEqual(len(girls), 2)
        for s in girls:
            self.assertEqual(s["gender"], "female")

        # Reset to All
        self.ss.filter_gender = "all"
        self.ss.apply_filter_and_sort()
        self.assertEqual(len(self.ss.get_display_students()), 5)

    def test_03_sort_by_name(self):
        """Test alphabetical sort A-Z and Z-A"""
        self.ss.sort_by = "name"
        self.ss.sort_ascending = True
        self.ss.apply_filter_and_sort()
        display = self.ss.get_display_students()
        names = [s["first_name"] for s in display]
        self.assertEqual(names, ["Alice", "Bob", "Charlie", "Diana", "Edward"])

        # Reverse (Z-A)
        self.ss.sort_ascending = False
        self.ss.apply_filter_and_sort()
        display_rev = self.ss.get_display_students()
        names_rev = [s["first_name"] for s in display_rev]
        self.assertEqual(names_rev, ["Edward", "Diana", "Charlie", "Bob", "Alice"])

    def test_04_sort_by_score(self):
        """Test sorting by score descending (high to low) and ascending"""
        self.ss.sort_by = "score"
        self.ss.sort_ascending = False
        self.ss.apply_filter_and_sort()
        display = self.ss.get_display_students()
        scores = [s["score"] for s in display]
        self.assertEqual(scores, [95, 90, 85, 70, 40])
        self.assertEqual(display[0]["first_name"], "Charlie")

        # Ascending (low to high)
        self.ss.sort_ascending = True
        self.ss.apply_filter_and_sort()
        display_asc = self.ss.get_display_students()
        scores_asc = [s["score"] for s in display_asc]
        self.assertEqual(scores_asc, [40, 70, 85, 90, 95])
        self.assertEqual(display_asc[0]["first_name"], "Bob")

    def test_05_click_filter_pills(self):
        """Test clicking interactive UI hitboxes for gender pills"""
        self.ss.draw_filter_sort_bar()

        # Click "Boys" pill
        self.ss.last_click_time = 0
        boys_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.ss.pill_boys_rect.center})
        res = self.ss.handle_event(boys_click)
        self.assertEqual(res, "filter_male")
        self.assertEqual(self.ss.filter_gender, "male")

        # Click "Girls" pill
        self.ss.last_click_time = 0
        girls_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.ss.pill_girls_rect.center})
        res_girls = self.ss.handle_event(girls_click)
        self.assertEqual(res_girls, "filter_female")
        self.assertEqual(self.ss.filter_gender, "female")

        # Click "All" pill
        self.ss.last_click_time = 0
        all_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.ss.pill_all_rect.center})
        res_all = self.ss.handle_event(all_click)
        self.assertEqual(res_all, "filter_all")
        self.assertEqual(self.ss.filter_gender, "all")

    def test_06_click_sort_buttons(self):
        """Test clicking interactive UI hitboxes for sort buttons"""
        self.ss.draw_filter_sort_bar()

        # Click "Name" sort button
        self.ss.last_click_time = 0
        name_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.ss.sort_name_rect.center})
        res_name = self.ss.handle_event(name_click)
        self.assertEqual(res_name, "sort_name")
        self.assertEqual(self.ss.sort_by, "name")
        self.assertTrue(self.ss.sort_ascending)

        # Click "Name" again to toggle Z-A
        self.ss.last_click_time = 0
        res_name2 = self.ss.handle_event(name_click)
        self.assertEqual(res_name2, "sort_name")
        self.assertFalse(self.ss.sort_ascending)

        # Click "Score" sort button (defaults to descending / highest first)
        self.ss.last_click_time = 0
        score_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.ss.sort_score_rect.center})
        res_score = self.ss.handle_event(score_click)
        self.assertEqual(res_score, "sort_score")
        self.assertEqual(self.ss.sort_by, "score")
        self.assertFalse(self.ss.sort_ascending)

    def test_07_keyboard_navigation_and_rendering(self):
        """Test keyboard arrow navigation on filtered and sorted lists"""
        display = self.ss.get_display_students()
        self.assertEqual(self.ss.selected_index, 0)

        # Down arrow
        down_ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN, 'unicode': '', 'mod': 0})
        self.ss.handle_event(down_ev)
        self.assertEqual(self.ss.selected_index, 1)

        # Up arrow
        up_ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP, 'unicode': '', 'mod': 0})
        self.ss.handle_event(up_ev)
        self.assertEqual(self.ss.selected_index, 0)

        # Enter key selects student
        enter_ev = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN, 'unicode': '', 'mod': 0})
        res = self.ss.handle_event(enter_ev)
        self.assertEqual(res, "select")
        self.assertEqual(self.menu.selected_student["first_name"], "Alice")

    def test_08_empty_results_safety(self):
        """Test that an empty roster renders cleanly without crashing"""
        self.ss.students = []
        self.ss.apply_filter_and_sort()
        self.assertEqual(len(self.ss.get_display_students()), 0)

        # Render list when 0 results
        self.ss.draw_filter_sort_bar()
        self.ss.draw_student_list()


if __name__ == '__main__':
    unittest.main()
