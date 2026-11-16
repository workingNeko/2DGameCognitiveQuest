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
            
            # But Quarter 2 IS unlocked because at least 1 summative was mastered!
            self.assertTrue(stage_select.is_quarter_unlocked("quarter2"))

            # When both 1st and 2nd are finished, Term 1 IS fully completed
            mock_load_progress.return_value = {
                "completed_summatives": {
                    "t1_s1": {"completed": True, "score": 10},
                    "t1_s2": {"completed": True, "score": 10}
                }
            }
            self.assertTrue(stage_select.is_quarter_completed("quarter1"))

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


if __name__ == "__main__":
    unittest.main()
