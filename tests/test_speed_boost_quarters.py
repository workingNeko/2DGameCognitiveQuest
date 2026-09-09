# tests/test_speed_boost_quarters.py
import os
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.main_menu import MainMenu
from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4

class TestSpeedBoostQuarters(unittest.TestCase):
    def setUp(self):
        self.screen = screen
        self.mm = MainMenu(self.screen)
        self.mm.student_id = "1"
        self.mm.selected_student = {"id": 1, "student_id": "1", "first_name": "SpeedTester"}

    def test_quarter1_speed_boost(self):
        """Verify Quarter 1 grants 3.0s speed boost on question clearance and updates correctly."""
        q1 = Quarter1(self.screen, self.mm, "map1.txt")
        if hasattr(q1, 'instruction_modal'):
            q1.instruction_modal.hide()

        self.assertEqual(q1.speed_boost_timer, 0.0)

        # State 3: Correct answer transition click
        q1.active_shape_id = 1
        q1.quiz_state = 3
        box_w, box_h = 500, 240
        box_x = (q1.width - box_w) // 2
        box_y = (q1.height - box_h) // 2
        btn_center = (box_x + box_w // 2, box_y + 140 + 21)

        q1.trigger_click(btn_center)
        self.assertEqual(q1.speed_boost_timer, 3.0, "Quarter 1 state 3 click should set speed_boost_timer to 3.0")
        self.assertEqual(q1.quiz_state, 0, "Quarter 1 should return to exploration state 0")

        # Verify timer decrements in state 0 when player has control (camera pan done)
        q1.camera_pan_active = False
        q1.speed_boost_timer = 3.0
        class MockClock:
            def tick(self, fps):
                return 500  # 0.5s
        q1.clock = MockClock()
        q1.update()
        self.assertAlmostEqual(q1.speed_boost_timer, 2.5, places=2)

        # Verify State 4: Out of tries reveal click also gives 3.0s boost
        q1.active_shape_id = 1
        q1.quiz_state = 4
        box_w, box_h = 560, 260
        box_x = (q1.width - box_w) // 2
        box_y = (q1.height - box_h) // 2
        btn_center4 = (box_x + box_w // 2, box_y + 195 + 21)
        q1.trigger_click(btn_center4)
        self.assertEqual(q1.speed_boost_timer, 3.0, "Quarter 1 state 4 click should set speed_boost_timer to 3.0")

    def test_quarter2_speed_boost(self):
        """Verify Quarter 2 grants 3.0s speed boost on question clearance."""
        q2 = Quarter2(self.screen, self.mm, "map4.txt")
        if hasattr(q2, 'instruction_modal'):
            q2.instruction_modal.hide()

        self.assertEqual(q2.speed_boost_timer, 0.0)

        # State 3: Correct answer transition click
        q2.quiz_state = 3
        box_w, box_h = 540, 260
        box_x = (q2.width - box_w) // 2
        box_y = (q2.height - box_h) // 2
        btn_center = (box_x + box_w // 2, box_y + 175 + 22)

        q2.trigger_click(btn_center)
        self.assertEqual(q2.speed_boost_timer, 3.0, "Quarter 2 state 3 click should set speed_boost_timer to 3.0")
        self.assertEqual(q2.banner_timer, 3.0, "Quarter 2 banner_timer should also be 3.0")

        # State 4: Out of tries reveal click
        q2.quiz_state = 4
        box_w, box_h = 580, 270
        box_x = (q2.width - box_w) // 2
        box_y = (q2.height - box_h) // 2
        btn_center4 = (box_x + box_w // 2, box_y + 190 + 22)

        q2.trigger_click(btn_center4)
        self.assertEqual(q2.speed_boost_timer, 3.0, "Quarter 2 state 4 click should set speed_boost_timer to 3.0")
        self.assertEqual(q2.banner_timer, 3.0)

    def test_quarter3_speed_boost(self):
        """Verify Quarter 3 grants 3.0s speed boost on advancing station progress across maps."""
        # Map 7
        q3_map7 = Quarter3(self.screen, self.mm, "map7.txt")
        if hasattr(q3_map7, 'instruction_modal'):
            q3_map7.instruction_modal.hide()
        q3_map7.advance_station_progress()
        self.assertEqual(q3_map7.speed_boost_timer, 3.0, "Quarter 3 Map 7 should set speed_boost_timer to 3.0")

        # Map 8
        q3_map8 = Quarter3(self.screen, self.mm, "map8.txt")
        if hasattr(q3_map8, 'instruction_modal'):
            q3_map8.instruction_modal.hide()
        q3_map8.advance_station_progress()
        self.assertEqual(q3_map8.speed_boost_timer, 3.0, "Quarter 3 Map 8 should set speed_boost_timer to 3.0")

        # Map 9
        q3_map9 = Quarter3(self.screen, self.mm, "map9.txt")
        if hasattr(q3_map9, 'instruction_modal'):
            q3_map9.instruction_modal.hide()
        q3_map9.advance_station_progress()
        self.assertEqual(q3_map9.speed_boost_timer, 3.0, "Quarter 3 Map 9 should set speed_boost_timer to 3.0")

    def test_quarter4_speed_boost(self):
        """Verify Quarter 4 grants 3.0s speed boost on question clearance."""
        q4 = Quarter4(self.screen, self.mm, "map10.txt")
        if hasattr(q4, 'instruction_modal'):
            q4.instruction_modal.hide()

        self.assertEqual(q4.speed_boost_timer, 0.0)

        # State 3: Correct answer transition click
        q4.quiz_state = 3
        box_w, box_h = 720, 300
        box_x = (q4.width - box_w) // 2
        box_y = (q4.height - box_h) // 2
        btn_center = (box_x + box_w // 2, box_y + 225 + 23)

        q4.trigger_click(btn_center)
        self.assertEqual(q4.speed_boost_timer, 3.0, "Quarter 4 state 3 click should set speed_boost_timer to 3.0")
        self.assertEqual(q4.quiz_state, 0, "Quarter 4 should return to exploration state 0")

        # State 4: Out of tries reveal click
        q4.quiz_state = 4
        box_w, box_h = 720, 310
        box_x = (q4.width - box_w) // 2
        box_y = (q4.height - box_h) // 2
        btn_center4 = (box_x + box_w // 2, box_y + 240 + 23)

        q4.trigger_click(btn_center4)
        self.assertEqual(q4.speed_boost_timer, 3.0, "Quarter 4 state 4 click should set speed_boost_timer to 3.0")

if __name__ == "__main__":
    unittest.main()
