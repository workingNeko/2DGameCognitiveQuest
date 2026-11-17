import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))

from db.connect_db import db


class TestSummativeModalAndProgression(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.get_surface()
        self.main_menu = MagicMock()
        self.main_menu.student_id = "2026-001"
        self.main_menu.selected_student = {"student_id": "2026-001", "first_name": "TestStudent"}
        self.main_menu.cursor_pos = (640, 360)
        self.main_menu.current_gesture = "NO HAND"
        self.main_menu.fist_start_time = 0
        self.main_menu.CLICK_HOLD_TIME = 0.9

    @patch("db.save_system.load_student_progress")
    def test_summative_modal_unlocks_and_cards(self, mock_load_progress):
        from screens.stageselect import StageSelect
        
        # Scenario: Teacher uploaded Summatives 1, 2, 3 for Term 1
        # Student completed Summative 1 (t1_s1)
        mock_load_progress.return_value = {
            "completed_summatives": {
                "t1_s1": {"completed": True, "score": 9, "percentage": 90.0, "total_questions": 10}
            },
            "completed_quarters": {}
        }

        with patch.object(db, "get_available_summatives_for_term", return_value=[1, 2, 3]):
            stage_select = StageSelect(self.screen, self.main_menu)
            stage_select.open_summative_modal(1)

            self.assertTrue(stage_select.summative_modal_active)
            self.assertEqual(stage_select.summative_modal_term, 1)
            self.assertEqual(len(stage_select.summative_modal_cards), 4)

            card1 = stage_select.summative_modal_cards[0]
            card2 = stage_select.summative_modal_cards[1]
            card3 = stage_select.summative_modal_cards[2]
            card4 = stage_select.summative_modal_cards[3]

            # Card 1 should be unlocked and completed
            self.assertTrue(card1["unlocked"])
            self.assertTrue(card1["completed"])
            self.assertEqual(card1["score"], 9)

            # Card 2 should be unlocked (because Card 1 is completed) but not yet completed
            self.assertTrue(card2["unlocked"])
            self.assertFalse(card2["completed"])

            # Card 3 should be locked (because Card 2 is not completed)
            self.assertFalse(card3["unlocked"])
            self.assertFalse(card3["completed"])

            # Test barriers_lifted cheat override (Ctrl+Shift+B)
            stage_select.barriers_lifted = True
            stage_select._refresh_summative_modal_data()
            self.assertTrue(all(c["unlocked"] for c in stage_select.summative_modal_cards))

    @patch("db.save_system.load_student_progress")
    def test_assessment_2_locked_before_assessment_1_completed(self, mock_load_progress):
        from screens.stageselect import StageSelect
        
        # Fresh student: nothing completed
        mock_load_progress.return_value = {
            "completed_summatives": {},
            "completed_quarters": {}
        }

        with patch.object(db, "get_available_summatives_for_term", return_value=[1, 2]):
            stage_select = StageSelect(self.screen, self.main_menu)
            stage_select.open_summative_modal(1)

            card1 = stage_select.summative_modal_cards[0]
            card2 = stage_select.summative_modal_cards[1]

            # Assessment 1 is unlocked initially
            self.assertTrue(card1["unlocked"])
            self.assertFalse(card1["completed"])

            # Assessment 2 is LOCKED until Assessment 1 is finished!
            self.assertFalse(card2["unlocked"])
            self.assertFalse(card2["completed"])

            # Clicking locked Assessment 2 does NOT start quest and shows locked banner
            stage_select.enter_quarter = MagicMock()
            clicked = stage_select.handle_summative_modal_click(card2["rect"].center)
            self.assertTrue(clicked)
            self.assertTrue(stage_select.summative_modal_active)  # Modal stays open
            self.assertIn("Complete Assessment 1 first", stage_select.locked_portal_banner_msg)
            stage_select.enter_quarter.assert_not_called()

    @patch("db.save_system.load_student_progress")
    def test_is_quarter_completed_dynamic_multi_summative(self, mock_load_progress):
        from screens.stageselect import StageSelect

        # When only 1st is finished, Term 1 is NOT fully completed
        mock_load_progress.return_value = {
            "completed_summatives": {
                "t1_s1": {"completed": True, "score": 10}
            }
        }
        with patch.object(db, "get_available_summatives_for_term", return_value=[1, 2]):
            stage_select = StageSelect(self.screen, self.main_menu)
            self.assertFalse(stage_select.is_quarter_completed("quarter1"))
            
            # Quarter 2 requires ALL available summatives (both 1 and 2), so with only 1 finished it is locked:
            self.assertFalse(stage_select.is_quarter_unlocked("quarter2"))

            # When both 1st and 2nd are finished, Term 1 IS fully completed and Quarter 2 unlocks
            mock_load_progress.return_value = {
                "completed_summatives": {
                    "t1_s1": {"completed": True, "score": 10},
                    "t1_s2": {"completed": True, "score": 10}
                }
            }
            self.assertTrue(stage_select.is_quarter_completed("quarter1"))
            self.assertTrue(stage_select.is_quarter_unlocked("quarter2"))

            # Test Term 2 multi-summative gating to Term 3
            mock_load_progress.return_value = {
                "completed_summatives": {
                    "t1_s1": {"completed": True, "score": 10},
                    "t1_s2": {"completed": True, "score": 10},
                    "t2_s1": {"completed": True, "score": 10}
                }
            }
            self.assertFalse(stage_select.is_quarter_completed("quarter2"))
            self.assertFalse(stage_select.is_quarter_unlocked("quarter3"))

            mock_load_progress.return_value = {
                "completed_summatives": {
                    "t1_s1": {"completed": True, "score": 10},
                    "t1_s2": {"completed": True, "score": 10},
                    "t2_s1": {"completed": True, "score": 10},
                    "t2_s2": {"completed": True, "score": 10}
                }
            }
            self.assertTrue(stage_select.is_quarter_completed("quarter2"))
            self.assertTrue(stage_select.is_quarter_unlocked("quarter3"))

            # Test Term 3 multi-summative gating to Term 4 (Remedial Stage)
            mock_load_progress.return_value = {
                "completed_summatives": {
                    "t1_s1": {"completed": True, "score": 10},
                    "t1_s2": {"completed": True, "score": 10},
                    "t2_s1": {"completed": True, "score": 10},
                    "t2_s2": {"completed": True, "score": 10},
                    "t3_s1": {"completed": True, "score": 10}
                }
            }
            self.assertFalse(stage_select.is_quarter_completed("quarter3"))
            self.assertFalse(stage_select.is_quarter_unlocked("quarter4"))

            mock_load_progress.return_value = {
                "completed_summatives": {
                    "t1_s1": {"completed": True, "score": 10},
                    "t1_s2": {"completed": True, "score": 10},
                    "t2_s1": {"completed": True, "score": 10},
                    "t2_s2": {"completed": True, "score": 10},
                    "t3_s1": {"completed": True, "score": 10},
                    "t3_s2": {"completed": True, "score": 10}
                }
            }
            self.assertTrue(stage_select.is_quarter_completed("quarter3"))
            self.assertTrue(stage_select.is_quarter_unlocked("quarter4"))

    @patch("db.save_system.load_student_progress")
    def test_remedial_stage_re_entry_with_missed_questions(self, mock_load_progress):
        from screens.stageselect import StageSelect

        # Student completed Quarter 4 previously, BUT has 3 unmastered missed questions
        mock_load_progress.return_value = {
            "completed_quarters": {"quarter4": {"completed": True}},
            "completed_summatives": {"remedial": {"completed": True}},
            "missed_questions": ["q_101", "q_102", "q_103"]
        }
        stage_select = StageSelect(self.screen, self.main_menu)
        # Remedial should NOT be marked finished because missed questions remain!
        self.assertFalse(stage_select.is_quarter_completed("quarter4"))

        # When missed_questions is empty, Remedial is fully completed
        mock_load_progress.return_value = {
            "completed_quarters": {"quarter4": {"completed": True}},
            "completed_summatives": {"remedial": {"completed": True}},
            "missed_questions": []
        }
        self.assertTrue(stage_select.is_quarter_completed("quarter4"))

    def test_main_menu_progress_with_12_summatives(self):
        save_data = {
            "completed_summatives": {
                "t1_s1": {"completed": True, "score": 10},
                "t1_s2": {"completed": True, "score": 8},
                "t2_s1": {"completed": True, "score": 9},
            }
        }
        req_slots = [f"t{t}_s{s}" for t in range(1, 4) for s in range(1, 5)]
        comp_summs = save_data.get("completed_summatives", {})
        completed_count = sum(1 for slot in req_slots if isinstance(comp_summs.get(slot), dict) and comp_summs[slot].get("completed"))
        progress = min(100, int(round((completed_count / 12.0) * 100)))

        # 3 out of 12 = 25%
        self.assertEqual(completed_count, 3)
        self.assertEqual(progress, 25)

    def test_leaderboard_tabs_and_summatives(self):
        from screens.leaderboard import Leaderboard
        with patch.object(Leaderboard, "refresh_data"):
            lb = Leaderboard(self.screen, self.main_menu)
            # Verify tab labels reflect Terms 1-3 and Remedial
            self.assertEqual(lb.tabs[0]["label"], "OVERALL RANKINGS")
            self.assertEqual(lb.tabs[1]["label"], "TERM 1 (Geometry)")
            self.assertEqual(lb.tabs[2]["label"], "TERM 2 (Kalye)")
            self.assertEqual(lb.tabs[3]["label"], "TERM 3 (Monetary)")
            self.assertEqual(lb.tabs[4]["label"], "REMEDIAL STAGE")

    @patch("db.save_system.load_student_progress")
    def test_assessment_modal_best_score_accuracy(self, mock_load_progress):
        from screens.stageselect import StageSelect
        from db.connect_db import db

        # Scenario: Student took Assessment 1 (5 questions) and got 1 correct (20% -> 20 PTS)
        # Previous bug displayed "20/5" because raw_score 20 was formatted directly over total questions 5.
        mock_load_progress.return_value = {
            "completed_summatives": {
                "t1_s1": {
                    "completed": True,
                    "score": 20,
                    "percentage": 20.0,
                    "total_questions": 5
                },
                "t1_s2": {
                    "completed": True,
                    "score": 100,
                    "percentage": 100.0,
                    "total_questions": 5
                }
            }
        }
        with patch.object(db, "get_available_summatives_for_term", return_value=[1, 2]):
            with patch.object(db, "get_questions", return_value=[{"id": i} for i in range(5)]):
                stage_select = StageSelect(self.screen, self.main_menu)
                stage_select.open_summative_modal(1)

                card1 = stage_select.summative_modal_cards[0]
                card2 = stage_select.summative_modal_cards[1]

                # Card 1 (20% on 5 questions -> 1/5 correct, 20 PTS)
                self.assertEqual(card1["score"], 1, "Card 1 score must be 1 (correct questions), NEVER 20")
                self.assertEqual(card1["correct_answers"], 1)
                self.assertEqual(card1["total"], 5)
                self.assertEqual(card1["percentage"], 20.0)
                self.assertEqual(card1["points"], 20)

                # Card 2 (100% on 5 questions -> 5/5 correct, 100 PTS)
                self.assertEqual(card2["score"], 5, "Card 2 score must be 5 (correct questions), NEVER 100")
                self.assertEqual(card2["correct_answers"], 5)
                self.assertEqual(card2["total"], 5)
                self.assertEqual(card2["percentage"], 100.0)
                self.assertEqual(card2["points"], 100)

                # Render modal frame to ensure no drawing/formatting exceptions
                stage_select.draw_summative_modal()


class TestCloudDrivenModalAccuracy(unittest.TestCase):
    def test_empty_term2_assessment2_stays_locked_and_completes_term2(self):
        """If the web app only has Term 2 Assessment 1 questions, Assessment 2 must stay unavailable/locked
        even after Assessment 1 is completed, and Term 2 counts as completed."""
        from unittest.mock import patch
        import pygame
        from screens.main_menu import MainMenu
        from screens.stageselect import StageSelect
        from db.connect_db import db

        pygame.display.init()
        screen = pygame.display.set_mode((1280, 720))
        menu = MainMenu(screen, enable_camera=False)
        menu.student_id = "TEST_T2_ACCURACY"

        progress_t2_a1_done = {
            "completed_summatives": {
                "t1_s1": {"completed": True, "score": 5, "total_questions": 5, "percentage": 100.0},
                "t1_s2": {"completed": True, "score": 10, "total_questions": 10, "percentage": 100.0},
                "t2_s1": {"completed": True, "score": 4, "total_questions": 5, "percentage": 80.0},
            }
        }
        q5 = [{"id": i, "prompt": f"Q{i}", "optionA": "1", "optionB": "2", "optionC": "3", "optionD": "4", "correctAnswer": "A"} for i in range(1, 6)]
        q3 = [{"id": 100 + i, "prompt": f"A2 Q{i}", "optionA": "1", "optionB": "2", "optionC": "3", "optionD": "4", "correctAnswer": "B"} for i in range(1, 4)]

        with patch("db.save_system.load_student_progress", return_value=progress_t2_a1_done), \
             patch.object(db, "get_available_summatives_for_term", side_effect=lambda t, force_refresh=False: [1, 2] if t == 1 else [1]):
            stage_select = StageSelect(screen, menu)

            def fake_get_qs(quarter=1, summative=None, force_refresh=False):
                if quarter == 2 and summative == 1:
                    return q5
                return []

            with patch.object(db, "get_questions", side_effect=fake_get_qs):
                stage_select.open_summative_modal(2)

            cards = stage_select.summative_modal_cards
            self.assertTrue(cards[0]["available_in_cloud"])
            self.assertTrue(cards[0]["unlocked"])
            self.assertEqual(cards[0]["q_count"], 5)

            self.assertFalse(cards[1]["available_in_cloud"])
            self.assertFalse(cards[1]["unlocked"])
            self.assertEqual(cards[1]["q_count"], 0)

            # Clicking unavailable Assessment 2 must refuse entry with banner message
            stage_select.handle_summative_modal_click(cards[1]["btn_rect"].center)
            self.assertTrue(stage_select.summative_modal_active)
            self.assertIn("No questions have been uploaded", stage_select.locked_portal_banner_msg)

            # Term 2 counts as completed since its only uploaded assessment (A1) is done
            self.assertTrue(stage_select.is_quarter_completed("quarter2"))
            stage_select.draw_summative_modal()

        # Now teacher uploads 3 questions for Term 2 Assessment 2 on the web app
        with patch("db.save_system.load_student_progress", return_value=progress_t2_a1_done), \
             patch.object(db, "get_available_summatives_for_term", side_effect=lambda t, force_refresh=False: [1, 2] if t in (1, 2) else [1]):
            def fake_get_qs_updated(quarter=1, summative=None, force_refresh=False):
                if quarter == 2 and summative == 1:
                    return q5
                if quarter == 2 and summative == 2:
                    return q3
                return []

            with patch.object(db, "get_questions", side_effect=fake_get_qs_updated):
                stage_select.open_summative_modal(2)

            cards = stage_select.summative_modal_cards
            self.assertTrue(cards[1]["available_in_cloud"])
            self.assertTrue(cards[1]["unlocked"])
            self.assertEqual(cards[1]["q_count"], 3)
            self.assertFalse(stage_select.is_quarter_completed("quarter2"))


if __name__ == "__main__":
    unittest.main()
