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
from screens.tutorial import TutorialScreen
from unittest.mock import patch
from db.connect_db import Database

MOCK_TEST_QUESTIONS = [
    {
        "prompt": f"Mock Test Question {i}",
        "optionA": "Choice A",
        "optionB": "Choice B",
        "optionC": "Choice C",
        "optionD": "Choice D",
        "correctAnswer": "A",
        "hint": "Hint"
    }
    for i in range(1, 7)
]


class TestTwoTriesQuizLimit(unittest.TestCase):
    def setUp(self):
        self.q_patch = patch.object(Database, "get_questions", return_value=MOCK_TEST_QUESTIONS)
        self.q_patch.start()
        self.mm = MainMenu(screen)
        self.mm.selected_student = {
            "id": 1,
            "student_id": "1",
            "first_name": "TestStudent",
            "last_name": "Tester",
            "score": 0,
            "progress": 0,
            "level": "Grade 2",
            "gender": "female"
        }

    def tearDown(self):
        self.q_patch.stop()

    def test_quarter1_two_tries_limit(self):
        q1 = Quarter1(screen, self.mm, "map1.txt")
        self.mm.quarter1 = q1
        if hasattr(q1, 'instruction_modal') and q1.instruction_modal.is_visible:
            q1.instruction_modal.hide()

        q1.quiz_station_index = 1
        q1.active_shape_id = 1
        q1.current_question_index = 0
        q1.quiz_state = 1
        q1.question_attempts[1] = 0

        # Retrieve questions for station 1
        q_idx = max(0, min(q1.current_question_index, len(q1.quiz_questions) - 1)) if q1.quiz_questions else 0
        q_data = q1.quiz_questions[q_idx] if q1.quiz_questions else {"question": "", "choices": [], "correct": 0}
        correct_idx = q_data.get("correct", 0)
        wrong_idx = 1 if correct_idx == 0 else 0

        # 1st wrong attempt via QuizDialog button rect
        btn_rect = q1.quiz_dialog.get_button_rect(wrong_idx)
        q1.trigger_click(btn_rect.center)

        self.assertEqual(q1.quiz_state, 2, "1st wrong answer should set quiz_state to 2 (1 try remaining)")
        self.assertIn(wrong_idx, q1.eliminated_choices, "Selected wrong choice must be eliminated")

        # Click Try Again button
        q1.draw_wrong_dialog()
        box_w, box_h = 740, 350
        box_x = (q1.width - box_w) // 2
        box_y = (q1.height - box_h) // 2
        retry_btn = pygame.Rect(box_x + (box_w - 240) // 2, box_y + 275, 240, 50)
        q1.trigger_click(retry_btn.center)
        self.assertEqual(q1.quiz_state, 1, "Clicking Try Again should return to quiz question (quiz_state = 1)")

        # 2nd wrong attempt
        other_wrong_idx = [i for i in range(4) if i != correct_idx and i != wrong_idx][0]
        btn_rect2 = q1.quiz_dialog.get_button_rect(other_wrong_idx)
        q1.trigger_click(btn_rect2.center)

        self.assertEqual(q1.quiz_state, 4, "2nd wrong answer should set quiz_state to 4 (Out of tries)")
        self.assertFalse(q1.first_attempt_correct[1], "Station 1 must be recorded as wrong")

        # Dismiss out-of-tries dialog -> marks answered and advances without requiring retry!
        q1.draw_out_of_tries_dialog()
        self.assertIsNotNone(q1.out_of_tries_btn_rect)
        q1.trigger_click(q1.out_of_tries_btn_rect.center)
        self.assertEqual(q1.quiz_state, 0, "Closing out of tries dialog should return to exploration (quiz_state = 0)")
        self.assertTrue(q1.shape_npcs[1]['answered'], "Shape station must be marked answered on 2 wrong answers")
        self.assertEqual(q1.quiz_station_index, 2, "quiz_station_index must advance to 2 without requiring retry")

    def test_quarter2_two_tries_limit(self):
        q2 = Quarter2(screen, self.mm, "map5.txt")
        self.mm.quarter2 = q2
        if hasattr(q2, 'instruction_modal') and q2.instruction_modal.is_visible:
            q2.instruction_modal.hide()

        q2.quiz_station_index = 1
        q2.current_question_index = 0
        q2.quiz_state = 1
        q2.station_attempts[1] = 0

        q_idx = max(0, min(q2.current_question_index, len(q2.quiz_questions) - 1)) if q2.quiz_questions else 0
        q_data = q2.quiz_questions[q_idx] if q2.quiz_questions else {"question": "", "choices": [], "correct": 0}
        correct_idx = q_data.get("correct", 0)
        wrong_idx = 1 if correct_idx == 0 else 0

        btn_rect = q2.quiz_dialog.get_button_rect(wrong_idx)
        q2.trigger_click(btn_rect.center)

        self.assertEqual(q2.quiz_state, 2, "Q2 1st wrong answer sets quiz_state to 2")
        self.assertIn(wrong_idx, q2.eliminated_choices)

        # Retry
        q2.draw_wrong_dialog()
        q2.trigger_click(q2.wrong_btn_rect.center)
        self.assertEqual(q2.quiz_state, 1)

        # 2nd wrong answer
        other_wrong_idx = [i for i in range(4) if i != correct_idx and i != wrong_idx][0]
        btn_rect2 = q2.quiz_dialog.get_button_rect(other_wrong_idx)
        q2.trigger_click(btn_rect2.center)

        self.assertEqual(q2.quiz_state, 4, "Q2 2nd wrong answer sets quiz_state to 4")
        self.assertFalse(q2.first_attempt_correct[1], "Station 1 must be recorded as wrong")

        # Dismiss out-of-tries dialog -> advances to station 2 without requiring retry!
        q2.draw_out_of_tries_dialog()
        q2.trigger_click(q2.out_of_tries_btn_rect.center)
        self.assertEqual(q2.quiz_state, 0)
        self.assertEqual(q2.quiz_station_index, 2, "quiz_station_index must advance to 2 without requiring retry")

    def test_quarter3_two_tries_limit(self):
        q3 = Quarter3(screen, self.mm, "map9.txt")
        self.mm.quarter3 = q3
        if hasattr(q3, 'instruction_modal') and q3.instruction_modal.is_visible:
            q3.instruction_modal.hide()

        q3.quiz_station_index = 1
        q3.current_question_index = 0
        q3.quiz_state = 1
        q3.station_attempts[1] = 0

        q_idx = max(0, min(q3.current_question_index, len(q3.quiz_questions) - 1)) if q3.quiz_questions else 0
        q_data = q3.quiz_questions[q_idx] if q3.quiz_questions else {"question": "", "choices": [], "correct": 0}
        correct_idx = q_data.get("correct", 0)
        wrong_idx = 1 if correct_idx == 0 else 0

        btn_rect = q3.quiz_dialog.get_button_rect(wrong_idx)
        q3.trigger_click(btn_rect.center)

        self.assertEqual(q3.quiz_state, 2, "Q3 1st wrong answer sets quiz_state to 2")

        # Retry
        q3.draw_wrong_dialog()
        q3.trigger_click(q3.wrong_btn_rect.center)
        self.assertEqual(q3.quiz_state, 1)

        # 2nd wrong answer
        other_wrong_idx = [i for i in range(4) if i != correct_idx and i != wrong_idx][0]
        btn_rect2 = q3.quiz_dialog.get_button_rect(other_wrong_idx)
        q3.trigger_click(btn_rect2.center)

        self.assertEqual(q3.quiz_state, 4, "Q3 2nd wrong answer sets quiz_state to 4")
        self.assertFalse(q3.first_attempt_correct[1], "Station 1 must be recorded as wrong")

        # Dismiss out-of-tries dialog -> advances to station 2 without requiring retry!
        q3.draw_out_of_tries_dialog()
        q3.trigger_click(q3.out_of_tries_btn_rect.center)
        self.assertEqual(q3.quiz_state, 0)
        self.assertEqual(q3.quiz_station_index, 2, "quiz_station_index must advance to 2 without requiring retry")

    def test_quarter4_two_tries_limit(self):
        q4 = Quarter4(screen, self.mm, "map12.txt")
        self.mm.quarter4 = q4
        if hasattr(q4, 'instruction_modal') and q4.instruction_modal.is_visible:
            q4.instruction_modal.hide()

        q4.quiz_station_index = 1
        q4.current_question_index = 0
        q4.quiz_state = 1
        q4.station_attempts[1] = 0

        q_idx = max(0, min(q4.current_question_index, len(q4.quiz_questions) - 1)) if q4.quiz_questions else 0
        q_data = q4.quiz_questions[q_idx] if q4.quiz_questions else {"question": "", "choices": [], "correct": 0}
        correct_idx = q_data.get("correct", 0)
        wrong_idx = 1 if correct_idx == 0 else 0

        btn_rect = q4.quiz_dialog.get_button_rect(wrong_idx)
        q4.trigger_click(btn_rect.center)

        self.assertEqual(q4.quiz_state, 2, "Q4 1st wrong answer sets quiz_state to 2")

        # Retry
        q4.draw_wrong_dialog()
        q4.trigger_click(q4.wrong_btn_rect.center)
        self.assertEqual(q4.quiz_state, 1)

        # 2nd wrong answer
        other_wrong_idx = [i for i in range(4) if i != correct_idx and i != wrong_idx][0]
        btn_rect2 = q4.quiz_dialog.get_button_rect(other_wrong_idx)
        q4.trigger_click(btn_rect2.center)

        self.assertEqual(q4.quiz_state, 4, "Q4 2nd wrong answer sets quiz_state to 4")
        self.assertFalse(q4.first_attempt_correct[1], "Station 1 must be recorded as wrong")

        # Dismiss out-of-tries dialog -> advances to station 2 and marks answered without requiring retry!
        q4.draw_out_of_tries_dialog()
        q4.trigger_click(q4.out_of_tries_btn_rect.center)
        self.assertEqual(q4.quiz_state, 0)
        self.assertEqual(q4.quiz_station_index, 2, "quiz_station_index must advance to 2 without requiring retry")
        self.assertIn(1, q4.answered_stations, "Station 1 must be marked answered without requiring retry")

    def test_tutorial_two_tries_limit(self):
        tut = TutorialScreen(screen, self.mm)
        tut.intro_anim_active = False
        tut.intro_dialog_open = False
        tut.demo_video_active = False

        tut.phase = 3
        tut.quiz_state = 1
        tut.quiz_attempts = 0
        tut.eliminated_choice = None

        # Correct answer is 1 (Option B: "4")
        # 1st wrong attempt (Option A, index 0)
        tut.submit_quiz_answer(0)
        self.assertEqual(tut.quiz_state, 2, "Tutorial 1st wrong answer sets quiz_state to 2")
        self.assertEqual(tut.quiz_attempts, 1)
        self.assertEqual(tut.eliminated_choice, 0)

        # Click Try Again
        box_w, box_h = 740, 340
        box_x = (tut.width - box_w) // 2
        box_y = (tut.height - box_h) // 2
        btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 250, 260, 52)
        tut.trigger_click(btn_rect.center)
        self.assertEqual(tut.quiz_state, 1, "Clicking Try Again returns to quiz_state 1")

        # 2nd wrong attempt (Option C, index 2)
        tut.submit_quiz_answer(2)
        self.assertEqual(tut.quiz_state, 4, "Tutorial 2nd wrong answer sets quiz_state to 4")

        # Dismiss out-of-tries dialog -> unlocks portal (phase 4) without requiring retry!
        tut.draw_sample_out_of_tries_dialog()
        self.assertIsNotNone(tut.out_of_tries_btn_rect)
        tut.trigger_click(tut.out_of_tries_btn_rect.center)
        self.assertEqual(tut.quiz_state, 0, "Closing out of tries dialog sets quiz_state to 0")
        self.assertEqual(tut.phase, 4, "Phase must advance to 4 (portal unlocked) without requiring retry")


if __name__ == "__main__":
    unittest.main()
