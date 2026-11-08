import os
import sys
import json
import time
import tempfile
import unittest
import urllib.request
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from db.connect_db import (
    Database,
    map_cloud_questions,
    sanitize_cloud_math_text,
    normalize_quarter_number,
    infer_quarter_from_text,
    db as live_db,
)
from db.save_system import mark_quarter_completed, delete_student_progress, load_student_progress


class FakeHTTPResponse:
    def __init__(self, body_obj, status=200, headers=None):
        self.status = status
        self._raw = json.dumps(body_obj).encode("utf-8") if not isinstance(body_obj, bytes) else body_obj
        self.headers = headers or {"Date": "Sun, 08 Nov 2026 15:00:00 GMT"}

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class MockVercelBackend:
    """In-memory stateful simulation of https://gamified-math-grading-system.vercel.app/api."""

    def __init__(self):
        self.next_id = 500
        self.online = True
        self.fail_next_student_post = False
        self.call_log = []

        self.units = [
            {"id": 4, "code": "M2-U3", "title": "Number and Algebra & Geometry", "quarter": "Quarter 1"},
            {"id": 8, "code": "M2-T2-U4", "title": "Foundations of Multiplication", "quarter": "Quarter 2"},
            {"id": 10, "code": "M2-T3-U7", "title": "Foundations of Division", "quarter": "Quarter 3"},
        ]
        self.assessments = [
            {"id": 1, "title": "Unit 1 Quiz - Number Sense", "unitId": 4, "type": "quiz", "totalPoints": 50},
            {"id": 3, "title": "Unit 3 Assessment - Fractions", "unitId": 4, "type": "test", "totalPoints": 100},
            {"id": 5, "title": "Unit 2 Quiz - Geometry", "unitId": 8, "type": "quiz", "totalPoints": 50},
            {"id": 6, "title": "Unit 1 Test - Data", "unitId": 8, "type": "test", "totalPoints": 100},
        ]
        self.questions = [
            {"id": 15, "unitId": 4, "quarter": "Quarter 1", "isActive": True, "prompt": "Sides on a triangle?", "optionA": "3", "optionB": "4", "optionC": "5", "optionD": "6", "correctAnswer": "A"},
            {"id": 30, "unitId": 4, "quarter": "Summative", "isActive": True, "prompt": "Summative check?", "optionA": "10", "optionB": "20", "optionC": "30", "optionD": "40", "correctAnswer": "B"},
        ]
        self.students = [
            {
                "id": 18,
                "userId": 1,
                "studentId": "S-2024-001",
                "fullName": "Juan Dela Cruz",
                "gradeLevel": "Grade 2",
                "section": "A",
                "gender": "Male",
                "avatarColor": "#f97316",
            }
        ]
        self.grades = []
        self.game_results = []

    def _alloc_id(self):
        self.next_id += 1
        return self.next_id

    def urlopen(self, req, timeout=5):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        method = req.get_method() if hasattr(req, "get_method") else "GET"
        body = json.loads(req.data.decode("utf-8")) if getattr(req, "data", None) else None
        path = url.split("/api/")[-1].split("?")[0].strip("/")
        self.call_log.append((method, path, body))

        if not self.online:
            raise urllib.error.URLError("Simulated network disconnect")

        if path == "units":
            if method == "GET":
                return FakeHTTPResponse(list(self.units))
            if method == "POST":
                row = dict(body)
                row["id"] = self._alloc_id()
                self.units.append(row)
                return FakeHTTPResponse(row)

        if path == "assessments":
            if method == "GET":
                return FakeHTTPResponse(list(self.assessments))
            if method == "POST":
                row = dict(body)
                row["id"] = self._alloc_id()
                self.assessments.append(row)
                return FakeHTTPResponse(row)

        if path == "questions" and method == "GET":
            return FakeHTTPResponse(list(self.questions))

        if path == "students":
            if method == "GET":
                return FakeHTTPResponse(list(self.students))
            if method == "DELETE":
                pk = body.get("id")
                self.students = [s for s in self.students if s.get("id") != pk]
                # PostgreSQL ON DELETE CASCADE behavior on Vercel
                self.game_results = [gr for gr in self.game_results if gr.get("studentId") != pk]
                self.grades = [g for g in self.grades if g.get("studentId") != pk]
                return FakeHTTPResponse({"success": True})
            if method == "POST":
                if self.fail_next_student_post:
                    self.fail_next_student_post = False
                    raise urllib.error.URLError("Simulated drop right after DELETE before POST")
                row = dict(body)
                if "id" not in row or row["id"] is None:
                    row["id"] = self._alloc_id()
                self.students = [s for s in self.students if s.get("id") != row["id"]]
                self.students.append(row)
                return FakeHTTPResponse(row)

        if path == "grades":
            if method == "GET":
                return FakeHTTPResponse(list(self.grades))
            if method == "POST":
                row = dict(body)
                row["id"] = self._alloc_id()
                row.setdefault("createdAt", "2026-11-08T15:00:05.000Z")
                self.grades.append(row)
                return FakeHTTPResponse(row)
            if method == "DELETE":
                gid = body.get("id")
                self.grades = [g for g in self.grades if g.get("id") != gid]
                return FakeHTTPResponse({"success": True})

        if path == "game-results":
            if method == "GET":
                return FakeHTTPResponse(list(self.game_results))
            if method == "POST":
                sid = body.get("studentId")
                st_match = next((s for s in self.students if s.get("id") == sid), None)
                if st_match is None:
                    err_bytes = json.dumps({"error": "Failed to save game result: foreign key violation"}).encode("utf-8")
                    raise urllib.error.HTTPError(url, 500, "Internal Server Error", {}, BytesIO(err_bytes))

                ass_id = body.get("assessmentId", 1)
                ass_obj = next((a for a in self.assessments if a.get("id") == ass_id), {})
                unit_obj = next((u for u in self.units if u.get("id") == ass_obj.get("unitId")), {})

                gr_row = dict(body)
                gr_row["id"] = self._alloc_id()
                gr_row["studentName"] = st_match.get("fullName")
                gr_row["createdAt"] = "2026-11-08T15:00:10.000Z"
                self.game_results.append(gr_row)

                # Mirror Vercel side effect: POST /api/game-results also inserts a row into grades!
                g_row = {
                    "id": self._alloc_id(),
                    "studentId": sid,
                    "studentName": st_match.get("fullName"),
                    "studentNumber": st_match.get("studentId"),
                    "assessmentId": ass_id,
                    "score": body.get("score", 0),
                    "pointsEarned": body.get("score", 0),
                    "feedback": body.get("feedback", ""),
                    "assessmentTitle": ass_obj.get("title", "Assessment"),
                    "quarter": unit_obj.get("quarter", "Quarter 1"),
                    "createdAt": "2026-11-08T15:00:10.000Z",
                }
                self.grades.append(g_row)
                return FakeHTTPResponse(gr_row)

        raise AssertionError(f"Unhandled mock endpoint: {method} {path}")


