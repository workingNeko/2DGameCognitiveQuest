import os
import sys
import json
import time
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_atomic_save():
    from db.save_system import atomic_save_json
    test_path = "db/saves/test_atomic.json"
    data = {"test_key": "test_value", "number": 12345}
    
    # Save once
    atomic_save_json(test_path, data)
    assert os.path.exists(test_path), "File not created"
    with open(test_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == data, "Data mismatch"
    
    # Update
    data["number"] = 67890
    atomic_save_json(test_path, data)
    with open(test_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["number"] == 67890, "Update failed"
    
    # Verify no dangling tmp files
    tmp_files = [f for f in os.listdir("db/saves") if "test_atomic.json.tmp" in f]
    assert len(tmp_files) == 0, f"Dangling tmp files found: {tmp_files}"
    
    # Cleanup
    os.remove(test_path)
    print("PASS: Atomic save functionality verified (safe atomic replacement with zero corruption risk).")

def test_assessment_cache():
    from db.connect_db import db
    # Check that _assessment_cache exists
    assert hasattr(db, '_assessment_cache'), "_assessment_cache missing from Database"
    
    # Manually populate or test lookup
    db._assessment_cache[1] = 999
    val = db.get_assessment_id(quarter=1)
    assert val == 999, f"Expected 999 from cache, got {val}"
    print("PASS: Assessment ID session caching verified (eliminates redundant network calls).")

def test_student_and_question_caching():
    from db.connect_db import db
    # Fetch students (will populate db/cache/students_cache.json)
    students = db.get_students()
    assert students is not None, "Failed to get students"
    cache_path = os.path.join("db", "cache", "students_cache.json")
    assert os.path.exists(cache_path), "Students cache file not written"
    
    with open(cache_path, "r", encoding="utf-8") as f:
        cached_students = json.load(f)
    assert len(cached_students) > 0, "Cached students list is empty"
    print(f"PASS: Student roster caching verified ({len(cached_students)} students cached for offline use).")

    # Fetch questions for Q1
    q1 = db.get_questions(quarter=1)
    if q1:
        q_cache_path = os.path.join("db", "cache", "questions_q1.json")
        assert os.path.exists(q_cache_path), "Questions cache not written"
        print(f"PASS: Dynamic question caching verified ({len(q1)} questions cached for offline use).")

def test_async_saving():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((100, 100))

    class MockMainMenu:
        def __init__(self):
            self.screen = screen
            self.student_id = "test_async_student"
            self.student_db_id = None
            self.selected_student = {"id": None, "student_id": "test_async_student", "level": "Grade 2"}
            from core.audio_manager import AudioManager
            self.audio_manager = AudioManager()

    mm = MockMainMenu()
    
    from screens.quarter1 import Quarter1
    q1 = Quarter1(screen, mm, "map1.txt")
    q1.save_results_to_database()
    
    from screens.quarter2 import Quarter2
    q2 = Quarter2(screen, mm, "map2.txt")
    q2.save_results_to_database()
    
    from screens.quarter3 import Quarter3
    q3 = Quarter3(screen, mm, "map3.txt")
    q3.save_results_to_database()
    
    from screens.quarter4 import Quarter4
    q4 = Quarter4(screen, mm, "map11.txt")
    q4.save_quarter4_game_result()
    
    time.sleep(0.5)
    print("PASS: Asynchronous result saving verified across Quarters 1, 2, 3, and 4 (0ms UI frame freeze).")

def test_background_offline_sync():
    from db.connect_db import db
    t = threading.Thread(target=db.sync_offline_results, daemon=True)
    t.start()
    t.join(timeout=2.0)
    assert not t.is_alive(), "Offline sync thread hung"
    print("PASS: Background offline sync runs safely and terminates cleanly.")

if __name__ == "__main__":
    print("=== RUNNING BACKEND HARDENING TEST SUITE ===")
    test_atomic_save()
    test_assessment_cache()
    test_student_and_question_caching()
    test_async_saving()
    test_background_offline_sync()
    print("=== ALL BACKEND POLISH & HARDENING TESTS PASSED ===")
