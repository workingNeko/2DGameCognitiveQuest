# tests/test_autosave_feature.py - Comprehensive Unit Tests for Autosave Feature
import os
import sys
import json
import time
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

import pygame
pygame.init()
pygame.font.init()

from core.autosave_manager import AutosaveManager
from db.save_system import (
    atomic_save_json,
    load_student_progress,
    save_student_progress,
    delete_student_progress,
    get_save_path,
    cleanup_orphaned_tmp_saves
)


class MockMainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.student_id = "AUTOSAVE_TEST_001"
        self.student_db_id = 999
        self.selected_student = {
            "id": 999,
            "student_id": "AUTOSAVE_TEST_001",
            "first_name": "Test",
            "last_name": "Student",
            "score": 50,
            "progress": 25,
            "level": "Grade 2",
            "gender": "male"
        }
        self.current_screen = "stage_select"
        self.popup_state = None
        self.stage_select = None
        self.quarter1 = None
        self.quarter2 = None
        self.quarter3 = None
        self.quarter4 = None
        self.last_stage_select_data = None
        self.autosave_manager = AutosaveManager(self, interval_seconds=1.0)


class TestAutosaveFeature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screen = pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.test_sid = "AUTOSAVE_TEST_001"
        self.save_path = get_save_path(self.test_sid)
        self.bak_path = f"{self.save_path}.bak"
        # Clean test files
        if os.path.exists(self.save_path):
            os.remove(self.save_path)
        if os.path.exists(self.bak_path):
            os.remove(self.bak_path)
        self.mm = MockMainMenu(self.screen)

    def tearDown(self):
        if os.path.exists(self.save_path):
            try:
                os.remove(self.save_path)
            except Exception:
                pass
        if os.path.exists(self.bak_path):
            try:
                os.remove(self.bak_path)
            except Exception:
                pass

    def test_01_autosave_creates_atomic_json_and_bak(self):
        """Verifies autosave creates both primary JSON and verified .bak mirror file."""
        ok = self.mm.autosave_manager.trigger_autosave(reason="test_trigger")
        self.assertTrue(ok, "Autosave trigger should succeed with logged in student")

        # Both primary file and backup mirror must exist
        self.assertTrue(os.path.exists(self.save_path), "Primary save file must exist")
        self.assertTrue(os.path.exists(self.bak_path), "Backup .bak mirror file must exist")

        # Verify contents
        with open(self.save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["student_id"], self.test_sid)

        with open(self.bak_path, "r", encoding="utf-8") as bf:
            bak_data = json.load(bf)
        self.assertEqual(bak_data["student_id"], self.test_sid)

    def test_02_power_interruption_recovery_from_corrupted_primary(self):
        """Simulates power outage corrupting primary save (0 bytes / invalid JSON) and tests recovery from .bak."""
        # 1. Create initial valid save with student name and progress
        self.mm.selected_student["first_name"] = "AlicePowerRecovery"
        from db.save_system import mark_quarter_completed
        mark_quarter_completed(self.mm, "quarter1", score=75, percentage=75.0, total_questions=5)

        self.assertTrue(os.path.exists(self.save_path))
        self.assertTrue(os.path.exists(self.bak_path))

        # Invalidate memory cache so load reads disk
        from db.save_system import invalidate_save_cache
        invalidate_save_cache()

        # 2. Simulate catastrophic power interruption: write 0 bytes / empty garbage to primary save
        with open(self.save_path, "w", encoding="utf-8") as f:
            f.write("")  # 0-byte torn write

        # 3. Load should catch corruption, restore from .bak, and rewrite valid primary
        recovered_data = load_student_progress(self.test_sid)
        self.assertIsNotNone(recovered_data, "Save system must recover data from .bak")
        self.assertEqual(recovered_data["selected_student"]["first_name"], "AlicePowerRecovery")
        self.assertEqual(recovered_data["selected_student"]["score"], 75)
        self.assertTrue(recovered_data["completed_quarters"]["quarter1"]["completed"])

        # Primary file should now be restored to valid JSON
        with open(self.save_path, "r", encoding="utf-8") as f:
            restored_json = json.load(f)
        self.assertEqual(restored_json["selected_student"]["first_name"], "AlicePowerRecovery")
        self.assertEqual(restored_json["selected_student"]["score"], 75)

    def test_03_cleanup_orphaned_tmp_saves(self):
        """Tests that leftover .tmp_* files from aborted power cuts are purged."""
        tmp_file = f"{self.save_path}.tmp_9999_12345"
        with open(tmp_file, "w") as f:
            f.write("partial")

        # Backdate mtime to simulate file older than 10 seconds
        old_time = time.time() - 20
        os.utime(tmp_file, (old_time, old_time))

        cleanup_orphaned_tmp_saves()
        self.assertFalse(os.path.exists(tmp_file), "Stale temporary save file must be deleted")

    def test_04_autosave_indicator_smooth_fade_and_draw(self):
        """Verifies autosave indicator badge counts down and renders without errors."""
        am = self.mm.autosave_manager
        am.notify_saved()
        self.assertEqual(am.indicator_timer, am.indicator_duration)

        # Draw while active
        test_surf = pygame.Surface((1280, 720))
        am.draw(test_surf)

        # Update by 1.0 second
        am.update(dt=1.0)
        self.assertAlmostEqual(am.indicator_timer, am.indicator_duration - 1.0, places=2)
        am.draw(test_surf)

        # Update until expired
        am.update(dt=2.0)
        self.assertEqual(am.indicator_timer, 0.0)
        am.draw(test_surf)  # Should gracefully no-op

    def test_05_quarter_in_level_progress_preservation(self):
        """Verifies in-level states (answered stations, puzzle flags, raft state) persist across saves."""
        from db.save_system import gather_quarter_data

        class MockQuarter4:
            def __init__(self):
                self.player_x = 32 * 25
                self.player_y = 32 * 10
                self.player_dir = "left"
                self.current_map_name = "map12.txt"
                self.quiz_state = 0
                self.quiz_station_index = 4
                self.current_question_index = 3
                self.stage_time_remaining = 450.0
                self.completed = False
                self.answered_stations = {1, 2, 3}
                self.addition_puzzle_solved = True
                self.key_puzzle_solved = False
                self.puzzle_solved = True
                self.raft_state = "ready_to_sail"

        q4 = MockQuarter4()
        data = gather_quarter_data(q4, "quarter4")

        self.assertIn(1, data["answered_stations"])
        self.assertIn(2, data["answered_stations"])
        self.assertIn(3, data["answered_stations"])
        self.assertTrue(data["addition_puzzle_solved"])
        self.assertEqual(data["raft_state"], "ready_to_sail")


if __name__ == "__main__":
    unittest.main()