class TestVercelConnectionSolidified(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.backend = MockVercelBackend()
        self.db = Database(api_base_url="https://mock-vercel.test/api", data_dir=self.temp_dir.name)

    def tearDown(self):
        with self.db._sync_lock:
            self.temp_dir.cleanup()

    def test_summative_and_quarter_normalization(self):
        """Summative labels map to stage 4 while 'Unit 2/3' titles never misclassify Quarter 1 assessments."""
        self.assertEqual(normalize_quarter_number("Summative"), 4)
        self.assertEqual(normalize_quarter_number("Summative Assessment"), 4)
        self.assertEqual(normalize_quarter_number("Quarter 4"), 4)
        self.assertEqual(normalize_quarter_number("Quarter 3"), 3)

        # Misleading unit numbers in assessment titles must NOT falsely trigger Q2/Q3
        self.assertIsNone(infer_quarter_from_text("Unit 2 Activity - Operations"))
        self.assertIsNone(infer_quarter_from_text("Unit 3 Assessment - Fractions"))
        self.assertEqual(infer_quarter_from_text("Completed Summative Assessment (Water Temple)."), 4)
        self.assertEqual(infer_quarter_from_text("Cognitive Maze - Quarter 3 Assessment"), 3)

        with patch("urllib.request.urlopen", side_effect=self.backend.urlopen):
            q4_rows = self.db.get_questions(quarter=4)
        self.assertEqual(len(q4_rows), 1)
        self.assertEqual(q4_rows[0]["id"], 30)
        self.assertEqual(q4_rows[0]["quarter"], "Summative")

    def test_latex_and_brace_math_sanitizer(self):
        """Live Vercel LaTeX/brace strings are cleaned into crisp Unicode while preserving currency prose."""
        self.assertEqual(
            sanitize_cloud_math_text("money:{₱}45 - {₱}12 = {₱}33"),
            "money: ₱45 - ₱12 = ₱33",
        )
        self.assertEqual(
            sanitize_cloud_math_text("repeated addition ($3 + 3 + 3 + 3$) or multiplication ($4 \\times 3$)"),
            "repeated addition (3 + 3 + 3 + 3) or multiplication (4 × 3)",
        )
        self.assertEqual(
            sanitize_cloud_math_text("one-half ($\\frac{1}{2}$) of 8 // 2 = 4 { mangoes}"),
            "one-half (1/2) of 8 ÷ 2 = 4 mangoes",
        )
        self.assertEqual(
            sanitize_cloud_math_text("John has $5 and Mary has $10"),
            "John has $5 and Mary has $10",
        )

        mapped = map_cloud_questions([
            {
                "prompt": "What is $\\frac{1}{2}$ + $\\frac{1}{2}$?",
                "optionA": "$\\frac{1}{4}$",
                "optionB": "1",
                "optionC": "2",
                "optionD": "0",
                "correctAnswer": "1",
                "explanation": "Two halves ($\\frac{1}{2}$) make 1 { whole}!",
            }
        ])
        self.assertEqual(mapped[0]["question"], "What is 1/2 + 1/2?")
        self.assertEqual(mapped[0]["choices"][0], "A. 1/4")
        self.assertEqual(mapped[0]["correct"], 1)
        self.assertEqual(mapped[0]["hint"], "Two halves (1/2) make 1 whole!")

    def test_assessment_provisioning_and_offline_persistence(self):
        """Missing 100-pt stage assessments (including Summative unit + assessment) are provisioned once and cached."""
        with patch("urllib.request.urlopen", side_effect=self.backend.urlopen):
            a1 = self.db.get_assessment_id(1)
            a2 = self.db.get_assessment_id(2)
            a3 = self.db.get_assessment_id(3)
            a4 = self.db.get_assessment_id(4)

        self.assertEqual(len({a1, a2, a3, a4}), 4, "All 4 stages must have distinct assessment IDs")

        # Verify Summative unit & assessment exist on backend with Quarter='Summative' and totalPoints=100
        ass4 = next(a for a in self.backend.assessments if a["id"] == a4)
        unit4 = next(u for u in self.backend.units if u["id"] == ass4["unitId"])
        self.assertEqual(ass4["totalPoints"], 100)
        self.assertEqual(unit4["quarter"], "Summative")

        # Verify cold-start offline DB instance reads the persisted assessments_map.json
        cold_db = Database(api_base_url="https://mock-vercel.test/api", data_dir=self.temp_dir.name)
        self.backend.online = False
        with patch("urllib.request.urlopen", side_effect=self.backend.urlopen):
            cold_db._mark_offline()
            self.assertEqual(cold_db.get_assessment_id(3), a3)
            self.assertEqual(cold_db.get_assessment_id(4), a4)

    def test_crash_safe_student_restore_wal_recovery(self):
        """If network drops right after DELETE /students before POST /students, student never vanishes and auto-recovers."""
        with patch("urllib.request.urlopen", side_effect=self.backend.urlopen):
            # Seed initial cache
            self.assertEqual(len(self.db.get_students(force_refresh=True)), 1)

            # Force POST /students to drop network right after DELETE /students succeeds!
            self.backend.fail_next_student_post = True
            # Retry loop has 3 attempts; drop network completely after first failure
            orig_urlopen = self.backend.urlopen

            def drop_on_student_post(req, timeout=5):
                method = req.get_method() if hasattr(req, "get_method") else "GET"
                url = req.full_url if hasattr(req, "full_url") else str(req)
                if method == "POST" and url.endswith("/students"):
                    self.backend.online = False
                    raise urllib.error.URLError("Power/Wi-Fi lost mid-reset!")
                return orig_urlopen(req, timeout=timeout)

            with patch("urllib.request.urlopen", side_effect=drop_on_student_post):
                self.db.delete_student_records(student_id="S-2024-001", student_db_id=18)

            # Student was deleted on backend, WAL must exist on disk!
            self.assertEqual(len(self.backend.students), 0)
            self.assertTrue(os.path.exists(self.db._pending_restore_path()))

            # While still offline, get_students() must STILL include Juan via WAL + cache!
            offline_roster = self.db.get_students(force_refresh=True)
            self.assertEqual(len(offline_roster), 1)
            self.assertEqual(offline_roster[0]["id"], 18)

            # Reconnect online -> automatic recovery restores Juan #18 to backend and clears WAL!
            self.backend.online = True
            self.db._mark_online()
            recovered_roster = self.db.get_students(force_refresh=True)
            self.assertEqual(len(recovered_roster), 1)
            self.assertEqual(len(self.backend.students), 1)
            self.assertEqual(self.backend.students[0]["id"], 18)
            self.assertFalse(os.path.exists(self.db._pending_restore_path()))

    def test_offline_new_game_fifo_sync_and_queue_deduplication(self):
        """Offline New Game purges stale cloud points BEFORE uploading post-reset offline scores (zero accumulation)."""
        with patch("urllib.request.urlopen", side_effect=self.backend.urlopen):
            self.db.get_students(force_refresh=True)
            a1 = self.db.get_assessment_id(1)
            # Old playthrough: 100 pts on Q1 in the cloud
            self.db.save_game_result(18, 100, 5, 5, 100.0, "Completed Quarter 1.", "Grade 2", assessment_id=a1)
            self.assertEqual(sum(r["score"] for r in self.backend.game_results), 100)

            # Go OFFLINE -> Start New Game -> Play Q1 (60 pts), replay Q1 (40 pts), replay Q1 (80 pts)
            self.backend.online = False
            self.db.delete_student_records(student_id="S-2024-001", student_db_id=18)
            self.db.save_game_result(18, 60, 5, 3, 60.0, "Completed Quarter 1.", "Grade 2", assessment_id=a1)
            self.db.save_game_result(18, 40, 5, 2, 40.0, "Completed Quarter 1.", "Grade 2", assessment_id=a1)
            self.db.save_game_result(18, 80, 5, 4, 80.0, "Completed Quarter 1.", "Grade 2", assessment_id=a1)

            # Queue must contain exactly [reset_student, Q1(score=80)]
            with open(self.db._pending_sync_path(), encoding="utf-8") as fp:
                queued = json.load(fp)
            self.assertEqual(len(queued), 2)
            self.assertEqual(queued[0]["_type"], "reset_student")
            self.assertEqual(queued[1]["score"], 80)

            # Reconnect online and flush queue!
            self.backend.online = True
            self.db._mark_online()
            synced = self.db.sync_offline_results()
            self.assertEqual(synced, 2)
            self.assertFalse(os.path.exists(self.db._pending_sync_path()))

            # Backend must have ONLY the post-reset 80-pt record (old 100-pt record wiped first!)
            self.assertEqual(len(self.backend.game_results), 1)
            self.assertEqual(self.backend.game_results[0]["score"], 80)
            self.assertEqual(len(self.backend.grades), 1)
            self.assertEqual(self.backend.grades[0]["score"], 80)

    def test_online_score_improvement_zero_inflation_and_manual_grade_preservation(self):
        """Improving Q2 (60 -> 80) replaces Q2 cleanly without inflating total points and preserves manual teacher grades."""
        with patch("urllib.request.urlopen", side_effect=self.backend.urlopen):
            a1 = self.db.get_assessment_id(1)
            a2 = self.db.get_assessment_id(2)

            # Seed a teacher manual classroom grade for Juan
            self.backend.grades.append({
                "id": 901,
                "studentId": 18,
                "assessmentId": 5,
                "score": 78,
                "pointsEarned": 39,
                "feedback": "Great effort on classroom worksheet.",
                "assessmentTitle": "Unit 2 Quiz - Geometry",
                "quarter": "Quarter 2",
                "createdAt": "2026-11-08T14:00:00.000Z",
            })

            # Play Q1 (100) and Q2 (60)
            self.db.save_game_result(18, 100, 5, 5, 100.0, "Completed Quarter 1.", "Grade 2", assessment_id=a1)
            self.db.save_game_result(18, 60, 5, 3, 60.0, "Completed Quarter 2.", "Grade 2", assessment_id=a2)
            self.assertEqual(sum(r["score"] for r in self.backend.game_results), 160)

            # Replay Q2 with LOWER score (40) -> skipped!
            self.db.save_game_result(18, 40, 5, 2, 40.0, "Completed Quarter 2.", "Grade 2", assessment_id=a2)
            self.assertEqual(len(self.backend.game_results), 2)
            self.assertEqual(sum(r["score"] for r in self.backend.game_results), 160)

            # Replay Q2 with HIGHER score (80) -> replaces 60 with 80 (total 180, NOT 240!)
            self.db.save_game_result(18, 80, 5, 4, 80.0, "Completed Quarter 2.", "Grade 2", assessment_id=a2)
            self.assertEqual(len(self.backend.game_results), 2)
            self.assertEqual(sum(r["score"] for r in self.backend.game_results), 180)

            # Teacher manual classroom grade must still be preserved!
            manual = [g for g in self.backend.grades if "classroom worksheet" in g.get("feedback", "")]
            self.assertEqual(len(manual), 1)
            self.assertEqual(manual[0]["score"], 78)

    def test_foreign_key_self_healing_when_student_recreated_by_teacher(self):
        """If teacher deletes and re-adds student with new PK (18 -> 42), save_game_result resolves new PK automatically."""
        saves_dir = os.path.join(self.temp_dir.name, "saves")
        os.makedirs(saves_dir, exist_ok=True)
        with open(os.path.join(saves_dir, "S-2024-001.json"), "w", encoding="utf-8") as f:
            json.dump({
                "student_id": "S-2024-001",
                "selected_student": {"id": 18, "student_id": "S-2024-001", "first_name": "Juan", "last_name": "Dela Cruz"},
            }, f)

        # Teacher recreated Juan with PK 42 instead of 18
        self.backend.students[0]["id"] = 42

        with patch("urllib.request.urlopen", side_effect=self.backend.urlopen):
            ok = self.db.save_game_result(18, 100, 5, 5, 100.0, "Completed Quarter 1.", "Grade 2", assessment_id=1)
        self.assertTrue(ok)
        self.assertEqual(len(self.backend.game_results), 1)
        self.assertEqual(self.backend.game_results[0]["studentId"], 42)

    def test_portal_preload_worker_and_short_ttl_cache(self):
        """StageSelect._preload_quarter_worker warms DB questions & assessment IDs without AttributeError."""
        from screens.stageselect import StageSelect

        dummy_self = MagicMock()
        dummy_self.portal_loading_done = False

        mock_resp = FakeHTTPResponse(self.backend.questions)
        with patch("db.connect_db.db", self.db), patch("urllib.request.urlopen", return_value=mock_resp) as m_open:
            StageSelect._preload_quarter_worker(dummy_self, "quarter4")
            self.assertTrue(dummy_self.portal_loading_done)
            calls_after_preload = m_open.call_count
            self.assertGreater(calls_after_preload, 0)

            # Immediate main-thread Quarter4 call hits short-TTL memory cache in 0 HTTP calls!
            qs = self.db.get_questions(4)
            self.assertEqual(m_open.call_count, calls_after_preload, "Main-thread init must hit pre-warmed memory cache")
            self.assertEqual(len(qs), 1)

    def test_leaderboard_accurate_quarter_and_summative_aggregation(self):
        """Leaderboard maps Q1, Q2, Q3, and Summative without overwriting Q1 and computes exact question counts."""
        students = self.backend.students
        grades = [
            {"studentId": 18, "score": 80, "pointsEarned": 80, "assessmentTitle": "Unit 1 Quiz - Number Sense", "quarter": "Quarter 1", "feedback": "Completed Quarter 1."},
            {"studentId": 18, "score": 60, "pointsEarned": 60, "assessmentTitle": "Unit 1 Test - Data", "quarter": "Quarter 2", "feedback": "Completed Quarter 2."},
            {"studentId": 18, "score": 100, "pointsEarned": 100, "assessmentTitle": "Unit 3 Assessment - Fractions", "quarter": "Quarter 1", "feedback": "Completed Quarter 3."},
            {"studentId": 18, "score": 100, "pointsEarned": 100, "assessmentTitle": "Unit 1 Test - Data", "quarter": "Summative", "feedback": "Completed Summative Assessment."},
        ]
        results = [
            {"studentId": 18, "score": 80, "correctAnswers": 4, "totalQuestions": 5, "percentage": 80.0, "feedback": "Completed Quarter 1."},
            {"studentId": 18, "score": 60, "correctAnswers": 3, "totalQuestions": 5, "percentage": 60.0, "feedback": "Completed Quarter 2."},
            {"studentId": 18, "score": 100, "correctAnswers": 5, "totalQuestions": 5, "percentage": 100.0, "feedback": "Completed Quarter 3."},
            {"studentId": 18, "score": 100, "correctAnswers": 1, "totalQuestions": 1, "percentage": 100.0, "feedback": "Completed Summative Assessment."},
        ]
        lb = self.db.get_leaderboard_data(students_api=students, api_grades=grades, api_results=results)
        self.assertEqual(len(lb), 1)
        entry = lb[0]
        self.assertEqual(entry["quarters_completed"], 4)
        self.assertEqual(entry["total_score"], 340)
        self.assertEqual(entry["quarters"][1]["score"], 80)
        self.assertEqual(entry["quarters"][2]["score"], 60)
        self.assertEqual(entry["quarters"][3]["score"], 100)
        self.assertEqual(entry["quarters"][4]["score"], 100)
        self.assertEqual(entry["quarters"][4]["correct"], 1)
        self.assertEqual(entry["quarters"][4]["total"], 1)
        self.assertEqual(entry["total_correct"], 13)
        self.assertEqual(entry["total_questions"], 16)

    def test_stage_save_idempotence_guard_prevents_double_thread_spawn(self):
        """Calling save_results_to_database() twice on Victory Card + Hub transition spawns only 1 save thread."""
        from screens.quarter1 import Quarter1
        from screens.quarter4 import Quarter4

        mock_mm = MagicMock()
        mock_mm.screen = screen
        mock_mm.selected_student = {"id": 18, "student_id": "S-2024-001", "first_name": "Juan", "level": "Grade 2"}
        mock_mm.student_db_id = 18
        mock_mm.audio_manager = MagicMock()

        with patch.object(Database, "get_questions", return_value=[]):
            q1 = Quarter1(screen, mock_mm, map_name="map1.txt")
            q4 = Quarter4(screen, mock_mm, map_name="map10.txt")

        with patch.object(q1, "_run_save_results_to_database") as m_run1:
            q1.save_results_to_database()
            q1.save_results_to_database()
            time.sleep(0.05)
            self.assertEqual(m_run1.call_count, 1)

        with patch.object(q4, "_run_save_quarter4_game_result") as m_run4:
            q4.save_quarter4_game_result()
            q4.save_quarter4_game_result()
            time.sleep(0.05)
            self.assertEqual(m_run4.call_count, 1)

    def test_live_vercel_curriculum_and_assessment_alignment(self):
        """Verify live https://gamified-math-grading-system.vercel.app/api curriculum & distinct 100-pt stage assessments."""
        health = live_db.check_cloud_health(timeout=5)
        if not health.get("online"):
            self.skipTest("Live Vercel API unreachable in current environment")

        # All 4 stage assessments resolve to distinct 100-point cloud assessments
        live_db._assessment_cache.clear()
        live_ids = [live_db.get_assessment_id(q) for q in (1, 2, 3, 4)]
        self.assertEqual(len(set(live_ids)), 4, f"Expected 4 distinct cloud assessment IDs, got {live_ids}")

        # Verify Q1..Q4 (Summative) question fetching & math sanitization against live cloud
        for q in (1, 2, 3, 4):
            raw_qs = live_db.get_questions(q, force_refresh=True)
            self.assertIsInstance(raw_qs, list)
            mapped_qs = map_cloud_questions(raw_qs)
            for mq in mapped_qs:
                self.assertNotIn("\\frac", mq["question"])
                self.assertNotIn("\\times", mq["question"])
                self.assertNotIn("\\frac", mq["hint"])
                self.assertNotIn("\\times", mq["hint"])
                self.assertNotIn("{₱}", mq["hint"])


if __name__ == "__main__":
    unittest.main()
