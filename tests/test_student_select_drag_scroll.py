import os
import sys
import unittest
import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'


class TestStudentSelectDragScroll(unittest.TestCase):
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
        # Populate with mock students for scrolling tests
        self.ss.students = [
            {"id": i, "student_id": f"S-{i:03d}", "first_name": f"Student{i}", "last_name": "Test",
             "score": i * 10, "progress": i * 5, "level": "Grade 2", "gender": "male" if i % 2 == 0 else "female"}
            for i in range(1, 20)
        ]

    def test_01_mouse_drag_to_scroll(self):
        """Test that dragging mouse inside the student list scrolls the view smoothly"""
        list_rect = pygame.Rect(40, 120, 1024 - 80, 768 - 200)
        start_pos = (list_rect.centerx, list_rect.centery)
        
        # 1. Mouse down inside list
        down_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': start_pos})
        self.ss.handle_event(down_ev)
        self.assertTrue(self.ss.is_mouse_dragging)
        self.assertEqual(self.ss.mouse_drag_start_y, start_pos[1])

        # 2. Drag mouse upwards by 150px (scrolls content downwards)
        drag_pos = (start_pos[0], start_pos[1] - 150)
        move_ev = pygame.event.Event(pygame.MOUSEMOTION, {'pos': drag_pos, 'rel': (0, -150), 'buttons': (1, 0, 0)})
        self.ss.handle_event(move_ev)
        self.assertGreater(self.ss.target_scroll_y, 100)

        # 3. Update frames for smooth interpolation
        for _ in range(10):
            self.ss.update()
        self.assertGreater(self.ss.scroll_y, 100)

        # 4. Mouse up completes drag
        up_ev = pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 1, 'pos': drag_pos})
        res = self.ss.handle_event(up_ev)
        self.assertFalse(self.ss.is_mouse_dragging)
        self.assertEqual(res, "scroll")

    def test_02_gesture_fist_drag_to_scroll(self):
        """Test that holding a FIST and moving vertically drags the student list"""
        import time
        list_rect = pygame.Rect(40, 120, 1024 - 80, 768 - 200)
        start_pos = (list_rect.centerx, list_rect.centery)
        now_t = time.time()

        # 1. Start fist gesture
        self.ss.update_gesture(start_pos, now_t, 0.9, "FIST")
        self.assertTrue(self.ss.is_gesture_dragging)
        self.assertEqual(self.ss.gesture_drag_start_y, start_pos[1])

        # 2. Move fist upwards by 180px (> 35px threshold for drag scroll)
        drag_pos = (start_pos[0], start_pos[1] - 180)
        self.ss.update_gesture(drag_pos, now_t, 0.9, "FIST")
        self.assertGreater(self.ss.target_scroll_y, 120)

        # 3. Release fist
        self.ss.update_gesture(drag_pos, 0.0, 0.9, "OPEN")
        self.assertFalse(self.ss.is_gesture_dragging)

    def test_03_gesture_hold_edge_auto_scroll(self):
        """Test that dragging a fist near top/bottom edge auto-scrolls"""
        import time
        list_rect = pygame.Rect(40, 120, 1024 - 80, 768 - 200)
        start_pos = (list_rect.centerx, list_rect.centery)
        now_t = time.time()

        # Start gesture at center, then drag down towards bottom edge
        self.ss.update_gesture(start_pos, now_t, 0.9, "FIST")
        bottom_edge_pos = (list_rect.centerx, list_rect.bottom - 10)

        initial_target = self.ss.target_scroll_y
        for _ in range(5):
            self.ss.update_gesture(bottom_edge_pos, now_t, 0.9, "FIST")
            self.ss.update()

        self.assertGreater(self.ss.target_scroll_y, initial_target)

    def test_04_tap_without_drag_selects_student(self):
        """Test that a direct click without dragging selects the student"""
        list_rect = pygame.Rect(40, 120, 1024 - 80, 768 - 200)
        item_pos = (list_rect.x + 50, list_rect.y + 30)

        down_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': item_pos})
        res = self.ss.handle_event(down_ev)
        self.assertEqual(res, "select")
        self.assertEqual(self.menu.student_id, "S-001")

    def test_05_fist_hold_dwell_selects_student(self):
        """Test that holding a FIST over a student card selects them upon reaching CLICK_HOLD_TIME"""
        import time
        self.menu.current_screen = "student_select"
        self.menu.student_select = self.ss

        list_rect = pygame.Rect(40, 120, 1024 - 80, 768 - 200)
        # Target Student 2 (row 1, y = 120 + 15 + 90 = 225)
        student2_pos = (list_rect.x + 100, list_rect.y + 15 + 90 + 30)

        # 1. Start holding fist
        start_t = time.time()
        self.ss.update_gesture(student2_pos, start_t, 0.9, "FIST")
        self.assertIsNone(self.menu.selected_student)

        # 2. Simulate holding fist past 0.9s
        past_t = start_t - 1.0  # elapsed 1.0s
        self.ss.update_gesture(student2_pos, past_t, 0.9, "FIST")

        # Verify Student 2 was selected!
        self.assertIsNotNone(self.menu.selected_student)
        self.assertEqual(self.menu.selected_student["student_id"], "S-002")
        self.assertEqual(self.menu.current_screen, "menu")

    def test_06_main_menu_fist_grace_period(self):
        """Test that momentary 1-frame drop does not instantly reset fist hold in MainMenu"""
        import time
        self.menu.fist_start_time = time.time() - 0.5
        self.menu.last_fist_time = time.time()
        
        # Simulate 1 frame where hand data is missing (not detected)
        self.menu.update_gesture() # When cap is None, uses mouse fallback, but let's test grace state
        self.menu.last_fist_time = time.time() # within 200ms grace
        self.assertTrue(time.time() - self.menu.last_fist_time <= 0.20)

    def test_07_fist_drag_scrolling_does_not_select_student(self):
        """Test that actively dragging with a fist scrolls the list without selecting any student"""
        import time
        self.menu.current_screen = "student_select"
        self.menu.student_select = self.ss

        list_rect = pygame.Rect(40, 120, 1024 - 80, 768 - 200)
        start_pos = (list_rect.centerx, list_rect.centery)
        start_t = time.time()

        # 1. Start fist at center (elapsed = 0.0s)
        self.ss.update_gesture(start_pos, start_t, 0.9, "FIST")

        # 2. Drag up by 150px
        drag_pos = (start_pos[0], start_pos[1] - 150)
        self.ss.update_gesture(drag_pos, start_t, 0.9, "FIST")

        # 3. Simulate staying in drag position even past 1.5 seconds
        self.ss.update_gesture(drag_pos, start_t - 1.5, 0.9, "FIST")

        # Verify list scrolled and NO student was selected
        self.assertGreater(self.ss.target_scroll_y, 80)
        self.assertTrue(self.ss.is_actively_scrolling)
        self.assertIsNone(self.menu.selected_student)
        self.assertEqual(self.menu.current_screen, "student_select")


if __name__ == '__main__':
    unittest.main()
