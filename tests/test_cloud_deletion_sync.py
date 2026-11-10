import unittest
import os
import sys
import time
import json
from unittest.mock import patch, MagicMock
import db.connect_db

class TestCloudDeletionSync(unittest.TestCase):
    def setUp(self):
        self.test_sid = "TEST-SYNC-001"
        self.test_db_id = 999
        self.save_path = f"db/saves/{self.test_sid}.json"
        if os.path.exists(self.save_path):
            os.remove(self.save_path)
        if os.path.exists(f"{self.save_path}.bak"):
            os.remove(f"{self.save_path}.bak")

    def tearDown(self):
        if os.path.exists(self.save_path):
            os.remove(self.save_path)
        if os.path.exists(f"{self.save_path}.bak"):
            os.remove(f"{self.save_path}.bak")

    def test_sync_prunes_locally_when_stages_deleted_on_cloud(self):
        """When webapp deletes specific stages, local save should prune them and recalculate scores."""
        from db.save_system import atomic_save_json, load_student_progress, sync_student_with_cloud

        # Setup local save with 3 quarters completed (Q1: 100, Q2: 60, Q3: 80, Total: 240)
        initial_save = {
            "student_id": self.test_sid,
            "selected_student": {"id": self.test_db_id, "student_id": self.test_sid, "score": 240, "progress": 75},
            "completed_quarters": {
                "quarter1": {"completed": True, "score": 100, "percentage": 100.0, "total_questions": 5},
                "quarter2": {"completed": True, "score": 60, "percentage": 60.0, "total_questions": 5},
                "quarter3": {"completed": True, "score": 80, "percentage": 80.0, "total_questions": 5},
            },
            "timestamp": time.time()
        }
        atomic_save_json(self.save_path, initial_save)

        # Mock cloud results where webapp deleted Quarter 2 and Quarter 3 (only Quarter 1 remains)
        mock_cloud_results = [
            {"studentId": self.test_db_id, "score": 100, "percentage": 100.0, "totalQuestions": 5, "feedback": "Completed Quarter 1."}
        ]

        from db.connect_db import Database
        mock_db = MagicMock(spec=Database)
        mock_db._is_offline_fast_fail.return_value = False
        mock_db._count_pending_sync.return_value = 0
        mock_db.get_game_results.return_value = mock_cloud_results
        mock_db.get_students.return_value = [{"id": self.test_db_id, "studentId": self.test_sid}]
        mock_db._same_student_id.side_effect = lambda a, b: str(a) == str(b)
        mock_db._resolve_record_quarter.side_effect = lambda r, a: 1
        mock_db._build_assessment_to_quarter_lookup.return_value = {}
        mock_db.normalize_quarter_number.side_effect = lambda q: int(str(q).replace("quarter", ""))

        with patch.object(sys.modules["db.connect_db"], "db", mock_db):
            res = sync_student_with_cloud(self.test_sid, student_db_id=self.test_db_id)

        self.assertTrue(res.get("synced"))
        self.assertEqual(res.get("action"), "updated")
        self.assertEqual(res.get("total_score"), 100)
        self.assertEqual(res.get("progress"), 25)

        # Verify local file was modified on disk
        updated = load_student_progress(self.test_sid)
        self.assertIn("quarter1", updated["completed_quarters"])
        self.assertNotIn("quarter2", updated["completed_quarters"])
        self.assertNotIn("quarter3", updated["completed_quarters"])
        self.assertEqual(updated["selected_student"]["score"], 100)
        self.assertEqual(updated["selected_student"]["progress"], 25)

    def test_sync_wipes_local_save_when_webapp_deletes_all_records(self):
        """When webapp deletes all records for a student, local save file should be purged."""
        from db.save_system import atomic_save_json, check_save_exists, sync_student_with_cloud

        initial_save = {
            "student_id": self.test_sid,
            "selected_student": {"id": self.test_db_id, "student_id": self.test_sid, "score": 200, "progress": 50},
            "completed_quarters": {
                "quarter1": {"completed": True, "score": 100, "percentage": 100.0, "total_questions": 5},
                "quarter2": {"completed": True, "score": 100, "percentage": 100.0, "total_questions": 5},
            },
            "timestamp": time.time()
        }
        atomic_save_json(self.save_path, initial_save)
        self.assertTrue(check_save_exists(self.test_sid))

        # Webapp has empty results list
        from db.connect_db import Database
        mock_db = MagicMock(spec=Database)
        mock_db._is_offline_fast_fail.return_value = False
        mock_db._count_pending_sync.return_value = 0
        mock_db.get_game_results.return_value = []
        mock_db.get_students.return_value = [{"id": self.test_db_id, "studentId": self.test_sid}]
        mock_db._same_student_id.side_effect = lambda a, b: str(a) == str(b)
        mock_db._build_assessment_to_quarter_lookup.return_value = {}
        mock_db.normalize_quarter_number.side_effect = lambda q: int(str(q).replace("quarter", ""))

        dummy_menu = MagicMock()
        dummy_menu.selected_student = {"score": 200, "progress": 50}

        with patch.object(sys.modules["db.connect_db"], "db", mock_db):
            res = sync_student_with_cloud(self.test_sid, student_db_id=self.test_db_id, main_menu=dummy_menu)

        self.assertTrue(res.get("synced"))
        self.assertEqual(res.get("action"), "reset_all")
        self.assertFalse(check_save_exists(self.test_sid))
        self.assertEqual(dummy_menu.selected_student["score"], 0)
        self.assertEqual(dummy_menu.selected_student["progress"], 0)

    def test_offline_mode_preserves_local_save(self):
        """When offline, cloud sync must never delete local saves."""
        from db.save_system import atomic_save_json, check_save_exists, sync_student_with_cloud

        initial_save = {
            "student_id": self.test_sid,
            "selected_student": {"id": self.test_db_id, "student_id": self.test_sid, "score": 100, "progress": 25},
            "completed_quarters": {
                "quarter1": {"completed": True, "score": 100, "percentage": 100.0, "total_questions": 5},
            },
            "timestamp": time.time()
        }
        atomic_save_json(self.save_path, initial_save)

        from db.connect_db import Database
        mock_db = MagicMock(spec=Database)
        mock_db._is_offline_fast_fail.return_value = True

        with patch.object(sys.modules["db.connect_db"], "db", mock_db):
            res = sync_student_with_cloud(self.test_sid, student_db_id=self.test_db_id)

        self.assertFalse(res.get("synced"))
        self.assertTrue(check_save_exists(self.test_sid))

if __name__ == "__main__":
    unittest.main()
